#!/usr/bin/env python3
"""Config-driven, source-linked xmeml; no transcoding, color baking or master retime.

Sync convention: source_seconds = offset_seconds + drift_ratio * master_seconds.
Video drift is corrected by resetting source slip at each cut, not a speed effect.
"""
import argparse
import copy
import csv
import json
import math
from fractions import Fraction
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET


def require(condition, message):
    if not condition:
        raise ValueError(message)


def frame(seconds, fps):
    return round(float(seconds) * fps)


def runs(values):
    result = []
    for i, value in enumerate(values):
        if not result or result[-1][2] != value:
            result.append([i, i + 1, value])
        else:
            result[-1][1] = i + 1
    return result


def smooth(parts, minimum, protected_first=False):
    """Absorb short visual beats within ONE continuous source range only."""
    parts = [p[:] for p in parts]
    i = 0
    while i < len(parts):
        if parts[i][1] - parts[i][0] >= minimum:
            i += 1
            continue
        require(len(parts) > 1, "retained range is too short for a safe visual beat")
        if i > 0:
            parts[i - 1][1] = parts[i][1]
            parts.pop(i)
            i -= 1
        else:
            require(not protected_first, "cannot shorten protected join cover")
            parts[1][0] = parts[0][0]
            parts.pop(0)
        i = max(i, 0)
    merged = []
    for a, b, role in parts:
        if merged and merged[-1][2] == role:
            merged[-1][1] = b
        else:
            merged.append([a, b, role])
    return merged


def load_labels(path, start, end, fps):
    labels = ["unknown"] * (end - start)
    previous_end = None
    with Path(path).open(newline="") as handle:
        for row in csv.DictReader(handle):
            a = frame(row["start_master_seconds"], fps)
            b = frame(row["end_master_seconds"], fps)
            require(b > a, f"empty speaker segment: {row}")
            require(previous_end is None or a >= previous_end, "speaker segments overlap or are unsorted")
            previous_end = b
            state = row["state"].lower()
            require(state in {"guest", "host", "wide", "overlap", "silence", "unknown"}, f"unknown state {state}")
            lo, hi = max(a, start), min(b, end)
            if hi > lo:
                labels[lo - start:hi - start] = [state] * (hi - lo)
    return labels


def camera_schedule(labels, fps, pacing):
    minimum = frame(pacing.get("minimum_hold_seconds", 3.5), fps)
    confirm = frame(pacing.get("speaker_confirm_seconds", .5), fps)
    reset = frame(pacing.get("wide_reset_after_seconds", 45), fps)
    wide_hold = frame(pacing.get("wide_hold_seconds", 6), fps)
    require(minimum >= frame(1, fps) and wide_hold >= minimum and reset > wide_hold, "invalid pacing")
    require(len(labels) >= minimum, "episode is shorter than minimum camera hold")
    values = ["wide"] * len(labels)
    current, shot_start, pending, since, last_wide_end = "wide", 0, None, 0, 0
    for i, state in enumerate(labels):
        desired = state if state in {"guest", "host"} else "wide"
        if desired != pending:
            pending, since = desired, i
        age = i - shot_start
        hold = wide_hold if current == "wide" else minimum
        can_cut = age >= hold and len(labels) - i >= minimum
        periodic = current != "wide" and i - last_wide_end >= reset
        needed = frame(1.2, fps) if state == "silence" else confirm
        if can_cut and (periodic or (desired != current and i - since + 1 >= needed)):
            if current == "wide":
                last_wide_end = i
            current = "wide" if periodic else desired
            shot_start = i
        values[i] = current
    return smooth(runs(values), minimum)


