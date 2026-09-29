#!/usr/bin/env python3
"""Read-only, every-frame alpha-bounds QA for a silent ProRes4444 render. Configure source frame ranges and body-clear zones explicitly."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np

LAYOUT = None
FPS = None
SIZE = None
QA_SIZE = None
QUANTIZATION = None
TOLERANCE = None
EXPECTED_GLOBAL_START = None
EXPECTED_GLOBAL_END = None
EXPECTED_FRAMES = None
SHOTS = None


def validate_config(data):
    def integer(value, label, minimum=0):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{label}: expected integer >= {minimum}")
        return value
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("config schema_version must be 1")
    fps_data = data.get("fps", {})
    if not isinstance(fps_data, dict):
        raise ValueError("fps must contain num and den")
    fps = Fraction(integer(fps_data.get("num"), "fps.num", 1), integer(fps_data.get("den"), "fps.den", 1))
    size = data.get("size", [])
    qa = data.get("decode_size", [])
    if not isinstance(size, list) or not isinstance(qa, list) or len(size) != 2 or len(qa) != 2:
        raise ValueError("size and decode_size must each contain width,height")
    size = tuple(integer(v, "size", 1) for v in size)
    qa = tuple(integer(v, "decode_size", 1) for v in qa)
    if size[0] % qa[0] or size[1] % qa[1] or size[0] // qa[0] != size[1] // qa[1]:
        raise ValueError("decode_size must evenly reduce both dimensions by the same integer")
    scale = size[0] // qa[0]
    if not 1 <= scale <= 4:
        raise ValueError("supported decode reduction is 1x through 4x")
    tolerance = integer(data.get("tolerance_pixels", scale), "tolerance_pixels")
    if tolerance > scale:
        raise ValueError("tolerance_pixels must not exceed the decode reduction factor")
    start = integer(data.get("global_start_frame"), "global_start_frame")
    end = integer(data.get("global_end_frame_exclusive"), "global_end_frame_exclusive", 1)
    if end <= start:
        raise ValueError("global end must be after start")
    zones = data.get("zones", {})
    if not isinstance(zones, dict) or not zones:
        raise ValueError("zones must be a nonempty name-to-bounds map")
    for name, rect in zones.items():
        if not isinstance(name, str) or not name or not isinstance(rect, list) or len(rect) != 4:
            raise ValueError("each zone needs a name and [left,top,right,bottom] bounds")
        for value in rect:
            integer(value, "zone coordinate")
        if not 0 <= rect[0] < rect[2] <= size[0] or not 0 <= rect[1] < rect[3] <= size[1]:
            raise ValueError(f"zone {name} is invalid or off canvas")
    shots = []
    previous_end = start
    shot_config = data.get("shots", [])
    if not isinstance(shot_config, list):
        raise ValueError("shots must be a list of frame intervals")
    for shot in shot_config:
        if not isinstance(shot, dict):
            raise ValueError("each shot must be a frame-interval object")
        first = integer(shot.get("start_frame"), "shot.start_frame")
        last = integer(shot.get("end_frame_exclusive"), "shot.end_frame_exclusive", 1)
        if first < previous_end or last <= first or first < start or last > end or shot.get("zone") not in zones:
            raise ValueError("shots must be ordered, nonoverlapping, within global range and reference an existing zone")
        shots.append({"start_frame": first, "end_frame_exclusive": last, "zone": shot["zone"], "allowed_bbox_pixels": zones[shot["zone"]]})
        previous_end = last
    if not shots:
        raise ValueError("at least one shot is required; uncovered frames must be transparent")
    return {"fps": fps, "size": size, "decode_size": qa, "scale": scale, "tolerance": tolerance, "start": start, "end": end, "shots": shots}


def configure(path):
    global LAYOUT,FPS,SIZE,QA_SIZE,QUANTIZATION,TOLERANCE,EXPECTED_GLOBAL_START,EXPECTED_GLOBAL_END,EXPECTED_FRAMES,SHOTS
    LAYOUT = Path(path).expanduser().resolve(strict=True)
    config = validate_config(json.loads(LAYOUT.read_text()))
    FPS,SIZE,QA_SIZE = config["fps"],config["size"],config["decode_size"]
    QUANTIZATION,TOLERANCE = config["scale"],config["tolerance"]
    EXPECTED_GLOBAL_START,EXPECTED_GLOBAL_END = config["start"],config["end"]
    EXPECTED_FRAMES = EXPECTED_GLOBAL_END - EXPECTED_GLOBAL_START
    SHOTS = config["shots"]


def load_layout():
    return SHOTS


def shot_for_frame(shots, global_frame):
    return next((s for s in shots if s["start_frame"] <= global_frame < s["end_frame_exclusive"]), None)


def occupancy_bbox(mask, scale=4):
    """Return continuous pixel-edge bounds [L,T,R,B], R/B exclusive."""
    rows = np.flatnonzero(np.any(mask, axis=1))
    if rows.size == 0:
        return None
    cols = np.flatnonzero(np.any(mask, axis=0))
    return [int(cols[0]) * scale, int(rows[0]) * scale,
            (int(cols[-1]) + 1) * scale, (int(rows[-1]) + 1) * scale]


def bbox_violations(bbox, allowed, tolerance=4):
    if bbox is None:
        return {}
    if allowed is None:
        return {"outside_scheduled_shots": True}
    spill = {"left": allowed[0] - bbox[0], "top": allowed[1] - bbox[1],
             "right": bbox[2] - allowed[2], "bottom": bbox[3] - allowed[3]}
    return {side: distance for side, distance in spill.items() if distance > tolerance}


def read_frame(pipe, length):
    chunks = bytearray()
    while len(chunks) < length:
        part = pipe.read(length - len(chunks))
        if not part:
            break
        chunks.extend(part)
    return chunks


def alpha_filter(width, height):
    return ("alphaextract,lut=y='if(gt(val,0),maxval,0)',"
            f"scale={width}:{height}:flags=area:in_range=full:out_range=full,format=gray")


def check_metadata(probe, start):
    problems = []
    streams = probe.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if len(videos) != 1:
        problems.append(f"Expected one video stream; found {len(videos)}")
    if audios:
        problems.append(f"Expected no audio streams; found {len(audios)}")
    if start != EXPECTED_GLOBAL_START:
        problems.append(f"Expected global start {EXPECTED_GLOBAL_START}; received {start}")
    if videos:
        v = videos[0]
        if (v.get("width"), v.get("height")) != SIZE:
            problems.append(f"Expected {SIZE[0]}x{SIZE[1]}; found {v.get('width')}x{v.get('height')}")
        for field in ("r_frame_rate", "avg_frame_rate"):
            try:
                correct_rate = Fraction(v.get(field, "0/1")) == FPS
            except (ValueError, ZeroDivisionError):
                correct_rate = False
            if not correct_rate:
                problems.append(f"Expected {field}={FPS}; found {v.get(field)}")
        if v.get("codec_name") != "prores" or not str(v.get("profile", "")).startswith("4444"):
            problems.append(f"Expected ProRes 4444 family; found {v.get('codec_name')} {v.get('profile')}")
    return problems, videos, audios


def run_check(args):
    configure(args.config)
    if args.global_start_frame is None:
        args.global_start_frame = EXPECTED_GLOBAL_START
    input_path = Path(args.input).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if report_path.exists():
        raise ValueError(f"Refusing to overwrite existing report: {report_path}")
    if not report_path.parent.is_dir():
        raise ValueError(f"Report parent directory does not exist: {report_path.parent}")
    if not input_path.is_file():
        raise ValueError(f"Input is not a regular file: {input_path}")
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            raise ValueError(f"Required executable not found: {binary}")

    shots = load_layout()
    report = {
        "input": str(input_path), "input_bytes": input_path.stat().st_size,
        "layout": str(LAYOUT), "layout_sha256": hashlib.sha256(LAYOUT.read_bytes()).hexdigest(),
        "contract": {
            "global_start_frame": args.global_start_frame,
            "expected_global_start_frame": EXPECTED_GLOBAL_START,
            "expected_global_end_frame_exclusive": EXPECTED_GLOBAL_END,
            "expected_frame_count": EXPECTED_FRAMES, "frame_rate": str(FPS),
            "expected_size": list(SIZE), "decode_size": list(QA_SIZE),
            "bbox_format": "[left,top,right,bottom] source pixel edges; right/bottom exclusive",
            "pixel_quantization_pixels": QUANTIZATION, "resampling_tolerance_pixels": TOLERANCE,
            "occupancy": "Any nonzero source alpha is binarized before area downsampling; any nonzero reduced value is occupied",
            "empty_frame_policy": "Individual empty frames pass bounds QA and are counted; an entirely empty video fails",
        },
        "shots": shots, "metadata_problems": [], "decode_errors": [], "frames": [],
    }
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(input_path)], capture_output=True, text=True)
    if probe.returncode:
        report["decode_errors"].append("ffprobe failed: " + probe.stderr.strip())
        probe_data = {}
    else:
        probe_data = json.loads(probe.stdout)
    report["probe"] = probe_data
    problems, videos, audios = check_metadata(probe_data, args.global_start_frame)
    report["metadata_problems"] = problems
    report["audio_stream_count"] = len(audios)
    report["no_audio"] = len(audios) == 0

    if videos:
        # Binarize before reduction: a one-pixel/low-alpha edge survives a 4x4 area bin.
        # Full-range scaling prevents low reduced occupancy from being treated as video-range black.
        vf = alpha_filter(*QA_SIZE)
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-xerror", "-err_detect", "explode", "-i", str(input_path),
                   "-map", "0:v:0", "-an", "-sn", "-dn", "-vf", vf, "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"]
        report["decode_command"] = command
        frame_bytes = QA_SIZE[0] * QA_SIZE[1]
        with tempfile.TemporaryFile() as error_file:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=error_file)
            try:
                local_frame = 0
                while True:
                    raw = read_frame(proc.stdout, frame_bytes)
                    if not raw:
                        break
                    if len(raw) != frame_bytes:
                        report["decode_errors"].append(f"Partial frame {local_frame}: {len(raw)} of {frame_bytes} bytes")
                        break
                    mask = np.frombuffer(raw, dtype=np.uint8).reshape(QA_SIZE[1], QA_SIZE[0]) > 0
                    bbox = occupancy_bbox(mask, QUANTIZATION)
                    global_frame = args.global_start_frame + local_frame
                    shot = shot_for_frame(shots, global_frame)
                    allowed = shot["allowed_bbox_pixels"] if shot else None
                    violations = bbox_violations(bbox, allowed, TOLERANCE)
                    report["frames"].append({
                        "local_frame": local_frame, "global_frame": global_frame,
                        "global_seconds": round(float(Fraction(global_frame, 1) / FPS), 9),
                        "zone": shot["zone"] if shot else None,
                        "alpha_bbox_pixels": bbox, "violations": violations,
                    })
                    local_frame += 1
                return_code = proc.wait()
            except BaseException:
                proc.kill()
                proc.wait()
                raise
            finally:
                proc.stdout.close()
            error_file.seek(0)
            decoder_stderr = error_file.read().decode("utf-8", errors="replace").strip()
            report["decode_return_code"] = return_code
            report["decoder_stderr"] = decoder_stderr
            if return_code != 0:
                report["decode_errors"].append(f"ffmpeg exited with code {return_code}")
            if decoder_stderr:
                report["decode_errors"].append("ffmpeg reported errors; see decoder_stderr")

    count = len(report["frames"])
    nonempty = sum(f["alpha_bbox_pixels"] is not None for f in report["frames"])
    outliers = [f for f in report["frames"] if f["violations"]]
    report.update({
        "decoded_frame_count": count, "frame_count_matches": count == EXPECTED_FRAMES,
        "nonempty_alpha_frames": nonempty, "empty_alpha_frames": count - nonempty,
        "out_of_bounds_frame_count": len(outliers),
        "out_of_bounds_local_frames": [f["local_frame"] for f in outliers],
        "out_of_bounds_global_frames": [f["global_frame"] for f in outliers],
        "decoded_global_range": [args.global_start_frame, args.global_start_frame + count],
    })
    failed = bool(report["metadata_problems"] or report["decode_errors"] or count != EXPECTED_FRAMES or outliers or nonempty == 0)
    report["result"] = "FAIL" if failed else "PASS"
    with report_path.open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(f"{report['result']}: {count}/{EXPECTED_FRAMES} frames; {len(outliers)} outside bounds; "
          f"{len(audios)} audio streams; {len(report['decode_errors'])} decode errors; "
          f"{count - nonempty} empty-alpha frames. Report: {report_path}")
    for problem in report["metadata_problems"] + report["decode_errors"]:
        print(problem, file=sys.stderr)
    return 1 if failed else 0


def self_test():
    # Pure in-memory fixtures: no movie, image, or Adobe project is created.
    empty = np.zeros((4, 5), dtype=bool)
    assert occupancy_bbox(empty) is None
    empty[1, 2] = True
    assert occupancy_bbox(empty) == [8, 4, 12, 8]
    assert bbox_violations([8, 4, 12, 8], [12, 8, 12, 8]) == {}
    assert bbox_violations([7, 4, 12, 8], [12, 8, 12, 8]) == {"left": 5}
    assert bbox_violations([8, 4, 17, 8], [8, 4, 12, 8]) == {"right": 5}
    assert bbox_violations(None, None) == {}
    assert bbox_violations([0, 0, 4, 4], None) == {"outside_scheduled_shots": True}
    config = {"schema_version":1,"fps":{"num":30,"den":1},"size":[8,8],"decode_size":[2,2],"global_start_frame":10,"global_end_frame_exclusive":12,"zones":{"left":[0,0,4,8],"right":[4,0,8,8]},"shots":[{"start_frame":10,"end_frame_exclusive":11,"zone":"left"},{"start_frame":11,"end_frame_exclusive":12,"zone":"right"}]}
    shots = validate_config(config)["shots"]
    assert shot_for_frame(shots,10)["zone"] == "left"
    assert shot_for_frame(shots,11)["zone"] == "right"
    assert shot_for_frame(shots,12) is None
    bad = dict(config, shots=[config["shots"][1],config["shots"][0]])
    try:
        validate_config(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("Unordered schedule accepted")
    # Exercise the real extraction/reduction filter with one faint 12-bit alpha pixel.
    # Frames exist only in pipe buffers; no media file is written.
    planes = np.zeros((4, 8, 8), dtype="<u2")
    planes[3, 1, 2] = 1
    fixture = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "rawvideo",
                              "-pixel_format", "yuva444p12le", "-video_size", "8x8", "-i", "pipe:0",
                              "-vf", alpha_filter(2, 2), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"],
                             input=planes.tobytes(), capture_output=True)
    assert fixture.returncode == 0, fixture.stderr.decode()
    assert len(fixture.stdout) == 4 and fixture.stdout[0] > 0 and fixture.stdout[1:] == bytes(3)
    print("PASS: in-memory bounds, tolerance, empty frames, exact cuts, and faint single-pixel alpha survival through FFmpeg")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="ProRes 4444 alpha-only movie")
    parser.add_argument("--config", help="JSON canvas, frame-range and shot-zone contract")
    parser.add_argument("--global-start-frame", type=int, help="Optional explicit source-frame origin; must match config")
    parser.add_argument("--report", help="New JSON report path; existing files are never overwritten")
    parser.add_argument("--self-test", action="store_true", help="Run small in-memory mask fixtures without creating media")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.input or not args.report or not args.config:
        parser.error("--input, --config and --report are required unless --self-test is used")
    try:
        return run_check(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
