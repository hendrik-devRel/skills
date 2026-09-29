#!/usr/bin/env python3
"""Reversible postprocessor for generated nested-angle FCP7 XML.

No Adobe calls or media changes. The installed builder and its inputs are untouched.
Requires a matching builder manifest plus explicit track and audio mappings.
"""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse
import uuid
import xml.etree.ElementTree as ET


def require(ok, message):
    if not ok:
        raise ValueError(message)


def keys(obj, allowed, label):
    require(isinstance(obj, dict), f"{label} must be an object")
    require(not set(obj) - set(allowed), f"Unknown {label} keys: {sorted(set(obj) - set(allowed))}")


def put(parent, tag, value):
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    node.text = str(value)
    return node


def integer(node, name):
    return int(node.findtext(name))


def rounded(value):
    return (value + Fraction(1, 2)).numerator // (value + Fraction(1, 2)).denominator


def definition_map(root, tag):
    return {n.get("id"): n for n in root.iter(tag) if n.get("id") and len(n)}


def path_value(value, base):
    path = Path(value).expanduser()
    return str((base / path if not path.is_absolute() else path).resolve())


def file_path(file_node, definitions):
    node = file_node if len(file_node) else definitions[file_node.get("id")]
    url = urlparse(node.findtext("pathurl", ""))
    require(url.scheme == "file" and url.netloc in ("", "localhost"), "Only local file URLs are supported")
    return str(Path(unquote(url.path)).resolve())


def enabled(node):
    return node.findtext("enabled", "TRUE").upper() == "TRUE"


def source_tuple(clip):
    return (integer(clip, "start"), integer(clip, "end"), integer(clip, "in"), integer(clip, "out"))


def complement(intervals, duration):
    gaps, cursor = [], 0
    for start, end in sorted(intervals):
        require(start >= cursor and end > start, "Overlapping or invalid intervals")
        if cursor < start:
            gaps.append((cursor, start))
        cursor = end
    if cursor < duration:
        gaps.append((cursor, duration))
    return gaps


def parse_config(config, base):
    keys(config, {"schema_version", "sequence_names", "video_tracks", "background", "disabled_gap_handles", "max_coverage_clip_frames", "audio"}, "adaptation config")
    require(config.get("schema_version") == 1, "schema_version must be 1")
    names = config.get("sequence_names")
    require(isinstance(names, list) and names and len(names) == len(set(names)), "Explicit unique sequence_names are required")
    tracks = config.get("video_tracks")
    require(isinstance(tracks, list) and len(tracks) == 3, "video_tracks must explicitly list exactly three cameras, bottom to top")
    for item in tracks:
        keys(item, {"camera", "label"}, "video track")
        require(all(isinstance(item.get(k), str) and item[k].strip() for k in ("camera", "label")), "Each video track needs a camera ID and label")
    require(len({t["camera"] for t in tracks}) == 3, "Each camera must occupy exactly one video track")
    background = config.get("background")
    require("background" in config, "Set background explicitly to null or a confirmed wide mapping")
    if background is not None:
        keys(background, {"camera", "confirmed_wide", "coverage"}, "background")
        require(background.get("confirmed_wide") is True, "An enabled background requires explicit visual confirmation of a wide camera")
        require(background.get("camera") == tracks[0]["camera"], "Confirmed wide background must be the bottom V1 camera")
        require(background.get("coverage") in ("required", "available"), "background.coverage must be required or available")
    require(isinstance(config.get("disabled_gap_handles"), bool), "disabled_gap_handles must be explicit true or false")
    chunk = config.get("max_coverage_clip_frames")
    if background is not None or config["disabled_gap_handles"]:
        require(isinstance(chunk, int) and not isinstance(chunk, bool) and chunk > 0, "Coverage requires explicit positive max_coverage_clip_frames at the verified sequence rate")
    audio = config.get("audio")
    keys(audio, {"mode", "stems", "keep_unselected_stems_disabled"}, "audio")
    require(audio.get("mode") in ("preserve", "promote_processed_stems"), "Choose explicit audio mode")
    if audio["mode"] == "promote_processed_stems":
        require(isinstance(audio.get("keep_unselected_stems_disabled"), bool), "Set keep_unselected_stems_disabled explicitly")
        require(isinstance(audio.get("stems"), list) and audio["stems"], "Promotion needs explicitly verified processed mono stems")
        for item in audio["stems"]:
            keys(item, {"path", "label"}, "stem")
            require(all(isinstance(item.get(k), str) and item[k].strip() for k in ("path", "label")), "Each stem needs a verified path and label")
            item["path"] = path_value(item["path"], base)
        require(len({s["path"] for s in audio["stems"]}) == len(audio["stems"]), "Duplicate selected stem paths would double dialogue")
    else:
        require(not audio.get("stems"), "audio preserve mode must not request stem promotion")
    return config