def assembled(parts, ranges, base, fps, cover_seconds=2.85, trailer=False):
    """Map kept master-frame ranges to a contiguous sequence with explicit joins."""
    labels = [None] * (parts[-1][1] if parts else 0)
    for a, b, role in parts:
        labels[a:b] = [role] * (b - a)
    output, cursor, previous_role = [], 0, None
    cover = frame(cover_seconds, fps)
    minimum = frame(1, fps)
    for index, entry in enumerate(ranges):
        a, b = entry["start"], entry["end"]
        require(b > a, "empty retained range")
        if trailer:
            roles = [entry.get("camera", "guest")] * (b - a)
            require(roles[0] in {"guest", "host", "wide"}, "invalid trailer camera")
        else:
            require(base <= a < b <= base + len(labels), "retained range outside full sequence")
            roles = labels[a - base:b - base]
        if index:
            require(len(roles) >= cover, "post-join range cannot hold 2.85-second cover")
            new_role = "wide" if previous_role != "wide" else "guest"
            stop = cover if len(roles) - cover >= minimum else len(roles)
            roles[:stop] = [new_role] * stop
        local = smooth(runs(roles), minimum, protected_first=index > 0)
        if index:
            require(local[0][2] != previous_role, "join has no camera change")
            require(local[0][1] >= cover, "join cover too short")
        for lo, hi, role in local:
            output.append({"start": cursor + lo, "end": cursor + hi, "master_start": a + lo,
                           "master_end": a + hi, "role": role, "range_index": index})
        cursor += b - a
        previous_role = local[-1][2]
    return output


def retained(start, end, removals):
    result, cursor = [], start
    for removal in removals:
        a, b = removal["start"], removal["end"]
        require(cursor < a < b < end, "removals overlap, touch, or trim an episode boundary")
        result.append({"start": cursor, "end": a})
        cursor = b
    result.append({"start": cursor, "end": end})
    return result


def source_range(spec, master_frame, length, fps, video):
    offset, slope = float(spec.get("offset_seconds", 0)), float(spec.get("drift_ratio", 1))
    require(slope > 0 and (video or slope == 1), "audio retime not supported; master/ISOs must share a clock")
    source_in = round(offset * fps + slope * master_frame)
    source_out = source_in + length
    duration = math.floor(float(spec["duration_seconds"]) * fps + 1e-7)
    require(0 <= source_in < source_out <= duration,
            f"source bounds fail for {spec['path']}: {source_in}:{source_out} / {duration}; no clamping allowed")
    error = (abs(slope - 1) * length + .5) / fps if video else .5 / fps
    return source_in, source_out, duration, error


def sub(parent, tag, value=None, **attrs):
    child = ET.SubElement(parent, tag, attrs)
    if value is not None:
        child.text = str(value)
    return child


def rate(parent, fps_fraction):
    r = sub(parent, "rate")
    sub(r, "timebase", round(float(fps_fraction)))
    sub(r, "ntsc", "TRUE" if fps_fraction.denominator == 1001 else "FALSE")


def nd_timecode(frames, nominal):
    seconds, ff = divmod(frames, nominal)
    minutes, ss = divmod(seconds, 60)
    hh, mm = divmod(minutes, 60)
    return f"{hh:02}:{mm:02}:{ss:02}:{ff:02} NDF"


def combine_podcast(roots, name):
    """One project, separate sequences; global source definitions deduplicated by URI."""
    combined = ET.Element("xmeml", version="5")
    project = sub(combined, "project")
    sub(project, "name", name + " — PODCAST")
    children, identities, definitions = sub(project, "children"), {}, {}
    for index, root in enumerate(roots):
        local_files = {f.get("id"): f for f in root.findall(".//file") if f.find("pathurl") is not None}
        sequence = copy.deepcopy(root.find("./project/children/sequence"))
        for element in sequence.iter():
            if element.tag == "file":
                original = local_files[element.get("id")]
                uri = original.findtext("pathurl")
                file_id = identities.setdefault(uri, f"source-{len(identities) + 1}")
                fingerprint = ET.tostring(original).replace(original.get("id").encode(), b"FILE_ID", 1)
                if uri in definitions:
                    require(definitions[uri] == fingerprint, f"conflicting metadata for shared source {uri}")
                    element.clear()
                else:
                    definitions[uri] = fingerprint
                    element.clear()
                    for child in original:
                        element.append(copy.deepcopy(child))
                element.set("id", file_id)
            elif element.get("id"):
                element.set("id", f"sequence-{index + 1}-{element.get('id')}")
        children.append(sequence)
    ET.indent(combined, space="  ")
    return combined


