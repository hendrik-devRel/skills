#!/usr/bin/env python3
"""Independent xmeml invariants; does not import the edit generator."""
import argparse
import json
import math
import re
from pathlib import Path
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET


def validate(path, min_shot_seconds=1, expected_markers=None, expected_audio_mode=None, expected_audio=None):
    root = ET.parse(path).getroot()
    files = {f.get("id"): f for f in root.findall(".//file") if f.find("pathurl") is not None}
    reports = []
    for sequence in root.findall(".//sequence"):
        duration = int(sequence.findtext("duration"))
        nominal = int(sequence.findtext("rate/timebase"))
        fps = nominal * 1000 / 1001 if sequence.findtext("rate/ntsc") == "TRUE" else nominal
        video_tracks = sequence.findall("media/video/track")
        audio_tracks = sequence.findall("media/audio/track")
        declaration = re.search(r"\[audio_delivery_mode=(recorder_mix|iso_mix)\]", sequence.findtext("description", ""))
        mode = declaration.group(1) if declaration else "recorder_mix"
        if expected_audio_mode is not None:
            assert mode == expected_audio_mode, "audio mode differs from expected configuration"
        assert len(video_tracks) == 1 and len(audio_tracks) == 3, "expected 1 picture / 3 audio tracks"
        audio_shapes, camera_frames, video_clips = [], {}, []
        for track_index, track in enumerate(video_tracks + audio_tracks):
            cursor, shape = 0, []
            for clip in track.findall("clipitem"):
                a, b, si, so = [int(clip.findtext(k)) for k in ("start", "end", "in", "out")]
                assert a == cursor and b > a, f"gap/overlap/empty range in {clip.get('id')}"
                assert so - si == b - a, "source/timeline length mismatch"
                file = files[clip.find("file").get("id")]
                source_duration = int(file.findtext("duration"))
                assert file.findtext("rate/timebase") == str(nominal) and file.findtext("rate/ntsc") == sequence.findtext("rate/ntsc"), "source/sequence cadence mismatch"
                assert 0 <= si < so <= source_duration, "source range outside duration"
                assert int(clip.findtext("duration")) == source_duration, "clip/file source duration disagreement"
                source_path = Path(unquote(urlparse(file.findtext("pathurl")).path))
                assert source_path.is_file(), f"missing source: {source_path}"
                if track_index == 0:
                    assert b - a >= math.ceil(min_shot_seconds * fps - .5), "short visual flash"
                    role = clip.findtext("name").split(" — ", 1)[0].lower()
                    camera_frames[role] = camera_frames.get(role, 0) + b - a
                    width = int(file.findtext("media/video/samplecharacteristics/width"))
                    height = int(file.findtext("media/video/samplecharacteristics/height"))
                    sw = int(sequence.findtext("media/video/format/samplecharacteristics/width"))
                    sh = int(sequence.findtext("media/video/format/samplecharacteristics/height"))
                    if (width, height) != (sw, sh):
                        scale = clip.findtext("filter/effect/parameter[value]/value")
                        assert scale is not None and abs(float(scale) - 100 * sw / width) < .001, "mixed-resolution scale missing"
                        assert abs(float(scale) - 100 * sh / height) < .001, "aspect ratio mismatch"
                    video_clips.append((a, b, role))
                else:
                    role = ("program", "guest_iso", "host_iso")[track_index - 1]
                    enabled = track_index == 1 if mode == "recorder_mix" else track_index != 1
                    assert clip.findtext("enabled") == ("TRUE" if enabled else "FALSE"), "incorrect program/safety audio state"
                    channels = int(file.findtext("media/audio/channelcount"))
                    assert channels == (2 if track_index == 1 else 1), "program stereo / ISO mono mismatch"
                    assert clip.get("premiereChannelType", "stereo" if channels == 2 else "mono") == ("stereo" if channels == 2 else "mono"), "incorrect Premiere audio channel type"
                    levels = {p.findtext("parameterid"): float(p.findtext("value")) for p in clip.findall("filter/effect/parameter")}
                    if "level" in levels:
                        assert 0 < levels["level"] <= 3.98109, "invalid audio gain"
                    if "pan" in levels:
                        assert channels == 1 and -1 <= levels["pan"] <= 1, "invalid mono pan"
                    if expected_audio is not None:
                        spec = expected_audio[role]
                        assert abs(levels.get("level", 1) - 10 ** (float(spec.get("gain_db", 0)) / 20)) < 1e-8, "gain differs from configured dB"
                        assert abs(levels.get("pan", 0) - float(spec.get("pan", 0))) < 1e-8, "pan differs from configuration"
                    shape.append((a, b))
                cursor = b
            assert cursor == duration, "track does not reach sequence end"
            if track_index:
                audio_shapes.append(shape)
        assert audio_shapes[0] == audio_shapes[1] == audio_shapes[2], "audio ripple boundaries differ"
        markers = sequence.findall("marker")
        if expected_markers is not None:
            assert len(markers) == expected_markers, "removal marker count mismatch"
        join_frames = [a for a, _ in audio_shapes[0][1:]]
        for join in join_frames:
            incoming = next((c for c in video_clips if c[0] == join), None)
            outgoing = next((c for c in video_clips if c[1] == join), None)
            assert incoming and outgoing, "no exact camera boundary at source discontinuity"
            assert incoming[2] != outgoing[2], "same-camera jump at source discontinuity"
            assert incoming[1] - incoming[0] >= round(2.85 * fps), "join cover shorter than 2.85s"
        for marker in markers:
            assert int(marker.findtext("in")) in join_frames, "removal marker not at a ripple join"
        assert sum(camera_frames.values()) == duration, "camera total does not match sequence"
        reports.append({"name": sequence.findtext("name"), "duration_frames": duration,
                        "audio_delivery_mode": mode,
                        "duration_seconds": duration / fps, "video_clips": len(video_clips),
                        "audio_tracks": 3, "markers": len(markers), "camera_frames": camera_frames})
    assert reports, "no sequence found"
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", type=Path, nargs="+")
    parser.add_argument("--min-shot-seconds", "--min-video-seconds", type=float, default=1)
    parser.add_argument("--expected-markers", type=int)
    parser.add_argument("--audio-mode", choices=["recorder_mix", "iso_mix"])
    parser.add_argument("--config", type=Path, help="Check audio mode and gain/pan against this config")
    args = parser.parse_args()
    config = json.loads(args.config.read_text()) if args.config else None
    for path in args.xml:
        print(json.dumps({"path": str(path), "checks": validate(path, args.min_shot_seconds, args.expected_markers,
              args.audio_mode or (config.get("audio_delivery_mode", "recorder_mix") if config else None),
              config["audio"] if config else None)}, indent=2))


if __name__ == "__main__":
    main()