def locate_angles(root, cameras):
    files = definition_map(root, "file")
    result = {}
    for camera, source in cameras.items():
        path = str(Path(source["path"]).resolve())
        matches = []
        for seq in definition_map(root, "sequence").values():
            clips = seq.findall("media/video/track/clipitem")
            if seq.find("media/audio") is not None or len(clips) != 1 or clips[0].find("file") is None:
                continue
            if file_path(clips[0].find("file"), files) == path:
                require(source_tuple(clips[0]) == (0, source["frames"], 0, source["frames"]), "ANGLE must retain its full source")
                matches.append(seq)
        require(len(matches) == 1, f"Expected one original full-source ANGLE for camera {camera}; found {len(matches)}")
        result[camera] = matches[0]
    return result


def clip_camera(clip, camera_for_angle):
    ref = clip.find("sequence")
    require(ref is not None and ref.get("id") in camera_for_angle, "Target picture must contain only mapped nested ANGLE clips")
    return camera_for_angle[ref.get("id")]


def new_nested_clip(angle, camera, source, start, end, source_in, active, unique_id):
    clip = ET.Element("clipitem", id=unique_id)
    put(clip, "name", angle.findtext("name") + (" — DISABLED COVERAGE" if not active else ""))
    put(clip, "enabled", "TRUE" if active else "FALSE")
    put(clip, "duration", source["frames"])
    clip.append(copy.deepcopy(angle.find("rate")))
    for key, value in (("start", start), ("end", end), ("in", source_in), ("out", source_in + end - start)):
        put(clip, key, value)
    ET.SubElement(clip, "sequence", id=angle.get("id"))
    put(ET.SubElement(clip, "sourcetrack"), "mediatype", "video")
    if source["scale_percent"] != 100:
        effect = ET.SubElement(ET.SubElement(clip, "filter"), "effect")
        for key, value in (("name", "Basic Motion"), ("effectid", "basic"), ("effectcategory", "motion"), ("effecttype", "motion"), ("mediatype", "video")):
            put(effect, key, value)
        parameter = ET.SubElement(effect, "parameter")
        for key, value in (("parameterid", "scale"), ("name", "Scale"), ("valuemin", 0), ("valuemax", 1000), ("value", source["scale_percent"])):
            put(parameter, key, value)
    return clip


def coverage_clips(gaps, spans, camera, source, angle, fps, chunk, active, next_id):
    clips, uncovered, drift = [], [], []
    fit = source["sync"]
    scale, offset = Fraction(str(fit["time_scale"])), Fraction(str(fit["offset_seconds"]))
    require(scale > 0, "Camera time_scale must be positive")
    for gap_a, gap_z in gaps:
        for span in spans:
            a, z = max(gap_a, span["timeline_start_frame"]), min(gap_z, span["timeline_end_frame"])
            if a >= z:
                continue
            def source_at(timeline_frame):
                recorder_frame = span["recorder_start_frame"] + timeline_frame - span["timeline_start_frame"]
                return rounded((Fraction(recorder_frame, 1) / fps - offset) / scale * fps)
            cursor = a
            if source_at(cursor) < 0:
                lo, hi = cursor, z
                while lo < hi:
                    mid = (lo + hi) // 2
                    if source_at(mid) < 0:
                        lo = mid + 1
                    else:
                        hi = mid
                if lo > cursor:
                    uncovered.append([cursor, lo])
                cursor = lo
            while cursor < z:
                source_in = source_at(cursor)
                if source_in >= source["frames"]:
                    uncovered.append([cursor, z])
                    break
                stop = min(z, cursor + chunk, cursor + source["frames"] - source_in)
                require(stop > cursor and source_in >= 0, "Could not construct bounded camera coverage")
                clips.append(new_nested_clip(angle, camera, source, cursor, stop, source_in, active, next_id()))
                drift.append(float(Fraction(stop - cursor, 1) / fps * abs(scale - 1)))
                cursor = stop
    return clips, uncovered, max(drift, default=0)


