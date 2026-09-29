#!/usr/bin/env python3
"""Detect preview audio offset against an authoritative WAV; optionally replace audio.
Requires FFmpeg, ffprobe, and NumPy. Never changes either input. See helper-contracts.md.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile

RATE = 48000


def command(args):
    return subprocess.run(args, check=True, capture_output=True).stdout


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def probe(path, ffprobe):
    return json.loads(command([ffprobe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


def decode(path, ffmpeg, np):
    raw = command([ffmpeg, '-nostdin', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                   '-ac', '1', '-ar', str(RATE), '-f', 'f32le', '-'])
    return np.frombuffer(raw, dtype='<f4').astype(np.float64)


def verify(preview, reference, ffmpeg, ffprobe, windows, max_lag, tolerance, threshold, np):
    ref, candidate = decode(reference, ffmpeg, np), decode(preview, ffmpeg, np)
    if not np.all(np.isfinite(ref)) or not np.all(np.isfinite(candidate)):
        raise ValueError('decoded audio contains nonfinite samples')
    media = probe(preview, ffprobe)
    audios = [s for s in media['streams'] if s.get('codec_type') == 'audio']
    videos = [s for s in media['streams'] if s.get('codec_type') == 'video']
    if len(audios) != 1 or len(videos) > 1:
        raise ValueError('verify expects one audio stream and at most one video stream')
    audio_start = float(audios[0].get('start_time', 0))
    picture_start = float(videos[0].get('start_time', 0)) if videos else 0.0
    # Raw PCM decoding strips stream timestamps; do not let identical samples hide a PTS offset.
    origin_delta = audio_start - picture_start
    origin_check = {'audio_start_seconds': audio_start, 'picture_start_seconds': picture_start,
                    'audio_minus_picture_seconds': origin_delta}
    if abs(origin_delta) > 1 / RATE:
        return {'status': 'TIMELINE_ORIGIN_MISMATCH', 'preview': str(Path(preview).resolve()),
                'reference': str(Path(reference).resolve()), 'sample_rate': RATE,
                'reference_samples_48k': len(ref), 'preview_samples_48k': len(candidate),
                'origin_check': origin_check, 'median_lag_samples_48k': None, 'windows': []}
    # AAC decode may include a partial final 1024-sample packet; PCM must match closely.
    sample_allowance = 1024 if audios[0].get('codec_name') == 'aac' else 2
    duration = len(ref) / RATE
    video_duration = float(videos[0].get('duration', 0)) if videos else None
    duration_ok = abs(len(ref) - len(candidate)) <= sample_allowance
    if videos:
        duration_ok = duration_ok and video_duration > 0 and abs(video_duration - duration) <= 2 / RATE
    duration_check = {'status': 'PASS' if duration_ok else 'FAIL',
                      'allowed_decoded_sample_difference': sample_allowance,
                      'video_duration_seconds': video_duration}
    if not duration_ok:
        return {'status': 'DURATION_MISMATCH', 'preview': str(Path(preview).resolve()),
                'reference': str(Path(reference).resolve()), 'sample_rate': RATE,
                'reference_samples_48k': len(ref), 'preview_samples_48k': len(candidate),
                'origin_check': origin_check, 'duration_check': duration_check,
                'median_lag_samples_48k': None, 'windows': []}
    if windows is None:
        # Six disjoint bins, omit bin edges to leave room for offset search.
        if duration < 3:
            raise ValueError('automatic six-window QA needs at least 3 seconds')
        bin_seconds = duration / 6
        windows = [[max(max_lag + 1 / RATE, i * bin_seconds + bin_seconds * .15),
                    min(duration - max_lag - 1 / RATE, (i + 1) * bin_seconds - bin_seconds * .15)]
                   for i in range(6)]
    if not isinstance(windows, list) or len(windows) != 6:
        raise ValueError('exactly six [start_seconds,end_seconds] windows are required')
    bound = round(max_lag * RATE)
    if bound < 1:
        raise ValueError('max-lag must cover at least one sample')
    results = []
    previous_end = -1
    for index, interval in enumerate(windows):
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError('each window must contain start and end seconds')
        start, end = [round(float(s) * RATE) for s in interval]
        if not bound <= start < end <= len(ref) or end + bound > len(candidate):
            raise ValueError('window plus max-lag search extends outside available audio')
        if end - start < RATE * .1:
            raise ValueError('each QA window must be at least 100 ms')
        if start < previous_end:
            raise ValueError('six QA windows must be ordered and non-overlapping')
        midpoint = (start + end) / 2 / RATE
        if not index * duration / 6 <= midpoint < (index + 1) * duration / 6:
            raise ValueError('each QA window midpoint must lie in its corresponding sixth of the reference duration')
        previous_end = end
        a = ref[start:end]
        a = a - np.mean(a)
        b = candidate[start - bound:end + bound]
        count = len(a)
        energy_a = float(np.dot(a, a))
        if energy_a / count < 1e-10:
            results.append({'start_seconds': start / RATE, 'end_seconds': end / RATE,
                            'status': 'SILENT_REFERENCE_WINDOW'})
            continue
        nfft = 1 << (len(b) + count - 2).bit_length()
        convolution = np.fft.irfft(np.fft.rfft(b, nfft) * np.fft.rfft(a[::-1], nfft), nfft)
        dots = convolution[count - 1:len(b)]
        sums = np.concatenate(([0.0], np.cumsum(b)))
        squares = np.concatenate(([0.0], np.cumsum(b * b)))
        moving_energy = (squares[count:] - squares[:-count]) - (sums[count:] - sums[:-count]) ** 2 / count
        denominator = np.sqrt(np.maximum(moving_energy, 0) * energy_a)
        correlations = np.divide(dots, denominator, out=np.zeros_like(dots), where=denominator > 0)
        best = int(np.argmax(correlations))
        lag = best - bound
        results.append({'start_seconds': start / RATE, 'end_seconds': end / RATE,
                        'lag_samples_48k': lag, 'lag_ms': lag * 1000 / RATE,
                        'correlation': float(np.clip(correlations[best], -1, 1)),
                        'search_boundary_hit': abs(lag) == bound})
    usable = [w for w in results if w.get('correlation', -1) >= threshold and not w.get('search_boundary_hit')]
    lags = [w['lag_samples_48k'] for w in usable]
    if len(usable) != 6:
        status = 'INCONCLUSIVE'
    elif all(abs(lag) <= tolerance for lag in lags):
        status = 'PASS_ZERO_LAG' if tolerance == 0 else 'PASS_WITHIN_TOLERANCE'
    elif max(lags) - min(lags) <= 2:
        status = 'CONSTANT_NONZERO_LAG'
    else:
        status = 'INCONSISTENT_LAG'
    return {'status': status, 'preview': str(Path(preview).resolve()),
            'reference': str(Path(reference).resolve()), 'sample_rate': RATE,
            'reference_samples_48k': len(ref), 'preview_samples_48k': len(candidate),
            'duration_check': duration_check,
            'origin_check': origin_check,
            'lag_convention': 'Positive means preview audio is delayed relative to reference.',
            'threshold': threshold, 'tolerance_samples': tolerance,
            'median_lag_samples_48k': statistics.median(lags) if lags else None, 'windows': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['verify', 'replace'])
    parser.add_argument('--preview', required=True)
    parser.add_argument('--reference', required=True, help='Authoritative WAV starting at exactly the same picture origin')
    parser.add_argument('--report', required=True, help='New JSON report; never overwritten')
    parser.add_argument('--out', help='New MP4, required for replace; video is stream-copied')
    parser.add_argument('--windows', help='JSON array of six [start_seconds,end_seconds] intervals')
    parser.add_argument('--max-lag', type=float, default=.15)
    parser.add_argument('--tolerance-samples', type=int, default=0)
    parser.add_argument('--min-correlation', type=float, default=.97)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    args = parser.parse_args()
    try:
        import numpy as np
    except ImportError:
        raise ValueError('NumPy is needed for measured FFT QA; select an existing Python with NumPy or install it in an isolated environment.')
    if not 0 < args.max_lag <= 1 or args.tolerance_samples < 0 or not 0 < args.min_correlation <= 1:
        raise ValueError('invalid lag/tolerance/correlation settings')
    for program in (args.ffmpeg, args.ffprobe):
        if not shutil.which(program):
            raise ValueError('program not found: ' + program)
    for path in (args.preview, args.reference):
        if not Path(path).is_file():
            raise ValueError('input is not a file: ' + path)
    if os.path.lexists(args.report):
        raise ValueError('report already exists')
    windows = json.loads(Path(args.windows).read_text()) if args.windows else None
    if args.mode == 'verify':
        if args.out:
            raise ValueError('--out applies only to replace')
        result = verify(args.preview, args.reference, args.ffmpeg, args.ffprobe, windows, args.max_lag,
                        args.tolerance_samples, args.min_correlation, np)
    else:
        if not args.out or Path(args.out).suffix.lower() != '.mp4':
            raise ValueError('replace requires a new --out .mp4')
        output = Path(args.out).resolve()
        if os.path.lexists(args.out):
            raise ValueError('output already exists')
        preview_probe = probe(args.preview, args.ffprobe)
        videos = [s for s in preview_probe['streams'] if s.get('codec_type') == 'video']
        if len(videos) != 1:
            raise ValueError('replace expects exactly one video stream')
        video_duration = float(videos[0].get('duration', 0))
        reference_probe = probe(args.reference, args.ffprobe)
        audios = [s for s in reference_probe['streams'] if s.get('codec_type') == 'audio']
        if len(audios) != 1 or not audios[0].get('codec_name', '').startswith('pcm_'):
            raise ValueError('replacement source must have exactly one uncompressed PCM audio stream')
        reference_duration = float(audios[0].get('duration', reference_probe['format'].get('duration', 0)))
        if video_duration <= 0 or abs(reference_duration - video_duration) > 2 / RATE:
            raise ValueError('picture and authoritative WAV duration must agree within 2 samples; export the matching native range first')
        # A same-directory temporary file avoids clobbering, and os.link publishes without overwrite.
        handle, temp = tempfile.mkstemp(prefix='audio-replacement-', suffix='.mp4', dir=output.parent)
        os.close(handle)
        Path(temp).unlink()
        try:
            command([args.ffmpeg, '-nostdin', '-v', 'error', '-n', '-i', args.preview, '-i', args.reference,
                     '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k',
                     '-ar', str(RATE), '-t', str(video_duration), '-movflags', '+faststart', temp])
            result = verify(temp, args.reference, args.ffmpeg, args.ffprobe, windows, args.max_lag,
                            args.tolerance_samples, args.min_correlation, np)
            result['original_preview'] = str(Path(args.preview).resolve())
            result['preview'] = str(output)
            if result['status'].startswith('PASS_'):
                # Confirm video stream copy by packet-content hash, not just dimensions/codec labels.
                hashes = []
                for path in (args.preview, temp):
                    hashes.append(command([args.ffmpeg, '-nostdin', '-v', 'error', '-i', path,
                                           '-map', '0:v:0', '-c:v', 'copy', '-f', 'hash', '-hash', 'sha256', '-']).decode().strip())
                if hashes[0] != hashes[1]:
                    raise ValueError('replacement unexpectedly changed compressed video payload')
                result['video_payload_sha256'] = hashes[0].split('=', 1)[1]
                os.link(temp, output)
                result['output_published'] = True
            else:
                result['output_published'] = False
        finally:
            Path(temp).unlink(missing_ok=True)
    write_new(args.report, result)
    print(json.dumps({'status': result['status'], 'report': str(Path(args.report).resolve()),
                      'median_lag_samples_48k': result['median_lag_samples_48k'],
                      'output_published': result.get('output_published')}))
    return 0 if result['status'].startswith('PASS_') else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            print(exc.stderr.decode(errors='replace')[-2000:], file=sys.stderr)
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
