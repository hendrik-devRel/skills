#!/usr/bin/env python3
"""Print a compact JSON inventory of media in a multicam episode folder."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


MEDIA_SUFFIXES = {".mp4", ".mov", ".mxf", ".wav", ".aif", ".aiff", ".mp3", ".m4a"}


def probe(path: Path, ffprobe: str) -> dict:
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration,format_name,start_time:stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,sample_rate,channels:format_tags=timecode,creation_time:stream_tags=timecode,creation_time",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        return {"path": str(path), "error": result.stderr.strip()}
    payload = json.loads(result.stdout)
    payload["path"] = str(path)
    payload["size_bytes"] = path.stat().st_size
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", type=Path)
    parser.add_argument("--ffprobe", default=shutil.which("ffprobe") or "ffprobe")
    args = parser.parse_args()
    episode = args.episode.expanduser().resolve()
    files = sorted(
        path for path in episode.rglob("*") if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES
    )
    print(json.dumps({"episode": str(episode), "media": [probe(path, args.ffprobe) for path in files]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