def visible_map(tracks, camera_for_angle, duration):
    clips = [(track_i, c) for track_i, track in enumerate(tracks) if enabled(track) for c in track.findall("clipitem") if enabled(c)]
    points = sorted({0, duration, *(integer(c, k) for _, c in clips for k in ("start", "end"))})
    result = []
    for a, z in zip(points, points[1:]):
        visible = [(i, c) for i, c in clips if integer(c, "start") <= a < z <= integer(c, "end")]
        require(visible, f"Visible picture gap at {a}:{z}")
        _, clip = max(visible, key=lambda pair: pair[0])
        current = [a, z, clip_camera(clip, camera_for_angle), integer(clip, "in") + a - integer(clip, "start")]
        if result and result[-1][1] == a and result[-1][2] == current[2] and result[-1][3] + a - result[-1][0] == current[3]:
            result[-1][1] = z
        else:
            result.append(current)
    return result


def promote_audio(seq, program, audio_config, files):
    if audio_config["mode"] == "preserve":
        return {"mode": "preserve", "changed": False}
    audio = seq.find("media/audio")
    require(audio is not None, "Target sequence has no audio")
    master = str(Path(program["audio"]["audible"]).resolve())
    allowed = {str(Path(p).resolve()) for p in program["audio"]["muted_processed_stems"]}
    selected = {s["path"]: s for s in audio_config["stems"]}
    require(set(selected) <= allowed, "Selected paths must be known processed mono stems in this sequence manifest")
    found, master_tracks, other_tracks = {}, [], []
    for track in audio.findall("track"):
        clips = track.findall("clipitem")
        require(clips and all(c.find("file") is not None for c in clips), "Unexpected empty or nested audio track")
        paths = {file_path(c.find("file"), files) for c in clips}
        require(len(paths) == 1, "Audio tracks with mixed source files require explicit native review")
        path = next(iter(paths))
        if path == master:
            master_tracks.append(track)
        elif path in selected:
            require(path not in found, "A selected stem exists on multiple tracks; refusing doubled dialogue")
            found[path] = track
            for clip in clips:
                file = clip.find("file")
                file = file if len(file) else files[file.get("id")]
                require(file.findtext("media/audio/channelcount") == "1", "Promotion requires an explicitly extracted one-channel stem")
                require(file.findtext("media/audio/samplecharacteristics/samplerate") == "48000", "Processed stem must be 48 kHz")
                require(clip.findtext("sourcetrack/trackindex") == "1", "Mono stem must use source channel 1")
                expected = [(s["timeline_start_frame"], s["timeline_end_frame"], s["recorder_start_frame"], s["recorder_end_frame"]) for s in program["spans"]]
                require([source_tuple(c) for c in clips] == expected, "Stem timing differs from recorder-aligned keep spans")
                put(clip, "enabled", "TRUE")
                put(clip, "name", selected[path]["label"])
                pans = [e for e in clip.findall("filter/effect") if e.findtext("effectid") == "audiopan"]
                require(len(pans) == 1, "Expected one existing Audio Pan effect on the builder stem")
                params = [p for p in pans[0].findall("parameter") if p.findtext("parameterid") == "pan"]
                require(len(params) == 1 and not params[0].findall("keyframe"), "Animated pan requires native review")
                put(params[0], "value", 0)
                for link in list(clip.findall("link")):
                    clip.remove(link)
            put(track, "enabled", "TRUE")
            put(track, "locked", "FALSE")
            put(track, "outputchannelindex", 1)
        else:
            require(path in allowed, "Unexpected non-master/non-stem audio track; refusing to infer its purpose")
            put(track, "enabled", "FALSE")
            for clip in clips:
                put(clip, "enabled", "FALSE")
            other_tracks.append(track)
    require(len(master_tracks) == 2, "Expected the original linked master L/R pair")
    require(set(found) == set(selected), "Some explicitly selected stems are absent; build with include_stems=true")
    for track in list(audio.findall("track")):
        audio.remove(track)
    for item in audio_config["stems"]:
        audio.append(found[item["path"]])
    if audio_config["keep_unselected_stems_disabled"]:
        for track in other_tracks:
            audio.append(track)
    require(seq.findtext("media/audio/numOutputChannels") == "2", "Expected the existing stereo Mix output group")
    return {"mode": "promote_processed_stems", "master_tracks_removed": 2, "master_path": master,
            "audible_centered_tracks": [{"track_index": i + 1, **item} for i, item in enumerate(audio_config["stems"])],
            "unselected_disabled_tracks_retained": len(other_tracks) if audio_config["keep_unselected_stems_disabled"] else 0,
            "native_pan_law_loudness_and_routing_verification_required": True}