def make_xml(config, name, shots, kept, removals, fps_fraction):
    fps = float(fps_fraction)
    mode = config.get("audio_delivery_mode", "recorder_mix")
    require(mode in {"recorder_mix", "iso_mix"}, "unknown audio_delivery_mode")
    root = ET.Element("xmeml", version="5")
    project = sub(root, "project")
    sub(project, "name", name)
    sequence = sub(sub(project, "children"), "sequence", id="sequence-" + name.split(" — ")[-1].lower())
    sub(sequence, "name", name)
    sub(sequence, "duration", shots[-1]["end"])
    rate(sequence, fps_fraction)
    sub(sequence, "description", "Source-linked edit; no LUT is applied by this XML. Native source dimensions preserved. "
        "Mixed-resolution sources explicitly scaled. Video sync uses per-cut slip, no baked retime. "
        f"[audio_delivery_mode={mode}] Audio gain/pan are editable XML effects, not baked normalization; verify in Premiere.")
    media = sub(sequence, "media")
    video = sub(media, "video")
    sample = sub(sub(video, "format"), "samplecharacteristics")
    rate(sample, fps_fraction)
    for tag, value in (("width", config["width"]), ("height", config["height"]),
                       ("anamorphic", "FALSE"), ("pixelaspectratio", "square"), ("fielddominance", "none")):
        sub(sample, tag, value)
    video_track = sub(video, "track")
    audio = sub(media, "audio")
    sub(audio, "numOutputChannels", 2)
    defined, rows, max_error = set(), [], 0

    def add_clip(track, spec, role, index, start, end, master, is_video, enabled):
        nonlocal max_error
        si, so, duration, error = source_range(spec, master, end - start, fps, is_video)
        if is_video:
            max_error = max(max_error, error)
            require(error <= config.get("max_within_shot_sync_error_seconds", .05),
                    f"within-shot drift {error:.6f}s exceeds limit for {role}; revise cut pacing or sync method")
        item = sub(track, "clipitem", id=f"{role}-{index}")
        if not is_video:
            item.set("premiereChannelType", "stereo" if spec.get("channels", 1) == 2 else "mono")
        sub(item, "name", f"{role.upper()} — {Path(spec['path']).name}" + (" — DISABLED REFERENCE" if not enabled else ""))
        for tag, value in (("enabled", "TRUE" if enabled else "FALSE"), ("duration", duration),
                           ("start", start), ("end", end), ("in", si), ("out", so)):
            sub(item, tag, value)
        rate(item, fps_fraction)
        file_id = "file-" + role
        file = sub(item, "file", id=file_id)
        if file_id not in defined:
            defined.add(file_id)
            sub(file, "name", Path(spec["path"]).name)
            sub(file, "pathurl", "file://localhost" + quote(str(Path(spec["path"]).resolve()), safe="/"))
            sub(file, "duration", duration)
            rate(file, fps_fraction)
            fm = sub(file, "media")
            if is_video:
                fs = sub(sub(fm, "video"), "samplecharacteristics")
                rate(fs, fps_fraction)
                for tag, value in (("width", spec["width"]), ("height", spec["height"]),
                                   ("anamorphic", "FALSE"), ("pixelaspectratio", "square"), ("fielddominance", "none")):
                    sub(fs, tag, value)
            else:
                fa = sub(fm, "audio")
                fs = sub(fa, "samplecharacteristics")
                sub(fs, "depth", spec.get("bit_depth", 24))
                sub(fs, "samplerate", spec.get("sample_rate", 48000))
                sub(fa, "channelcount", spec.get("channels", 1))
        if is_video:
            note = spec.get("color_note", "Color interpretation requires verification; no LUT applied")
            sub(sub(item, "labels"), "label2", note)
            scale = 100 * config["width"] / spec["width"]
            require(abs(scale - 100 * config["height"] / spec["height"]) < .01, "mixed aspect ratios require explicit framing decision")
            if scale != 100:
                effect = sub(sub(item, "filter"), "effect")
                for tag, value in (("name", "Basic Motion"), ("effectid", "basic"), ("effecttype", "motion"),
                                   ("mediatype", "video"), ("effectcategory", "motion")):
                    sub(effect, tag, value)
                p = sub(effect, "parameter", authoringApp="PremierePro")
                for tag, value in (("parameterid", "scale"), ("name", "Scale"), ("valuemin", 0),
                                   ("valuemax", 1000), ("value", scale)):
                    sub(p, tag, value)
            rows.append({"camera": role, "sequence_in_frame": start, "sequence_out_frame": end,
                         "sequence_in_seconds": start / fps, "sequence_out_seconds": end / fps,
                         "master_in_frame": master, "master_out_frame": master + end - start,
                         "master_in_seconds": master / fps, "master_out_seconds": (master + end - start) / fps,
                         "source_in_frame": si, "source_out_frame": so, "source_in_seconds": si / fps,
                         "source_out_seconds": so / fps, "within_shot_sync_error_bound_seconds": error,
                         "sequence_in_timecode": nd_timecode(start, round(fps)), "source_path": spec["path"]})
        else:
            st = sub(item, "sourcetrack")
            sub(st, "mediatype", "audio")
            sub(st, "trackindex", 1)
            controls = []
            if "gain_db" in spec:
                gain = float(spec["gain_db"])
                require(math.isfinite(gain) and -96 <= gain <= 12, "gain_db outside supported -96..12 dB range")
                controls.append(("Audio Levels", "audiolevels", "Level", "level", 0, 3.98109, 10 ** (gain / 20)))
            if "pan" in spec:
                pan = float(spec["pan"])
                require(math.isfinite(pan) and -1 <= pan <= 1, "pan must be -1 (left) to +1 (right)")
                require(spec.get("channels", 1) == 1, "pan support is limited to mono ISO clips")
                controls.append(("Audio Pan", "audiopan", "Pan", "pan", -1, 1, pan))
            for effect_name, effect_id, param_name, param_id, lo, hi, value in controls:
                effect = sub(sub(item, "filter"), "effect")
                for tag, val in (("name", effect_name), ("effectid", effect_id), ("effectcategory", effect_id),
                                 ("effecttype", effect_id), ("mediatype", "audio"), ("pproBypass", "false")):
                    sub(effect, tag, val)
                parameter = sub(effect, "parameter", authoringApp="PremierePro")
                for tag, val in (("name", param_name), ("parameterid", param_id), ("valuemin", lo),
                                 ("valuemax", hi), ("value", f"{value:.12g}")):
                    sub(parameter, tag, val)

    for i, shot in enumerate(shots):
        add_clip(video_track, config["sources"][shot["role"]], shot["role"], i,
                 shot["start"], shot["end"], shot["master_start"], True, True)
    for role in ("program", "guest_iso", "host_iso"):
        track, cursor = sub(audio, "track", currentExplodedTrackIndex="0", premiereTrackType="Stereo", totalExplodedTrackCount="2"), 0
        sub(track, "enabled", "TRUE")
        enabled = role == "program" if mode == "recorder_mix" else role != "program"
        require("enabled" not in config["audio"][role] or config["audio"][role]["enabled"] == enabled,
                f"{role}.enabled conflicts with audio_delivery_mode={mode}")
        for i, span in enumerate(kept):
            length = span["end"] - span["start"]
            add_clip(track, config["audio"][role], role, i, cursor, cursor + length,
                     span["start"], False, enabled)
            cursor += length
    removed = 0
    for i, removal in enumerate(removals):
        marker = sub(sequence, "marker")
        where = removal["start"] - kept[0]["start"] - removed
        sub(marker, "name", f"Removal {i + 1}: {removal.get('reason', 'approved repair')}")
        sub(marker, "comment", json.dumps(removal))
        sub(marker, "in", where)
        sub(marker, "out", where)
        removed += removal["end"] - removal["start"]
    ET.indent(root, space="  ")
    return root, rows, max_error


