#!/usr/bin/env python3
"""Local speech restoration. Dependencies: numpy, scipy, soundfile; FFmpeg for de-clicking.

No resampling, normalization, synthesis, or source modification. This helper accepts
mono WAV/WAVEX PCM_16, PCM_24, and FLOAT audio. Non-audio WAV metadata is not copied.
"""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
import soundfile as sf
from scipy import ndimage, signal

NFFT, HOP = 8192, 2048
CONTEXT = 16 * HOP
SUBTYPES = {"PCM_16", "PCM_24", "FLOAT"}


def number(value):
    result = float(value)
    if not math.isfinite(result):
        raise argparse.ArgumentTypeError("must be a finite number")
    return result


def positive(value):
    result = number(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def nonnegative(value):
    result = number(value)
    if result < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return result


def region(value):
    try:
        start, end = map(number, value.split(":"))
        if start < 0 or end <= start:
            raise ValueError()
        return start, end
    except (ValueError, argparse.ArgumentTypeError):
        raise argparse.ArgumentTypeError("use START:END in seconds, with 0 <= START < END")


def inspect(path):
    info = sf.info(path)
    if info.format not in {"WAV", "WAVEX"} or info.channels != 1:
        raise ValueError("expected a mono WAV or WAVEX source")
    if info.subtype not in SUBTYPES:
        raise ValueError("supported source subtypes: PCM_16, PCM_24, FLOAT")
    if info.samplerate < 32000:
        raise ValueError("this fixed-window helper requires a sample rate of at least 32000 Hz")
    if not info.frames:
        raise ValueError("source contains no samples")
    return info


def finite(x):
    if not np.isfinite(x).all():
        raise ValueError("audio contains NaN or infinite samples")
    return x


def db(rms):
    return float(20 * np.log10(max(float(rms), 1e-15)))


def spectrum(x, sr):
    # Padding explicitly keeps nperseg/noverlap valid even for very short pilots.
    if len(x) < NFFT:
        x = np.pad(x, (0, NFFT - len(x)))
    return signal.stft(x, fs=sr, nperseg=NFFT, noverlap=NFFT-HOP,
                       boundary="zeros", padded=True)[2]


def levels(path, start=0, stop=None):
    info = inspect(path)
    stop = info.frames if stop is None else stop
    windows, total, peak, rail_count = [], 0.0, 0.0, 0
    rail = {"PCM_16": 1-2**-15, "PCM_24": 1-2**-23, "FLOAT": 1.0}[info.subtype]
    with sf.SoundFile(path) as source:
        source.seek(start)
        for frame in range(start, stop, info.samplerate):
            x = finite(source.read(min(info.samplerate, stop-frame), dtype="float32"))
            power = float(np.dot(x.astype(np.float64), x.astype(np.float64)))
            total += power
            peak = max(peak, float(np.max(np.abs(x))))
            rail_count += int(np.count_nonzero(np.abs(x) >= rail))
            windows.append({"start": frame / info.samplerate,
                            "end": (frame+len(x)) / info.samplerate,
                            "rms_dbfs": db(np.sqrt(power/len(x)))})
    return {"frames": stop-start, "sample_rate": info.samplerate,
            "channels": 1, "subtype": info.subtype, "format": info.format,
            "duration_seconds": (stop-start)/info.samplerate,
            "rms_dbfs": db(np.sqrt(total/(stop-start))), "peak": peak,
            "peak_dbfs": db(peak), "samples_at_full_scale": rail_count,
            "nonfinite_samples": 0, "windows": windows}


def distributed(items, maximum=120):
    if len(items) <= maximum:
        return items
    return [items[i] for i in np.linspace(0, len(items)-1, maximum, dtype=int)]


def references(path, info, regions=None, threshold=None, exclude=0):
    if regions:
        chosen = []
        for start, end in sorted(regions):
            if end > info.duration or end-start < max(0.5, 3*NFFT/info.samplerate):
                raise ValueError("each noise region must be in the source and at least max(0.5 seconds, 3 FFT windows) long")
            if chosen and start < chosen[-1][1]:
                raise ValueError("noise regions must not overlap")
            chosen.append((start, end))
        candidates = []
        for start, end in chosen:
            step = max(1.0, 3*NFFT/info.samplerate)
            cursor = start
            while cursor < end:
                tail = min(cursor+step, end)
                if tail-cursor >= max(0.5, 3*NFFT/info.samplerate):
                    candidates.append((cursor, tail))
                cursor = tail
    else:
        full = levels(path)
        candidates = [(q["start"], q["end"]) for q in full["windows"]
                      if q["start"] >= exclude and q["rms_dbfs"] < threshold
                      and q["end"]-q["start"] >= max(0.5, 3*NFFT/info.samplerate)]
    if not candidates:
        raise ValueError("no suitable quiet references; choose verified quiet --noise-region intervals or revise threshold/exclusion")
    selected, powers = distributed(candidates), []
    with sf.SoundFile(path) as source:
        for start, end in selected:
            first, last = round(start*info.samplerate), round(end*info.samplerate)
            source.seek(first)
            x = finite(source.read(last-first, dtype="float32"))
            spec = spectrum(x, info.samplerate)
            # Exclude boundary-padded frames; median across intervals resists breaths.
            frames = np.arange(spec.shape[1])*HOP
            valid = (frames >= NFFT//2) & (frames+NFFT//2 <= len(x))
            powers.append(np.mean(np.abs(spec[:, valid])**2, axis=1))
    profile = np.median(powers, axis=0)
    if not np.isfinite(profile).all() or float(np.max(profile)) <= 1e-25:
        raise ValueError("references are silent or invalid; cannot learn a useful noise profile")
    return profile.astype(np.float32), selected, len(candidates)


def prominent_lines(profile, sr):
    power_db = 10*np.log10(np.maximum(profile, 1e-25))
    baseline = ndimage.median_filter(power_db, size=41, mode="nearest")
    indices, _ = signal.find_peaks(power_db-baseline, height=6, distance=3)
    indices = [i for i in indices if 20 <= i*sr/NFFT <= min(16000, sr/2)]
    indices = sorted(indices, key=lambda i: power_db[i], reverse=True)[:16]
    return [{"frequency_hz": float(i*sr/NFFT),
             "power_db": float(power_db[i]),
             "prominence_over_local_median_db": float(power_db[i]-baseline[i])}
            for i in indices]


def destinations(inputs, outputs):
    paths = [Path(p).expanduser().resolve() for p in outputs]
    sources = [Path(p).expanduser().resolve() for p in inputs]
    if len(set(paths)) != len(paths):
        raise ValueError("output and report paths must differ")
    for path in paths:
        if path in sources:
            raise ValueError("refusing to overwrite a source")
        if path.exists():
            raise ValueError(f"refusing existing output: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    return paths


def publish_json(path, report):
    # Hard-link publication is atomic and, unlike replace(), never clobbers a race.
    fd, name = tempfile.mkstemp(prefix=".audio-report-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
            handle.write("\n")
        os.link(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def analyze(args):
    source = Path(args.source).expanduser().resolve()
    report_path = destinations([source], [args.report])[0] if args.report else None
    info = inspect(source)
    result = {"source": str(source), **levels(source)}
    quiet = [q for q in result["windows"] if q["start"] >= args.exclude_start_seconds
             and q["rms_dbfs"] < args.quiet_threshold_db]
    result["quiet_candidates"] = distributed(quiet)
    result["quiet_threshold_dbfs"] = args.quiet_threshold_db
    result["quiet_candidate_count"] = len(quiet)
    try:
        profile, selected, count = references(source, info, threshold=args.quiet_threshold_db,
                                               exclude=args.exclude_start_seconds)
        result.update(noise_reference_regions=selected, prominent_noise_lines=prominent_lines(profile, info.samplerate))
    except ValueError as exc:
        result["noise_profile_note"] = str(exc)
    result["interpretation"] = "Quiet candidates and spectral peaks require human review; speech, gating, or room sound can contaminate them."
    if report_path:
        publish_json(report_path, result)
        print(str(report_path))
    else:
        print(json.dumps(result, indent=2, allow_nan=False))


def denoise(x, sr, profile, maximum_db, noise_scale):
    spec = spectrum(x, sr)
    estimate = ndimage.gaussian_filter(np.abs(spec)**2, sigma=(0.65, 1.0), mode="nearest")
    floor = 10**(-maximum_db/20)
    gain = np.sqrt(np.maximum(1-profile[:, None]*noise_scale/np.maximum(estimate, 1e-25), floor**2))
    gain = ndimage.gaussian_filter(gain, sigma=(0.7, 1.0), mode="nearest")
    _, out = signal.istft(spec*gain, fs=sr, nperseg=NFFT, noverlap=NFFT-HOP, boundary=True)
    return finite(out[:len(x)].astype(np.float32))


def compare(source_path, cleaned_path, source_start=0):
    original, cleaned = inspect(source_path), inspect(cleaned_path)
    if original.samplerate != cleaned.samplerate or source_start+cleaned.frames > original.frames:
        raise ValueError("source and cleaned audio have incompatible rate or timing")
    before = levels(source_path, source_start, source_start+cleaned.frames)
    after = levels(cleaned_path)
    thirds = np.array_split(np.arange(len(before["windows"])), 3)
    loudest = [max((before["windows"][i] for i in third), key=lambda q: q["rms_dbfs"])
               for third in thirds if len(third)]
    lags = []
    with sf.SoundFile(source_path) as src, sf.SoundFile(cleaned_path) as dst:
        for window in loudest:
            frame = round(window["start"]*original.samplerate)
            length = round((window["end"]-window["start"])*original.samplerate)
            if length < 512:
                continue
            src.seek(frame)
            dst.seek(frame-source_start)
            a, b = src.read(length), dst.read(length)
            a, b = a-a.mean(), b-b.mean()
            norm = float(np.linalg.norm(a)*np.linalg.norm(b))
            if norm <= 1e-20:
                continue
            corr = signal.correlate(b, a, mode="full", method="fft")
            center = len(a)-1
            limited = corr[center-256:center+257]
            index = int(np.argmax(limited))
            lags.append({"source_start_seconds": frame/original.samplerate,
                         "lag_samples": index-256,
                         "normalized_correlation": float(limited[index]/norm)})
    changes = [{"source_start_seconds": a["start"], "source_rms_dbfs": a["rms_dbfs"],
                "cleaned_rms_dbfs": b["rms_dbfs"], "rms_change_db": b["rms_dbfs"]-a["rms_dbfs"]}
               for a, b in zip(before.pop("windows"), after.pop("windows"))]
    return {"source_segment": before, "cleaned": after, "lag_checks": lags,
            "overall_rms_change_db": after["rms_dbfs"]-before["rms_dbfs"],
            "one_second_rms_comparisons": changes,
            "note": "RMS change is signal-level change, not a speech-quality or noise-removal score. Lag uses the highest-energy one-second window in each temporal third; short or silent windows may be unmeasurable."}


def restore(args):
    began = time.monotonic()
    source = Path(args.source).expanduser().resolve()
    output, report_path = destinations([source], [args.output, args.report or str(args.output)+".json"])
    if output.suffix.lower() != ".wav":
        raise ValueError("restored output must end in .wav")
    info = inspect(source)
    if args.max_reduction_db > 30:
        raise ValueError("max reduction must be between 0 and 30 dB")
    if args.noise_scale > 100:
        raise ValueError("noise scale must be <= 100")
    if not 1 <= args.declick_threshold <= 100:
        raise ValueError("declick threshold must be between 1 and 100")
    first = round(args.start_seconds*info.samplerate)
    last = info.frames if args.duration_seconds is None else first+round(args.duration_seconds*info.samplerate)
    if first >= info.frames or last > info.frames or last <= first:
        raise ValueError("requested segment must contain at least one sample and lie within the source")
    profile, selected, count = references(source, info, regions=args.noise_region,
                                           threshold=args.noise_threshold_db,
                                           exclude=args.exclude_start_seconds)
    block = max(HOP, int(args.chunk_seconds*info.samplerate)//HOP*HOP)
    grid_start = first//HOP*HOP
    work_start = max(0, grid_start-CONTEXT)
    work_end = min(info.frames, last+CONTEXT)
    filter_text = None
    prequant_peak = 0.0
    with tempfile.TemporaryDirectory(prefix=".audio-restoration-", dir=output.parent) as temporary:
        temp = Path(temporary)
        process_source, offset = source, 0
        if args.declick:
            ffmpeg = shutil.which(args.ffmpeg)
            if not ffmpeg:
                raise ValueError("FFmpeg was not found; install it or pass --ffmpeg /path/to/ffmpeg")
            pad = round(0.2*info.samplerate)
            length = work_end-work_start
            filter_text = (f"atrim=start_sample={work_start}:end_sample={work_end},asetpts=N/SR/TB,"
                           f"adelay={pad}S:all=1,apad=pad_len={pad},"
                           f"adeclick=window=55:overlap=75:arorder=2:threshold={args.declick_threshold}:burst=1,"
                           f"atrim=start_sample={pad}:end_sample={pad+length},asetpts=N/SR/TB")
            process_source = temp/"declicked.wav"
            print("Repairing clicks with padded FFmpeg adeclick", file=sys.stderr, flush=True)
            subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-n", "-i", str(source),
                            "-af", filter_text, "-c:a", "pcm_f32le", str(process_source)], check=True)
            declick_info = inspect(process_source)
            if declick_info.frames != length or declick_info.samplerate != info.samplerate:
                raise ValueError("de-click pass changed frame count or sample rate")
            offset = work_start
        temporary_output = temp/"restored.wav"
        with sf.SoundFile(process_source) as src, sf.SoundFile(temporary_output, "w", samplerate=info.samplerate,
                channels=1, subtype=info.subtype, format=info.format) as dst:
            for start in range(grid_start, last, block):
                end = min(start+block, last)
                low = max(work_start, start-CONTEXT)
                high = min(work_end, end+CONTEXT)
                src.seek(low-offset)
                x = finite(src.read(high-low, dtype="float32"))
                y = denoise(x, info.samplerate, profile, args.max_reduction_db, args.noise_scale)
                out = y[max(start, first)-low:end-low]
                prequant_peak = max(prequant_peak, float(np.max(np.abs(out))))
                ceiling = {"PCM_16": 1-2**-15, "PCM_24": 1-2**-23, "FLOAT": float("inf")}[info.subtype]
                if np.max(out) > ceiling or (info.subtype != "FLOAT" and np.min(out) < -1):
                    raise ValueError("processing would clip the PCM output; use gentler settings or prepare a separate attenuated working source")
                dst.write(out)
                print(f"Restored {(end-first)/info.samplerate:.1f} / {(last-first)/info.samplerate:.1f} seconds", file=sys.stderr, flush=True)
        done = inspect(temporary_output)
        if done.frames != last-first or done.samplerate != info.samplerate or done.subtype != info.subtype:
            raise ValueError("output format or frame count changed")
        qa = compare(source, temporary_output, first)
        report = {"source": str(source), "output": str(output), "source_start_frame": first,
                  "source_start_seconds": first/info.samplerate, "frames": done.frames,
                  "sample_rate": info.samplerate, "subtype": info.subtype, "format": info.format,
                  "noise_reference_regions_seconds": selected, "eligible_noise_region_count": count,
                  "noise_profile_power": profile.tolist(), "noise_profile_method": "median of mean STFT powers per quiet interval; padded edge frames excluded",
                  "parameters": {"max_reduction_db": args.max_reduction_db, "noise_scale": args.noise_scale,
                                 "nfft": NFFT, "hop": HOP, "context_samples": CONTEXT, "chunk_samples": block,
                                 "declick": args.declick, "declick_threshold": args.declick_threshold,
                                 "declick_filter": filter_text},
                  "prequantization_peak": prequant_peak, "normalization": False, "resampling": False,
                  "fixed_gain_db": 0, "non_audio_metadata_copied": False,
                  "qa": qa, "seconds_elapsed": time.monotonic()-began}
        os.link(temporary_output, output)
        try:
            publish_json(report_path, report)
        except Exception:
            output.unlink()
            raise
    print(json.dumps({"output": str(output), "report": str(report_path), "frames": done.frames,
                      "source_start_seconds": first/info.samplerate, "lag_checks": qa["lag_checks"]}, indent=2))


def preview(args):
    source = Path(args.source).expanduser().resolve()
    cleaned = Path(args.cleaned).expanduser().resolve()
    output, report_path = destinations([source, cleaned], [args.output, str(args.output)+".json"])
    if output.suffix.lower() != ".wav":
        raise ValueError("preview output must end in .wav")
    original, repaired = inspect(source), inspect(cleaned)
    sr = original.samplerate
    offset = round((args.cleaned_start_seconds or 0)*sr)
    if original.samplerate != repaired.samplerate or offset+repaired.frames > original.frames:
        raise ValueError("source and cleaned sample rate or duration are incompatible")
    if args.cleaned_start_seconds is None and original.frames != repaired.frames:
        raise ValueError("frame counts differ; for a pilot, pass its --cleaned-start-seconds explicitly")
    first, length = round(args.start_seconds*sr), round(args.duration_seconds*sr)
    if length < 1 or first < offset or first+length > offset+repaired.frames:
        raise ValueError("preview excerpt must lie within both source and cleaned audio")
    if abs(args.gain_db) > 120:
        raise ValueError("preview gain must be between -120 and 120 dB")
    gain = 10**(args.gain_db/20)
    with sf.SoundFile(source) as src, sf.SoundFile(cleaned) as dst:
        src.seek(first)
        dst.seek(first-offset)
        a, b = finite(src.read(length)), finite(dst.read(length))
    before, after = a*gain, b*gain
    if max(np.max(np.abs(before)), np.max(np.abs(after))) > 1:
        raise ValueError("preview gain would exceed full scale; lower --gain-db")
    fade_samples = min(round(args.fade_ms*sr/1000), length//2)
    if fade_samples:
        fade = np.linspace(0, 1, fade_samples)
        for excerpt in (before, after):
            excerpt[:fade_samples] *= fade
            excerpt[-fade_samples:] *= fade[::-1]
    joined = np.concatenate([before, np.zeros(round(args.gap_seconds*sr)), after])
    with tempfile.TemporaryDirectory(prefix=".audio-preview-", dir=output.parent) as temporary:
        wave = Path(temporary)/"preview.wav"
        sf.write(wave, joined, sr, subtype="FLOAT")
        os.link(wave, output)
        report = {"source": str(source), "cleaned": str(cleaned), "output": str(output),
                  "order": ["original", "silence", "cleaned"], "source_start_seconds": first/sr,
                  "excerpt_seconds": length/sr, "gap_seconds": args.gap_seconds,
                  "shared_gain_db": args.gain_db, "sample_rate": sr,
                  "fade_samples": fade_samples, "fade_ms": fade_samples*1000/sr,
                  "cleaned_source_start_seconds": offset/sr,
                  "note": "Both excerpts use identical gain and edge fades. They are not independently loudness-normalized."}
        try:
            publish_json(report_path, report)
        except Exception:
            output.unlink()
            raise
    print(json.dumps(report, indent=2))


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    analysis = commands.add_parser("analyze", help="scan one-second levels and report quiet candidates / prominent noise lines")
    analysis.add_argument("source")
    analysis.add_argument("--report")
    analysis.add_argument("--quiet-threshold-db", type=number, default=-60)
    analysis.add_argument("--exclude-start-seconds", type=nonnegative, default=0)
    analysis.set_defaults(run=analyze)
    restoration = commands.add_parser("restore", help="restore a full mono WAV or a timed pilot segment")
    restoration.add_argument("source")
    restoration.add_argument("output")
    selection = restoration.add_mutually_exclusive_group(required=True)
    selection.add_argument("--noise-region", type=region, action="append", help="verified quiet START:END seconds; repeat for distributed intervals")
    selection.add_argument("--noise-threshold-db", type=number, help="auto-select one-second intervals below this RMS dBFS")
    restoration.add_argument("--exclude-start-seconds", type=nonnegative, default=0)
    restoration.add_argument("--max-reduction-db", type=nonnegative, default=8)
    restoration.add_argument("--noise-scale", type=positive, default=1)
    restoration.add_argument("--declick", action="store_true")
    restoration.add_argument("--declick-threshold", type=positive, default=2)
    restoration.add_argument("--ffmpeg", default="ffmpeg")
    restoration.add_argument("--start-seconds", type=nonnegative, default=0)
    restoration.add_argument("--duration-seconds", type=positive)
    restoration.add_argument("--chunk-seconds", type=positive, default=60)
    restoration.add_argument("--report")
    restoration.set_defaults(run=restore)
    comparison = commands.add_parser("preview", help="write original, silence, cleaned to a FLOAT WAV at identical gain")
    comparison.add_argument("source")
    comparison.add_argument("cleaned")
    comparison.add_argument("output")
    comparison.add_argument("--start-seconds", type=nonnegative, default=0)
    comparison.add_argument("--duration-seconds", type=positive, default=12)
    comparison.add_argument("--cleaned-start-seconds", type=nonnegative,
                            help="source time of frame zero in a pilot cleaned file")
    comparison.add_argument("--gap-seconds", type=nonnegative, default=0.5)
    comparison.add_argument("--fade-ms", type=nonnegative, default=5,
                            help="equal edge fades per excerpt; 0 disables fades (default: 5 ms)")
    comparison.add_argument("--gain-db", type=number, default=0)
    comparison.set_defaults(run=preview)
    return root


def main():
    args = parser().parse_args()
    try:
        args.run(args)
    except (ValueError, OSError, RuntimeError, OverflowError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
