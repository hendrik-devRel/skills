#!/usr/bin/env python3
"""Assemble recorder-frame keeps without changing picture duration. Requires numpy.

Usage: python3 assemble_filler_audio.py manifest.json --source aligned.wav --output edited.wav
See ../references/filler-audio-config.md for the manifest and review contract.
Only explicit 60000/1001 fps manifests and aligned 48 kHz PCM are supported.
No source is modified.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import struct
import tempfile
import wave

import numpy as np

SR = 48000
FPS = Fraction(60000, 1001)
SAMPLES_PER_FRAME = Fraction(SR, 1) / FPS
LSB = 1 / 8388608
BLOCK = 262144


def rounded(value: Fraction) -> int:
    """Nearest integer, ties upward; never banker's/float rounding."""
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def frame_sample(frame: int) -> int:
    return rounded(frame * SAMPLES_PER_FRAME)


def ms_samples(value) -> int:
    return rounded(Fraction(Decimal(str(value))) * SR / 1000)


def safe_ms_samples(value) -> int:
    # An approved margin is an upper bound: never round beyond it.
    exact = Fraction(Decimal(str(value))) * SR / 1000
    return exact.numerator // exact.denominator


def integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


class PCM:
    """Read little-endian RIFF/RF64 integer PCM, including PCM24 extensible WAV."""

    def __init__(self, path):
        self.path = Path(path).resolve()
        file_size = self.path.stat().st_size
        fmt = data = None
        data64 = None
        with self.path.open("rb") as stream:
            header = stream.read(12)
            if len(header) != 12 or header[:4] not in (b"RIFF", b"RF64") or header[8:] != b"WAVE":
                raise ValueError("Source must be a little-endian PCM WAV (RIFF or RF64)")
            while stream.tell() + 8 <= file_size:
                ident, size = struct.unpack("<4sI", stream.read(8))
                offset = stream.tell()
                if ident == b"ds64":
                    chunk = stream.read(min(size, 28))
                    if len(chunk) < 28:
                        raise ValueError("Invalid RF64 ds64 chunk")
                    data64 = struct.unpack_from("<Q", chunk, 8)[0]
                elif ident == b"fmt ":
                    fmt = stream.read(min(size, 64))
                elif ident == b"data":
                    if size == 0xFFFFFFFF:
                        if data64 is None:
                            raise ValueError("RF64 data size missing")
                        size = data64
                    data = (offset, size)
                stream.seek(offset + size + size % 2)
                if fmt is not None and data is not None:
                    break
        if fmt is None or data is None or len(fmt) < 16:
            raise ValueError("WAV fmt/data chunk missing")
        code, self.channels, self.rate, _, align, bits = struct.unpack_from("<HHIIHH", fmt)
        if code == 0xFFFE:
            pcm_guid = bytes.fromhex("0100000000001000800000aa00389b71")
            if len(fmt) < 40 or fmt[24:40] != pcm_guid:
                raise ValueError("Extensible WAV must contain integer PCM")
            valid_bits = struct.unpack_from("<H", fmt, 18)[0]
            if valid_bits not in (0, bits):
                raise ValueError("Packed valid-bit/container-bit mismatch is unsupported")
        elif code != 1:
            raise ValueError("Only integer PCM is supported; convert float/compressed input explicitly")
        self.width = bits // 8
        if bits not in (16, 24, 32) or self.channels not in (1, 2):
            raise ValueError("Expected mono or stereo PCM16/24/32")
        if self.rate != SR or align != self.channels * self.width:
            raise ValueError("Source must already be aligned 48 kHz PCM with a valid block alignment")
        offset, size = data
        if size % align or offset + size > file_size:
            raise ValueError("Truncated or partial-sample PCM source")
        self.frames = size // align
        self.bits = bits
        self._bytes = np.memmap(self.path, dtype=np.uint8, mode="r", offset=offset,
                                shape=(self.frames, self.channels, self.width))

    def read(self, start, length):
        if start < 0 or length < 0 or start + length > self.frames:
            raise ValueError(f"Source samples [{start}, {start + length}) exceed [0, {self.frames})")
        raw = self._bytes[start:start + length]
        if self.width == 3:
            values = raw[..., 0].astype(np.int32)
            values |= raw[..., 1].astype(np.int32) << 8
            values |= raw[..., 2].astype(np.int32) << 16
            values = (values ^ 0x800000) - 0x800000
        else:
            values = np.ascontiguousarray(raw).view(f"<i{self.width}").reshape(length, self.channels)
        return values.astype(np.float64) / (2 ** (self.bits - 1))