def build(config, config_dir):
    fps_fraction = Fraction(str(config["fps"]))
    fps = float(fps_fraction)
    require(fps_fraction.denominator in {1, 1001}, "xmeml rate must be integer or standard NTSC rational")
    serialized_fps = Fraction(round(fps) * 1000, 1001) if fps_fraction.denominator == 1001 else Fraction(round(fps), 1)
    require(fps_fraction > 0 and serialized_fps == fps_fraction, "frame rate cannot round-trip through xmeml timebase/NTSC fields")
    for role, spec in config["sources"].items():
        require(spec.get("variable_frame_rate", False) is False, f"{role}: variable frame rate requires a verified conform workflow")
        require("fps" in spec, f"{role}: explicitly supply probed source fps")
        require(Fraction(str(spec["fps"])) == fps_fraction,
                f"{role}: unequal source frame rates are not supported; choose a verified conform workflow")
    for role, channels in (("program", 2), ("guest_iso", 1), ("host_iso", 1)):
        require(config["audio"][role].get("channels") == channels, f"{role}: unsupported channel layout; expected {channels} channels")
    for spec in list(config["sources"].values()) + list(config["audio"].values()):
        path = Path(spec["path"])
        spec["path"] = str((config_dir / path).resolve() if not path.is_absolute() else path)
        require(Path(spec["path"]).is_file(), f"missing source {spec['path']}")
    start, end = frame(config["master_start_seconds"], fps), frame(config["master_end_seconds"], fps)
    require(0 <= start < end, "invalid master bounds")
    csv_path = config_dir / config["speaker_segments_csv"]
    labels = load_labels(csv_path, start, end, fps)
    parts = camera_schedule(labels, fps, config.get("pacing", {}))
    full_ranges = [{"start": start, "end": end}]
    variants = [("FULL", assembled(parts, full_ranges, start, fps), full_ranges, [])]
    rejected, accepted = [], []
    if "approved_removals" in config:
        for raw in sorted(config["approved_removals"], key=lambda r: r["start_master_seconds"]):
            removal = dict(raw, start=frame(raw["start_master_seconds"], fps), end=frame(raw["end_master_seconds"], fps))
            try:
                proposal = accepted + [removal]
                kept = retained(start, end, proposal)
                assembled(parts, kept, start, fps)
                accepted = proposal
            except ValueError as error:
                rejected.append(dict(raw, rejection=str(error)))
        kept = retained(start, end, accepted)
        variants.append(("TIGHTENED", assembled(parts, kept, start, fps), kept, accepted))
    if config.get("trailer_ranges"):
        ranges = [dict(r, start=frame(r["start_master_seconds"], fps), end=frame(r["end_master_seconds"], fps))
                  for r in config["trailer_ranges"]]
        variants.append(("TRAILER-DRAFT", assembled(parts, ranges, start, fps, trailer=True), ranges, []))
    out = (config_dir / config["output_dir"]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"fps": str(fps_fraction), "sync_convention": "source_seconds = offset_seconds + drift_ratio * master_seconds",
              "audio_delivery_mode": config.get("audio_delivery_mode", "recorder_mix"),
              "audio_effect_status": "Editable gain/pan encoded in XML; native interpretation and loudness not verified by generator",
              "sync_method": "per-cut video slip; no retime; audio retains master cadence",
              "source_media": config["sources"], "audio_media": config["audio"],
              "color_status": "XML labels only; source/master transforms must be verified in Premiere",
              "master_in_frame": start, "master_out_frame": end, "unknown_speaker_seconds": labels.count("unknown") / fps,
              "rejected_removals": rejected, "accepted_removals": accepted, "sequences": {}}
    podcast_roots = []
    for label, shots, kept, removals in variants:
        name = config.get("episode_name", "Podcast") + " — " + label
        root, rows, error = make_xml(config, name, shots, kept, removals, fps_fraction)
        if label != "TRAILER-DRAFT":
            podcast_roots.append(root)
        variant_out = (config_dir / config.get("trailer_output_dir", config["output_dir"])).resolve() if label == "TRAILER-DRAFT" else out
        variant_out.mkdir(parents=True, exist_ok=True)
        xml_path, cut_path = variant_out / f"{label}.xml", variant_out / f"{label}-cuts.csv"
        ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
        with cut_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        totals = {role: sum(s["end"] - s["start"] for s in shots if s["role"] == role) for role in config["sources"]}
        duration = shots[-1]["end"]
        report["sequences"][label] = {"xml": str(xml_path), "cut_csv": str(cut_path), "duration_frames": duration,
            "duration_seconds": duration / fps, "duration_timecode": nd_timecode(duration, round(fps)),
            "shot_count": len(shots), "minimum_shot_seconds": min(s["end"] - s["start"] for s in shots) / fps,
            "camera_frames": totals, "camera_percent": {k: 100 * v / duration for k, v in totals.items()},
            "wide_share_note": "Diagnostic, not a quota; review pacing by picture.",
            "max_within_shot_sync_error_bound_seconds": error, "removal_marker_count": len(removals)}
    combined_path = out / "PODCAST.xml"
    ET.ElementTree(combine_podcast(podcast_roots, config.get("episode_name", "Podcast"))).write(combined_path, encoding="utf-8", xml_declaration=True)
    report["podcast_combined_xml"] = str(combined_path)
    (out / "edit-summary.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(json.loads(args.config.read_text()), args.config.resolve().parent), indent=2))
