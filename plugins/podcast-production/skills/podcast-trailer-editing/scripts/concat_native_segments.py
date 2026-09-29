#!/usr/bin/env python3
"""Verify and copy-concatenate native silent renders without retiming frames.

Run only after the native renderer has finished all segments. A JSON plan supplies
fps, dimensions, total_frames, output, and ordered segments with path/start_frame/
frames. The segment files must start at zero; start_frame records their original
composition positions. This helper never calls Adobe and never replaces a file.

The concatenation uses explicit frame-derived durations. It fails on a timestamp
or decoded-picture mismatch rather than adding, dropping, or retiming frames.
Decoded bytes are hashed as bounded chunks, never retained for an entire clip.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

CODEC_KEYS = (
    'codec_name', 'codec_tag_string', 'profile', 'level', 'width', 'height',
    'coded_width', 'coded_height', 'pix_fmt', 'sample_aspect_ratio',
    'field_order', 'color_range', 'color_space', 'color_transfer',
    'color_primaries', 'chroma_location', 'has_b_frames', 'refs',
    'is_avc', 'nal_length_size', 'bits_per_raw_sample', 'extradata_size',
    'extradata_hash', 'r_frame_rate', 'avg_frame_rate', 'time_base',
)


def run(command):
    p = subprocess.run(command, capture_output=True, text=True)
    if p.returncode or p.stderr.strip():
        raise RuntimeError(f'Command failed ({p.returncode}): {p.stderr[-6000:]}')
    return p.stdout


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def fingerprint(path):
    before = path.stat()
    digest = sha256(path)
    after = path.stat()
    a = (before.st_size, before.st_mtime_ns, before.st_ino)
    b = (after.st_size, after.st_mtime_ns, after.st_ino)
    if a != b:
        raise ValueError(f'File changed while being hashed: {path}')
    return {'path': str(path), 'size': a[0], 'mtime_ns': a[1],
            'inode': a[2], 'sha256': digest}


def positive(value, label, *, zero=False):
    if type(value) is not int or value < (0 if zero else 1):
        raise ValueError(f'{label} must be a valid integer frame count or position')
    return value


def resolve(value, folder):
    if not isinstance(value, str) or not value or '\n' in value or '\r' in value:
        raise ValueError('Paths must be nonempty single-line strings')
    p = Path(value).expanduser()
    return (p if p.is_absolute() else folder / p).resolve()


def load_plan(path):
    path = path.resolve(strict=True)
    plan = json.loads(path.read_text())
    fps_parts = plan.get('fps')
    if not isinstance(fps_parts, list) or len(fps_parts) != 2:
        raise ValueError('fps must be an integer numerator/denominator pair')
    fps = Fraction(positive(fps_parts[0], 'fps numerator'),
                   positive(fps_parts[1], 'fps denominator'))
    size = plan.get('dimensions')
    if not isinstance(size, list) or len(size) != 2:
        raise ValueError('dimensions must contain width and height')
    width, height = (positive(value, 'dimension') for value in size)
    if width % 2 or height % 2:
        raise ValueError('Even dimensions are required for yuv420p')
    total = positive(plan.get('total_frames'), 'total_frames')
    output = resolve(plan.get('output'), path.parent)
    if output.suffix.lower() != '.mp4':
        raise ValueError('Output must be MP4')
    segments = plan.get('segments')
    if not isinstance(segments, list) or not segments:
        raise ValueError('At least one ordered segment is required')
    normalized, cursor = [], 0
    for index, item in enumerate(segments):
        if not isinstance(item, dict):
            raise ValueError('Each segment must be an object')
        start = positive(item.get('start_frame'), 'start_frame', zero=True)
        count = positive(item.get('frames'), 'frames')
        if start != cursor:
            raise ValueError(f'Segment {index + 1}: gap, overlap, or incorrect ordering')
        source = resolve(item.get('path'), path.parent)
        if not source.is_file():
            raise FileNotFoundError(f'Native segment is not ready: {source}')
        normalized.append({'path': source, 'start_frame': start, 'frames': count})
        cursor += count
    if cursor != total:
        raise ValueError(f'Segment sum {cursor} does not match total_frames {total}')
    sources = [s['path'] for s in normalized]
    if len(set(sources)) != len(sources) or output in sources:
        raise ValueError('Segment paths must be distinct and different from output')
    report = output.with_name(output.name + '.concat-qa.json')
    for destination in (output, report):
        if os.path.lexists(destination):
            raise FileExistsError(f'Refusing replacement: {destination}')
    return plan, fps, (width, height), total, normalized, output, report


def stream_command(command, consume):
    """Drain bounded stdout while stderr is stored on disk to avoid a pipe deadlock."""
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors)
        try:
            value = consume(process.stdout)
            process.stdout.close()
            code = process.wait()
            errors.seek(0, os.SEEK_END)
            length = errors.tell()
            errors.seek(max(0, length - 6000))
            message = errors.read().decode(errors='replace').strip()
            if code or message:
                raise RuntimeError(f'Command failed ({code}): {message}')
            return value
        except BaseException:
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()
            raise


def inspect_video(path, frames, fps, size, ffprobe):
    meta = json.loads(run([ffprobe, '-v', 'error', '-threads', '2',
                           '-show_streams', '-show_data_hash', 'sha256',
                           '-of', 'json', str(path)]))
    streams = meta.get('streams', [])
    if len(streams) != 1 or streams[0].get('codec_type') != 'video':
        raise ValueError(f'{path}: exactly one video stream and no other streams required')
    video = streams[0]
    if video.get('codec_name') != 'h264' or video.get('pix_fmt') != 'yuv420p':
        raise ValueError(f'{path}: native H.264 yuv420p required')
    if (video.get('width'), video.get('height')) != size:
        raise ValueError(f'{path}: incorrect picture dimensions')
    if any(Fraction(video.get(k, '0/1')) != fps for k in ('r_frame_rate', 'avg_frame_rate')):
        raise ValueError(f'{path}: incorrect rational frame rate')
    if video.get('sample_aspect_ratio', '1:1') != '1:1':
        raise ValueError(f'{path}: square pixels required')
    rotations = [video.get('tags', {}).get('rotate', 0)]
    rotations += [s.get('rotation', 0) for s in video.get('side_data_list', [])]
    if any(float(value) % 360 for value in rotations):
        raise ValueError(f'{path}: rotated media is not supported')
    time_base = Fraction(video['time_base'])
    if int(video.get('start_pts', -1)) != 0:
        raise ValueError(f'{path}: picture origin must be zero')
    if int(video.get('duration_ts', -1)) * time_base != Fraction(frames, 1) / fps:
        raise ValueError(f'{path}: exact stream duration mismatch')
    if int(video.get('nb_frames', -1)) != frames:
        raise ValueError(f'{path}: declared frame count mismatch')
    if not video.get('extradata_hash'):
        raise ValueError(f'{path}: codec extradata hash is unavailable')

    def check_timestamps(stream):
        count = 0
        first_is_key = False
        for raw in stream:
            line = raw.decode().strip()
            if not line:
                continue
            fields = dict(p.split('=', 1) for p in line.split('|') if '=' in p)
            if 'best_effort_timestamp' not in fields:
                # Frame side-data may be serialized on its own blank-adjacent row.
                if 'pts' not in fields and 'key_frame' not in fields:
                    continue
                raise ValueError(f'{path}: missing decoded frame timestamp')
            expected = Fraction(count, 1) / fps
            if (int(fields['best_effort_timestamp']) * time_base != expected
                    or int(fields.get('pts', -1)) * time_base != expected):
                raise ValueError(f'{path}: shifted/nonuniform PTS at decoded frame {count}')
            if count == 0:
                first_is_key = fields.get('key_frame') == '1'
            count += 1
        if count != frames or not first_is_key:
            raise ValueError(f'{path}: decoded count mismatch or missing initial keyframe')
        return {'decoded_frames': count, 'all_frame_pts_exact': True,
                'zero_origin': True, 'first_frame_is_keyframe': True,
                'exact_duration': str(Fraction(frames, 1) / fps)}

    scan = [ffprobe, '-v', 'error', '-threads', '2', '-select_streams', 'v:0',
            '-show_frames', '-show_entries', 'frame=pts,best_effort_timestamp,key_frame',
            '-of', 'compact=p=0:nk=0', str(path)]
    checked = stream_command(scan, check_timestamps)
    return video, checked


def decoded_digest(path, frames, size, ffmpeg, aggregate=None):
    local = hashlib.sha256()
    bytes_per_frame = size[0] * size[1] * 3 // 2

    def consume(stream):
        count = 0
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            local.update(chunk)
            if aggregate is not None:
                aggregate.update(chunk)
            count += len(chunk)
        if count != frames * bytes_per_frame:
            raise ValueError(f'{path}: decoded byte/frame count mismatch: {count}')
        return {'decoded_yuv420p_sha256': local.hexdigest(),
                'decoded_frames': count // bytes_per_frame, 'decoded_bytes': count,
                'strict_full_decode_pass': True}

    command = [ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-err_detect', 'explode',
               '-threads', '2', '-noautorotate', '-i', str(path), '-map', '0:v:0',
               '-an', '-sn', '-dn', '-pix_fmt', 'yuv420p', '-fps_mode', 'passthrough',
               '-threads', '2', '-f', 'rawvideo', '-']
    return stream_command(command, consume)


def decimal_duration(value):
    with localcontext() as ctx:
        ctx.prec = 32
        return format(Decimal(value.numerator) / Decimal(value.denominator), '.18f')


def quote_concat(path):
    # ffconcat uses shell-style single quoting; this is file syntax, never a shell command.
    return "'" + str(path).replace("'", "'\\''") + "'"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path, help='JSON plan with exact ordered composition frame ranges')
    parser.add_argument('--ffmpeg', default=shutil.which('ffmpeg') or 'ffmpeg')
    parser.add_argument('--ffprobe', default=shutil.which('ffprobe') or 'ffprobe')
    args = parser.parse_args()
    try:
        plan_hash = sha256(args.plan)
        plan, fps, size, total, segments, output, report_path = load_plan(args.plan)
        inputs = [s['path'] for s in segments]
        before = {str(p): fingerprint(p) for p in inputs}
        codec, checks = None, []
        source_pixels = hashlib.sha256()
        for segment in segments:
            source, count = segment['path'], segment['frames']
            video, timing = inspect_video(source, count, fps, size, args.ffprobe)
            current = {key: video.get(key) for key in CODEC_KEYS}
            if codec is None:
                codec = current
            elif current != codec:
                differences = {k: [codec[k], current[k]] for k in CODEC_KEYS if codec[k] != current[k]}
                raise ValueError(f'{source}: codec parameters differ: {differences}')
            pixels = decoded_digest(source, count, size, args.ffmpeg, source_pixels)
            checks.append({'path': str(source), 'composition_start_frame': segment['start_frame'],
                           'timing': timing, 'picture': pixels})
            print(f'Validated segment: {source.name} | {count} frames', flush=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.concat-native-', dir=output.parent) as temp:
            temp = Path(temp)
            listing = ['ffconcat version 1.0']
            for segment in segments:
                listing += ['file ' + quote_concat(segment['path']),
                            'duration ' + decimal_duration(Fraction(segment['frames'], 1) / fps)]
            list_text = '\n'.join(listing) + '\n'
            list_path = temp / 'segments.ffconcat'
            list_path.write_text(list_text)
            candidate = temp / 'native.mp4'
            command = [args.ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-threads', '2',
                       '-f', 'concat', '-safe', '0', '-i', str(list_path), '-map', '0:v:0',
                       '-an', '-sn', '-dn', '-map_metadata', '-1', '-map_chapters', '-1',
                       '-c:v', 'copy', '-video_track_timescale', str(fps.numerator),
                       '-movie_timescale', str(fps.numerator), '-movflags', '+faststart',
                       '-n', str(candidate)]
            # No -r, fps filter, timestamp offsets, dropped frames, or negative-PTS repair.
            run(command)
            _, output_timing = inspect_video(candidate, total, fps, size, args.ffprobe)
            output_pixels = decoded_digest(candidate, total, size, args.ffmpeg)
            if output_pixels['decoded_yuv420p_sha256'] != source_pixels.hexdigest():
                raise ValueError('Output decoded picture differs from the ordered source frame sequence')
            for source in inputs:
                if fingerprint(source) != before[str(source)]:
                    raise ValueError(f'Original segment changed during processing: {source}')
            if sha256(args.plan) != plan_hash:
                raise ValueError('Concat plan changed during processing')
            report = {
                'status': 'PASS_NATIVE_SEGMENT_CONCAT',
                'created_utc': datetime.now(timezone.utc).isoformat(),
                'plan_path': str(args.plan.resolve()), 'plan_sha256': plan_hash, 'plan': plan,
                'inputs': list(before.values()), 'identical_codec_parameters': codec,
                'segments': checks, 'ffconcat': list_text, 'concat_command': command,
                'output': str(output), 'sha256': sha256(candidate),
                'output_timing': output_timing, 'output_picture': output_pixels,
                'source_sequential_decoded_yuv420p_sha256': source_pixels.hexdigest(),
                'all_decoded_frames_match_ordered_source': True,
                'picture_stream_copied': True, 'audio_streams': 0,
                'originals_unchanged': True,
                'memory_contract': 'At most one 1 MiB raw chunk plus hash state; decoded video is not accumulated.',
                'limitations': ['Native segment frame zero must have been rendered at its documented composition start.',
                                'Pixel identity verifies concatenation, not the original editorial choices or source clock.',
                                'Subjective visual and listening review is not asserted.'],
                'script_sha256': sha256(Path(__file__)),
            }
            staged_report = temp / 'concat-qa.json'
            staged_report.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
            os.link(candidate, output)
            try:
                os.link(staged_report, report_path)
            except BaseException:
                if output.stat().st_ino == candidate.stat().st_ino:
                    output.unlink()
                raise
        print(f'PASS: {output}\nQA: {report_path}', flush=True)
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, ZeroDivisionError) as error:
        print(f'FAILED: {error}\nNo existing file was replaced.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