def pcm24_bytes(values):
    quantized = np.clip(np.rint(values * 8388608), -8388608, 8388607).astype(np.int32)
    output = np.empty((*quantized.shape, 3), dtype=np.uint8)
    output[..., 0] = quantized & 255
    output[..., 1] = (quantized >> 8) & 255
    output[..., 2] = (quantized >> 16) & 255
    return output.tobytes()


def raised_cosine(length):
    return (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, length)))[:, None]


def plan(manifest, source):
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")
    if "fps" not in manifest:
        raise ValueError("fps is required; this helper supports only explicit '60000/1001'")
    if manifest["fps"] != "60000/1001":
        raise ValueError("fps must be exactly '60000/1001'; other rates are unsupported")
    keeps = manifest.get("keep_recorder_frames")
    if not isinstance(keeps, list) or not keeps:
        raise ValueError("keep_recorder_frames must be a nonempty array of [in, out) integer frames")
    segments = []
    cumulative = 0
    previous = None
    for index, interval in enumerate(keeps):
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError(f"Keep {index} must be [in, out)")
        start, end = (integer(v, f"keep {index}") for v in interval)
        if start < 0 or end <= start or (previous is not None and start <= previous):
            raise ValueError("Keeps must be positive-length, sorted and separated; merge touching intervals first")
        out_start = frame_sample(cumulative)
        cumulative += end - start
        out_end = frame_sample(cumulative)
        source_start = frame_sample(start)
        length = out_end - out_start
        if source_start + length > source.frames:
            raise ValueError(f"Keep {index} exceeds source length after sample quantization")
        segments.append({"recorder_frames": [start, end], "output_samples": [out_start, out_end],
                         "source_samples": [source_start, source_start + length],
                         "nominal_recorder_end_sample": frame_sample(end)})
        previous = end
    supplied = manifest.get("joins", [{} for _ in range(len(keeps) - 1)])
    if not isinstance(supplied, list) or len(supplied) != len(keeps) - 1:
        raise ValueError("joins must contain exactly one entry between each pair of keeps")
    joins = []
    for index, spec in enumerate(supplied):
        if not isinstance(spec, dict):
            raise ValueError(f"Join {index} must be an object")
        mode = spec.get("mode", "crossfade")
        if mode not in ("crossfade", "room_tone"):
            raise ValueError(f"Join {index}: mode must be crossfade or room_tone")
        requested = ms_samples(spec.get("fade_ms", 20))
        if not 480 <= requested <= 1440:
            raise ValueError(f"Join {index}: fade_ms must be 10–30 ms")
        left, right = segments[index:index + 2]
        left_end, right_start = left["source_samples"][1], right["source_samples"][0]
        gap = right_start - left_end
        half = min(requested // 2,
                   (left["output_samples"][1] - left["output_samples"][0]) // 2,
                   (right["output_samples"][1] - right["output_samples"][0]) // 2)
        reason = None
        tone = spec.get("room_tone_recorder_frames", manifest.get("room_tone_recorder_frames"))
        if mode == "crossfade":
            outgoing = safe_ms_samples(spec.get("safe_outgoing_handle_ms", 0))
            incoming = safe_ms_samples(spec.get("safe_incoming_handle_ms", 0))
            if outgoing < 0 or incoming < 0:
                raise ValueError("Safe handle lengths cannot be negative")
            cross_half = min(half, outgoing, incoming, max(0, gap // 2))
            if cross_half >= 240:
                half = cross_half
            elif tone is not None:
                mode = "room_tone"
                reason = "Insufficient explicitly safe removed-interval handles for a 10 ms crossfade"
            else:
                raise ValueError(f"Join {index}: insufficient safe handles; supply room_tone_recorder_frames or revise the cut")
        if half < 240:
            raise ValueError(f"Join {index}: kept span too short for a nonoverlapping 10 ms fade; review the cut")
        boundary = left["output_samples"][1]
        item = {"index": index, "mode": mode, "requested_fade_ms": requested / 48,
                "fade_ms": 2 * half / 48, "half_samples": half,
                "output_samples": [boundary - half, boundary + half],
                "excluded_source_samples": [left_end, right_start], "fallback_reason": reason}
        if mode == "crossfade":
            item["outgoing_source_samples"] = [left_end - half, left_end + half]
            item["incoming_source_samples"] = [right_start - half, right_start + half]
            item["approved_outgoing_handle_samples"] = outgoing
            item["approved_incoming_handle_samples"] = incoming
        else:
            if not isinstance(tone, list) or len(tone) != 2:
                raise ValueError(f"Join {index}: room_tone_recorder_frames must identify approved clean room tone")
            tone_start, tone_end = [frame_sample(integer(v, "room tone frame")) for v in tone]
            if tone_start < 0 or tone_end > source.frames or tone_end - tone_start < 2 * half:
                raise ValueError(f"Join {index}: approved room-tone span is out of bounds or shorter than the fade")
            tone_center = (tone_start + tone_end) // 2
            item["room_tone_source_samples"] = [tone_center - half, tone_center + half]
            item["outgoing_source_samples"] = [left_end - half, left_end]
            item["incoming_source_samples"] = [right_start, right_start + half]
        joins.append(item)
    return segments, joins, cumulative


def make_blend(source, join):
    outgoing = source.read(join["outgoing_source_samples"][0],
                           join["outgoing_source_samples"][1] - join["outgoing_source_samples"][0])
    incoming = source.read(join["incoming_source_samples"][0],
                           join["incoming_source_samples"][1] - join["incoming_source_samples"][0])
    peak = max(float(np.max(np.abs(outgoing))), float(np.max(np.abs(incoming))))
    if join["mode"] == "crossfade":
        weights = raised_cosine(len(outgoing))
        blend = outgoing * (1 - weights) + incoming * weights
    else:
        half = join["half_samples"]
        tone = source.read(join["room_tone_source_samples"][0], 2 * half)
        peak = max(peak, float(np.max(np.abs(tone))))
        weights = raised_cosine(half)
        blend = np.concatenate((outgoing * (1 - weights) + tone[:half] * weights,
                                tone[half:] * (1 - weights) + incoming * weights))
    return blend, peak


def verify(path, source, copies, blends, expected_samples, used_peak):
    actual = PCM(path)
    if actual.frames != expected_samples or actual.bits != 24 or actual.channels != source.channels:
        raise AssertionError("Output format/sample count mismatch")
    error = 0.0
    blend_error = 0.0
    stats = np.zeros((5, source.channels), dtype=np.float64)
    count = 0
    for copy in copies:
        length = copy["length_samples"]
        for offset in range(0, length, BLOCK):
            size = min(BLOCK, length - offset)
            expected = source.read(copy["source_start_sample"] + offset, size)
            observed = actual.read(copy["output_start_sample"] + offset, size)
            error = max(error, float(np.max(np.abs(expected - observed))))
            stats[0] += expected.sum(axis=0)
            stats[1] += observed.sum(axis=0)
            stats[2] += (expected * expected).sum(axis=0)
            stats[3] += (observed * observed).sum(axis=0)
            stats[4] += (expected * observed).sum(axis=0)
            count += size
    for start, expected in blends:
        observed = actual.read(start, len(expected))
        blend_error = max(blend_error, float(np.max(np.abs(expected - observed))))
    peak = 0.0
    for start in range(0, actual.frames, BLOCK):
        peak = max(peak, float(np.max(np.abs(actual.read(start, min(BLOCK, actual.frames - start))))))
    correlation = []
    for channel in range(source.channels):
        sx, sy, xx, yy, xy = stats[:, channel]
        variance = max(0, xx - sx * sx / max(count, 1)) * max(0, yy - sy * sy / max(count, 1))
        correlation.append(float(np.clip((xy - sx * sy / count) / math.sqrt(variance), -1, 1))
                           if variance > 0 and count else None)
    if error > LSB + 1e-12 or blend_error > LSB + 1e-12 or peak > used_peak + LSB + 1e-12:
        raise AssertionError("PCM verification failed: source mapping, blend mismatch, or sample-peak overshoot")
    return {"passed": True, "sample_count": actual.frames, "outside_fades_max_abs_error": error,
            "outside_fades_correlation_by_channel": correlation, "outside_fades_samples": count,
            "blend_max_abs_error": blend_error, "output_sample_peak": peak,
            "used_source_sample_peak": used_peak, "sample_peak_overshoot": max(0, peak - used_peak),
            "quantization_tolerance": LSB,
            "true_peak_note": "Convex blends bound sample peaks. Measure native/export true peak separately; no limiter or loudness processing is applied."}


def assemble(manifest, source_path, output_path, report_path=None):
    source = PCM(source_path)
    output = Path(output_path).resolve()
    report_path = Path(report_path).resolve() if report_path else output.with_suffix(".report.json")
    if output.exists() or report_path.exists() or output == report_path:
        raise ValueError("Output and report must be distinct new files; existing files are never overwritten")
    if not output.parent.is_dir() or not report_path.parent.is_dir():
        raise ValueError("Create the output/report directories first")
    segments, joins, total_frames = plan(manifest, source)
    total_samples = frame_sample(total_frames)
    if total_samples * source.channels * 3 > 0xFFFFFFFF - 64:
        raise ValueError("Output exceeds RIFF WAV capacity; split the edit or use a separate RF64 writer")
    copies, blends = [], []
    used_peak = 0.0
    cursor = 0
    temp = tempfile.NamedTemporaryFile(prefix=f".{output.name}.", suffix=".partial", dir=output.parent, delete=False)
    temporary = Path(temp.name)
    temp.close()
    try:
        with wave.open(str(temporary), "wb") as writer:
            writer.setparams((source.channels, 3, SR, total_samples, "NONE", "not compressed"))
            for index, segment in enumerate(segments):
                before = joins[index - 1]["half_samples"] if index else 0
                after = joins[index]["half_samples"] if index < len(joins) else 0
                start = segment["source_samples"][0] + before
                length = segment["source_samples"][1] - after - start
                if length < 0:
                    raise AssertionError("Join fades overlap")
                if length:
                    copies.append({"source_start_sample": start, "output_start_sample": cursor,
                                   "length_samples": length})
                    for offset in range(0, length, BLOCK):
                        block = source.read(start + offset, min(BLOCK, length - offset))
                        used_peak = max(used_peak, float(np.max(np.abs(block))))
                        writer.writeframesraw(pcm24_bytes(block))
                    cursor += length
                if index < len(joins):
                    blend, peak = make_blend(source, joins[index])
                    used_peak = max(used_peak, peak)
                    if cursor != joins[index]["output_samples"][0]:
                        raise AssertionError("Join moved relative to picture")
                    blends.append((cursor, blend))
                    writer.writeframesraw(pcm24_bytes(blend))
                    cursor += len(blend)
        if cursor != total_samples:
            raise AssertionError("Cumulative output duration differs from kept picture frames")
        qa = verify(temporary, source, copies, blends, total_samples, used_peak)
        report = {"source": str(source.path), "output": str(output), "sample_rate": SR,
                  "channels": source.channels, "source_bits": source.bits, "output_bits": 24,
                  "fps": "60000/1001", "kept_picture_frames": total_frames,
                  "picture_duration_seconds": float(total_frames / FPS),
                  "output_samples": total_samples, "audio_duration_seconds": total_samples / SR,
                  "duration_error_samples": float(total_samples - total_frames * SAMPLES_PER_FRAME),
                  "sample_mapping": "Round cumulative kept-frame boundaries; source in = nearest recorder-frame sample. Copy at 1:1 speed outside explicitly listed fades.",
                  "segments": segments, "joins": joins, "unchanged_ranges": copies, "verification": qa}
        # link() refuses to replace files created concurrently; no destructive overwrite.
        os.link(temporary, output)
        try:
            with report_path.open("x") as stream:
                json.dump(report, stream, indent=2, allow_nan=False)
                stream.write("\n")
        except Exception:
            output.unlink()
            raise
        return report
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text())
        report = assemble(manifest, args.source, args.output, args.report)
    except (ValueError, OSError, AssertionError, KeyError, TypeError) as error:
        parser.exit(2, f"assemble_filler_audio: {error}\n")
    print(json.dumps({"output": report["output"], "samples": report["output_samples"],
                      "seconds": report["audio_duration_seconds"], "verification": report["verification"]}, indent=2))


if __name__ == "__main__":
    main()