def restore_referenced_file_definitions(root, original_files):
    # A removed master clip may have held the only file definition used by an
    # unmodified preview/sync sequence. Relocate that definition to its first ref.
    present = definition_map(root, "file")
    restored = []
    for parent in root.iter():
        for index, node in enumerate(list(parent)):
            if node.tag == "file" and not len(node) and node.get("id") not in present:
                ident = node.get("id")
                require(ident in original_files, f"Missing original file definition {ident}")
                replacement = copy.deepcopy(original_files[ident])
                parent.remove(node)
                parent.insert(index, replacement)
                present[ident] = replacement
                restored.append(ident)
    return restored


def validate_structure(root, check_media=True):
    definitions, references = {}, []
    for node in root.iter():
        ident = node.get("id")
        if ident:
            if len(node):
                require(ident not in definitions, f"Duplicate ID definition {ident}")
                definitions[ident] = node.tag
            else:
                references.append((node.tag, ident))
    require(all(definitions.get(i) == tag for tag, i in references), "Unresolved or mistyped XML references")
    for ref in root.findall(".//linkclipref"):
        require(definitions.get(ref.text) == "clipitem", "Dangling audio link after restructuring")
    files = definition_map(root, "file")
    if check_media:
        for node in files.values():
            require(Path(file_path(node, files)).is_file(), f"Source file missing: {node.findtext('pathurl')}")
    clip_count = 0
    for seq in definition_map(root, "sequence").values():
        duration = integer(seq, "duration")
        for track in seq.findall("media/video/track") + seq.findall("media/audio/track"):
            cursor = 0
            for clip in track.findall("clipitem"):
                a, z, si, so = source_tuple(clip)
                require(0 <= cursor <= a < z <= duration, "Track overlap, bad order, or sequence overflow")
                require(0 <= si < so <= integer(clip, "duration") and so - si == z - a, "Invalid source bounds or changed clip speed")
                cursor = z
                clip_count += 1
    return {"unique_definitions": len(definitions), "resolved_references": len(references), "clips_checked": clip_count,
            "source_files_exist": check_media, "source_bounds_and_track_order": "PASS"}


def adapt(root, manifest, config):
    fps = Fraction(manifest["fps"])
    cameras = manifest["cameras"]
    camera_ids = [t["camera"] for t in config["video_tracks"]]
    require(set(camera_ids) <= set(cameras), "An explicit camera mapping is absent from the builder manifest")
    angles = locate_angles(root, {k: cameras[k] for k in camera_ids})
    camera_for_angle = {seq.get("id"): cam for cam, seq in angles.items()}
    angle_snapshots = {cam: ET.tostring(seq) for cam, seq in angles.items()}
    files = {ident: copy.deepcopy(node) for ident, node in definition_map(root, "file").items()}
    programs = {p["sequence_name"]: p for p in manifest["programs"]}
    sequences = list(definition_map(root, "sequence").values())
    namespace, counter = "separate-" + uuid.uuid4().hex[:12], 0
    def next_id():
        nonlocal counter
        counter += 1
        return f"{namespace}-clip-{counter}"
    reports = []
    for name in config["sequence_names"]:
        matches = [s for s in sequences if s.findtext("name") == name]
        require(len(matches) == 1 and name in programs, f"Target must uniquely name a regular builder program: {name}")
        seq, program = matches[0], programs[name]
        duration = integer(seq, "duration")
        require(duration == program["frames"], "Sequence/manifest duration mismatch")
        expected_audio_spans, cursor = [], 0
        for span in program["spans"]:
            a, z = span["timeline_start_frame"], span["timeline_end_frame"]
            ra, rz = span["recorder_start_frame"], span["recorder_end_frame"]
            require(all(isinstance(v, int) and not isinstance(v, bool) for v in (a, z, ra, rz)), "Manifest spans must use integer frames")
            require(a == cursor and z > a and ra >= 0 and rz - ra == z - a, "Manifest retained spans must cover a contiguous, duration-preserving recorder map")
            expected_audio_spans.append((a, z, ra, rz))
            cursor = z
        require(cursor == duration, "Manifest retained spans do not cover this sequence")
        master_path = str(Path(program["audio"]["audible"]).resolve())
        master_tracks = [track for track in seq.findall("media/audio/track") if track.findall("clipitem")
                         and all(c.find("file") is not None and file_path(c.find("file"), files) == master_path for c in track.findall("clipitem"))]
        require(len(master_tracks) == 2 and all([source_tuple(c) for c in track.findall("clipitem")] == expected_audio_spans for track in master_tracks),
                "Manifest recorder spans disagree with the original builder master tracks")
        timebase = int(seq.findtext("rate/timebase"))
        actual_fps = Fraction(timebase * 1000, 1001) if seq.findtext("rate/ntsc") == "TRUE" else Fraction(timebase, 1)
        require(actual_fps == fps, "Sequence/manifest frame rate mismatch")
        video = seq.find("media/video")
        original_tracks = video.findall("track")
        require(len(original_tracks) == 1 and enabled(original_tracks[0]), "Target must be the unmodified one-video-track builder output")
        original_clips = original_tracks[0].findall("clipitem")
        require(original_clips and all(enabled(c) for c in original_clips), "Original active cuts must all be enabled")
        before = visible_map(original_tracks, camera_for_angle, duration)
        active_snapshots = {c.get("id"): ET.tostring(c) for c in original_clips}
        tracks, stats = {}, []
        for item in config["video_tracks"]:
            track = ET.Element("track")
            put(track, "enabled", "TRUE")
            put(track, "locked", "FALSE")
            tracks[item["camera"]] = track
        for clip in original_clips:
            original_tracks[0].remove(clip)
            tracks[clip_camera(clip, camera_for_angle)].append(clip)
        for index, item in enumerate(config["video_tracks"], 1):
            cam, track = item["camera"], tracks[item["camera"]]
            active = track.findall("clipitem")
            active_intervals = [(integer(c, "start"), integer(c, "end")) for c in active]
            gaps = complement(active_intervals, duration)
            background = config["background"] is not None and cam == config["background"]["camera"]
            additions, uncovered, drift = [], [], 0
            if background or config["disabled_gap_handles"]:
                additions, uncovered, drift = coverage_clips(gaps, program["spans"], cam, cameras[cam], angles[cam], fps,
                    config["max_coverage_clip_frames"], background, next_id)
                if background and config["background"]["coverage"] == "required":
                    require(not uncovered, f"Confirmed wide lacks required underlying coverage in {name}: {uncovered}")
                for clip in additions:
                    track.append(clip)
            ordered = sorted(track.findall("clipitem"), key=lambda c: integer(c, "start"))
            for clip in list(track.findall("clipitem")):
                track.remove(clip)
            track.extend(ordered)
            stats.append({"track_index": index, **item, "active_editorial_clips": len(active),
                          "added_background_clips": len(additions) if background else 0,
                          "added_disabled_gap_clips": 0 if background else len(additions),
                          "unavailable_coverage_ranges": uncovered, "max_added_clip_drift_estimate_seconds": drift})
        video.remove(original_tracks[0])
        video.extend(tracks.values())
        after = visible_map(list(tracks.values()), camera_for_angle, duration)
        require(before == after, f"Visible camera or source map changed in {name}")
        for clip in seq.findall("media/video/track/clipitem"):
            if clip.get("id") in active_snapshots:
                require(ET.tostring(clip) == active_snapshots[clip.get("id")], "An original editorial clip was altered")
        audio_report = promote_audio(seq, program, config["audio"], files)
        reports.append({"name": name, "frames": duration, "video_tracks": stats, "visible_camera_and_source_map_unchanged": True,
                        "original_active_clip_properties_unchanged": True, "visible_map": after, "audio": audio_report})
    restored = restore_referenced_file_definitions(root, files)
    require(all(ET.tostring(angles[c]) == data for c, data in angle_snapshots.items()), "A full-source ANGLE sequence changed")
    return {"programs": reports, "original_angle_sequences_unchanged": True, "relocated_shared_file_definitions": restored,
            "native_import_verified": False, "track_labels": "Desired labels recorded here; rename/check native track labels after import.",
            "notes": ["All original nests retain full source handles. Disabled gap clips are optional references; trim/remove adjacent disabled references if they block an edge extension.",
                      "No confirmed wide means no enabled background is invented. Extending an active clip may require trimming another active track to preserve the desired topmost view.",
                      "Added coverage uses the explicit camera affine clock at each chunk, without a speed effect, matching the builder model.",
                      "This changes construction XML only. Native import, source scaling, sync, centered routing, pan-law loudness, and output limiting need separate verification."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_xml", type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        inputs = [p.expanduser().resolve() for p in (args.input_xml, args.manifest, args.config)]
        output = args.output.expanduser().resolve()
        report_path = output.with_suffix(".separate-tracks.json")
        require(output.parent.is_dir(), "Create the output directory before running the helper")
        require(output.suffix.lower() == ".xml", "Output must have .xml suffix")
        require(not output.exists() and not report_path.exists(), "Refusing to overwrite an existing output or report")
        require(output not in inputs and report_path not in inputs, "Outputs must differ from every input")
        raw = inputs[0].read_bytes()
        manifest = json.loads(inputs[1].read_text())
        require(hashlib.sha256(raw).hexdigest() == manifest.get("xml_sha256"), "Input XML does not match its builder manifest; do not reconstruct a native edited project")
        config = parse_config(json.loads(inputs[2].read_text()), inputs[2].parent)
        root = ET.fromstring(raw)
        require(root.tag == "xmeml", "Expected FCP7 XMEML")
        report = adapt(root, manifest, config)
        report["structural_validation"] = validate_structure(root)
        report["inputs"] = {"xml": str(inputs[0]), "manifest": str(inputs[1]), "config": str(inputs[2]), "input_xml_sha256": manifest["xml_sha256"]}
        report["fps"] = manifest["fps"]
        ET.indent(root, space="  ")
        data = b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + ET.tostring(root, encoding="utf-8") + b"\n"
        validate_structure(ET.fromstring(data))
        report["output_xml_sha256"] = hashlib.sha256(data).hexdigest()
        with output.open("xb") as stream:
            stream.write(data)
        with report_path.open("x") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
        print(json.dumps({"status": "STRUCTURAL_PASS_NATIVE_IMPORT_PENDING", "xml": str(output), "report": str(report_path)}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
