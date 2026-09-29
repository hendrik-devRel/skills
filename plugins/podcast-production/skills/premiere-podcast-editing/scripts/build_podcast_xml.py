#!/usr/bin/env python3
"""Build ungraded FCP7 nested-angle XML from an explicit podcast edit JSON config.

Requires Python 3.10+ and ffprobe on PATH (or --ffprobe). Only writes the requested
XML and its .manifest.json; never imports into Premiere or modifies source media.
See ../references/xml-config.md for the config contract and native review limits.
"""
from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction
import hashlib
import shutil
import sys
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlparse
import uuid
import xml.etree.ElementTree as ET

# Initialized explicitly by build(); one configuration per CLI invocation.
FPS_NUM = FPS_DEN = FPS = TIMEBASE = NTSC = None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), f"{label} must be a finite number")
    return float(value)


def configure_rate(value):
    global FPS_NUM, FPS_DEN, FPS, TIMEBASE, NTSC
    require(isinstance(value, str) and "/" in value,
            'fps must be a rational string, for example "60000/1001"')
    fraction = Fraction(value)
    integer_rates = {24, 25, 30, 50, 60}
    if fraction.denominator == 1 and fraction.numerator in integer_rates:
        TIMEBASE, NTSC = fraction.numerator, "FALSE"
    elif fraction in {Fraction(n * 1000, 1001) for n in (24, 30, 60)}:
        TIMEBASE, NTSC = round(float(fraction)), "TRUE"
    else:
        raise ValueError("Supported FPS: 24/1, 25/1, 30/1, 50/1, 60/1, 24000/1001, 30000/1001, 60000/1001")
    FPS_NUM, FPS_DEN = fraction.numerator, fraction.denominator
    FPS = float(fraction)


def keys(value, allowed, label):
    require(isinstance(value, dict), f"{label} must be an object")
    require(not (set(value) - set(allowed)),
            f"Unknown keys in {label}: {sorted(set(value) - set(allowed))}")


def ranges(value):
    require(isinstance(value, list) and value, "keep_ranges must be a nonempty list")
    previous = -1
    result = []
    for pair in value:
        require(isinstance(pair, list) and len(pair) == 2, "Each keep range needs [start, end]")
        a, z = (number(v, "keep range time") for v in pair)
        require(0 <= a < z and a >= previous and frame(z) > frame(a),
                "Keep ranges must be positive-length, ordered, non-overlapping recorder seconds")
        result.append([a, z])
        previous = z
    return result


def make_spans(keeps):
    spans, timeline = [], 0
    for a_seconds, z_seconds in keeps:
        a, z = frame(a_seconds), frame(z_seconds)
        spans.append({"recorder_start_frame": a, "recorder_end_frame": z,
                      "timeline_start_frame": timeline, "timeline_end_frame": timeline + z - a})
        timeline += z - a
    return spans, timeline


def validate_plan(plan, spans, cameras):
    expected = 0
    for shot in plan:
        a, z = shot["timeline_start_frame"], shot["timeline_end_frame"]
        ra, rz = shot["recorder_start_frame"], shot["recorder_end_frame"]
        require(shot["camera"] in cameras, f"Unknown camera: {shot['camera']}")
        require(a == expected and z > a and rz - ra == z - a, "Camera plan must be contiguous and duration preserving")
        require(any(s["timeline_start_frame"] <= a < z <= s["timeline_end_frame"]
                    and ra - s["recorder_start_frame"] == a - s["timeline_start_frame"] for s in spans),
                "Shot does not map to one retained recorder interval")
        expected = z
    require(expected == spans[-1]["timeline_end_frame"], "Camera plan does not cover all retained media")


def explicit_plan(shots, keeps, cameras):
    spans, duration = make_spans(keeps)
    plan = []
    previous = -1
    for shot in shots:
        keys(shot, {"start", "end", "camera", "reason"}, "shot")
        a, z = number(shot["start"], "shot start"), number(shot["end"], "shot end")
        require(0 <= a < z and a >= previous, "Explicit shots must be ordered and non-overlapping")
        previous = z
        require(shot["camera"] in cameras, f"Unknown camera: {shot['camera']}")
        for span in spans:
            left, right = max(frame(a), span["recorder_start_frame"]), min(frame(z), span["recorder_end_frame"])
            if right > left:
                start = span["timeline_start_frame"] + left - span["recorder_start_frame"]
                plan.append({"camera": shot["camera"], "reason": shot.get("reason", "explicit shot"),
                             "recorder_start_frame": left, "recorder_end_frame": right,
                             "timeline_start_frame": start, "timeline_end_frame": start + right - left})
    plan.sort(key=lambda x: x["timeline_start_frame"])
    validate_plan(plan, spans, cameras)
    return plan, spans, duration


def el(parent, tag, value=None, **attrs):
    node = ET.SubElement(parent, tag, attrs)
    if value is not None:
        node.text = str(value)
    return node


def rate(parent):
    node = el(parent, "rate")
    el(node, "timebase", TIMEBASE)
    el(node, "ntsc", NTSC)


def frame(seconds):
    return math.floor(seconds * FPS + 0.5)


def timecode(parent):
    node = el(parent, "timecode")
    rate(node)
    el(node, "string", "00:00:00:00")
    el(node, "frame", 0)
    el(node, "displayformat", "NDF")


def video_characteristics(parent, width, height):
    node = el(parent, "samplecharacteristics")
    rate(node)
    el(node, "width", width)
    el(node, "height", height)
    el(node, "anamorphic", "FALSE")
    el(node, "pixelaspectratio", "square")
    el(node, "fielddominance", "none")


def motion_scale(clip, value):
    effect = el(el(clip, "filter"), "effect")
    for key, val in [("name", "Basic Motion"), ("effectid", "basic"),
                     ("effectcategory", "motion"), ("effecttype", "motion"),
                     ("mediatype", "video")]:
        el(effect, key, val)
    parameter = el(effect, "parameter")
    for key, val in [("parameterid", "scale"), ("name", "Scale"),
                     ("valuemin", 0), ("valuemax", 1000), ("value", value)]:
        el(parameter, key, val)


def camera_plan(segments, keeps, speaker_camera_map, wide_camera, policy):
    """Map retained recorder ranges to contiguous integer-frame editorial shots."""
    # A genuine 5.000s recorder turn can round to 299 frames at 59.94.
    # Accept that one-frame quantization tolerance rather than deleting the turn.
    minimum = math.ceil(policy["minimum_shot_seconds"] * FPS)
    quantized_minimum = max(1, math.floor(policy["minimum_shot_seconds"] * FPS))
    wide_hold = math.ceil(policy["wide_hold_seconds"] * FPS)
    opening_seconds = policy["opening_wide_seconds"]
    closing_seconds = policy["closing_wide_seconds"]
    relief_seconds = policy["relief_after_seconds"]
    planned, spans = [], []
    timeline = 0
    for keep_index, (start_seconds, end_seconds) in enumerate(keeps):
        a, z = frame(start_seconds), frame(end_seconds)
        require(z - a >= minimum, "Automatic planning requires each keep range to be at least minimum_shot_seconds")
        boundaries = {a, z}
        for item in segments:
            boundaries.update(f for f in [frame(item["start"]), frame(item["end"])] if a < f < z)
        parts = []
        ordered = sorted(boundaries)
        for left, right in zip(ordered, ordered[1:]):
            midpoint = (left + right) / 2 / FPS
            speaker = next((s["speaker"] for s in segments if s["start"] <= midpoint < s["end"]), None)
            camera = speaker_camera_map.get(speaker, wide_camera)
            if parts and parts[-1]["camera"] == camera:
                parts[-1]["end"] = right
            else:
                parts.append({"start": left, "end": right, "camera": camera, "reason": "speaker"})

        def override(left, right, reason):
            nonlocal parts
            revised = []
            for shot in parts:
                if shot["end"] <= left or shot["start"] >= right:
                    revised.append(shot)
                    continue
                if shot["start"] < left:
                    revised.append({**shot, "end": left})
                revised.append({"start": max(left, shot["start"]),
                    "end": min(right, shot["end"]), "camera": wide_camera, "reason": reason})
                if shot["end"] > right:
                    revised.append({**shot, "start": right})
            parts = revised

        if keep_index == 0 and opening_seconds:
            override(a, min(z, a + frame(opening_seconds)), "opening wide")
        if keep_index == len(keeps) - 1 and closing_seconds:
            override(max(a, z - math.ceil(closing_seconds * FPS)), z, "closing wide")
        for shot in list(parts):
            if shot["camera"] == wide_camera or not relief_seconds:
                continue
            cursor = shot["start"] + frame(relief_seconds)
            while cursor + wide_hold * 2 <= shot["end"]:
                override(cursor, cursor + wide_hold, "wide relief")
                cursor += wide_hold + frame(relief_seconds)

        # Join identical adjacent angles before enforcing the five-second floor.
        merged = []
        for shot in parts:
            if merged and merged[-1]["camera"] == shot["camera"]:
                merged[-1]["end"] = shot["end"]
                if shot["reason"] not in merged[-1]["reason"]:
                    merged[-1]["reason"] += "; " + shot["reason"]
            else:
                merged.append(dict(shot))
        parts = merged
        i = 0
        while i < len(parts):
            missing = minimum - (parts[i]["end"] - parts[i]["start"])
            if missing <= 0:
                i += 1
                continue
            if i + 1 < len(parts) and parts[i+1]["end"] - parts[i+1]["start"] >= minimum + missing:
                parts[i]["end"] += missing
                parts[i+1]["start"] += missing
            elif i and parts[i-1]["end"] - parts[i-1]["start"] >= minimum + missing:
                parts[i-1]["end"] -= missing
                parts[i]["start"] -= missing
            elif parts[i]["end"] - parts[i]["start"] >= quantized_minimum:
                # Keep the existing one-frame borrowing policy where it works.
                # When neighboring five-second turns cannot donate a frame,
                # retain this valid rounded turn instead of merging it away.
                i += 1
                continue
            elif i:
                parts[i-1]["end"] = parts[i]["end"]
                parts.pop(i)
                i -= 1
            elif len(parts) > 1:
                parts[i+1]["start"] = parts[i]["start"]
                parts.pop(i)
            else:
                require(parts[i]["end"] - parts[i]["start"] >= quantized_minimum, "Retained interval is too short")
            i += 1
        spans.append({"recorder_start_frame": a, "recorder_end_frame": z,
            "timeline_start_frame": timeline, "timeline_end_frame": timeline + z - a})
        for shot in parts:
            require(shot["end"] - shot["start"] >= quantized_minimum, "Shot minimum failed")
            planned.append({"camera": shot["camera"], "reason": shot["reason"],
                "recorder_start_frame": shot["start"], "recorder_end_frame": shot["end"],
                "timeline_start_frame": timeline + shot["start"] - a,
                "timeline_end_frame": timeline + shot["end"] - a})
        timeline += z - a
    require(all(x["timeline_end_frame"] == y["timeline_start_frame"] for x, y in zip(planned, planned[1:])), "Noncontiguous camera plan")
    return planned, spans, timeline


class Builder:
    def __init__(self, config, base_dir, ffprobe):
        self.config, self.base_dir, self.ffprobe = config, base_dir, ffprobe
        self.prefix = config["project_name"]
        require(isinstance(self.prefix, str) and self.prefix.strip(), "project_name must be nonempty")
        self.width, self.height = config["output_resolution"]
        require(all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in (self.width, self.height)),
                "output_resolution must contain two positive integers")
        self.uid = "podcast-" + uuid.uuid4().hex[:12]
        self.counter = 0
        self.audio_files, self.audio_probes = {}, {}
        self.sparse_sequences = set()
        self.root = ET.Element("xmeml", {"version": "5"})
        project = el(self.root, "project")
        el(project, "name", self.prefix + " Import")
        self.children = el(project, "children")
        self.sources, self.sync = {}, {}
        self.angle_ids = {}
        self.report = {"fps": f"{FPS_NUM}/{FPS_DEN}", "id_namespace": self.uid,
                       "sequences": [], "shots": [], "warnings": [],
                       "xml_role": "Ungraded construction interchange. Native grading and project save are separate.",
                       "mutations": "Only generated XML and manifest; source files read-only."}
        require(isinstance(config["cameras"], dict) and config["cameras"], "cameras must be a nonempty object")
        for camera, item in config["cameras"].items():
            require(isinstance(camera, str) and camera.strip(), "Camera IDs must be nonempty strings")
            keys(item, {"path", "sync"}, f"camera {camera}")
            fit = item["sync"]
            keys(fit, {"time_scale", "offset_seconds"}, f"camera {camera} sync")
            scale = number(fit["time_scale"], "measured time_scale")
            offset = number(fit["offset_seconds"], "measured offset_seconds")
            require(scale > 0, "time_scale must be positive")
            path = self.path(item["path"])
            probe = self.probe(path)
            video = [s for s in probe["streams"] if s["codec_type"] == "video"]
            require(len(video) == 1, f"Expected one video stream: {path}")
            stream = video[0]
            target_rate = Fraction(FPS_NUM, FPS_DEN)
            require(Fraction(stream["r_frame_rate"]) == target_rate
                    and Fraction(stream["avg_frame_rate"]) == target_rate,
                    f"Source rates must equal configured FPS (no VFR/retiming support): {path}")
            require(stream.get("nb_frames", "N/A").isdigit(), f"Exact nb_frames required from ffprobe: {path}")
            require(stream.get("sample_aspect_ratio", "1:1") in ("1:1", "N/A"), f"Non-square pixels unsupported: {path}")
            require(stream.get("field_order", "progressive") in ("progressive", "unknown"), f"Interlaced video unsupported: {path}")
            rotations = [float(d.get("rotation", 0)) for d in stream.get("side_data_list", [])]
            rotations.append(float(stream.get("tags", {}).get("rotate", 0)))
            require(all(r % 360 == 0 for r in rotations), f"Rotated video must be normalized first: {path}")
            width, height, frames = int(stream["width"]), int(stream["height"]), int(stream["nb_frames"])
            require(min(width, height, frames) > 0, f"Invalid source dimensions or frames: {path}")
            scale_percent = min(self.width / width, self.height / height) * 100
            require(scale_percent <= 1000, "Required scale exceeds supported Basic Motion range")
            self.sources[camera] = {"path": path, "frames": frames, "width": width, "height": height,
                                    "duration_seconds": frames / FPS, "scale_percent": scale_percent}
            self.sync[camera] = {"fit": {"time_scale": scale, "offset_seconds": offset}}
        self.report["cameras"] = {k: {**v, "path": str(v["path"]), "sync": self.sync[k]["fit"]}
                                  for k, v in self.sources.items()}

    def path(self, value):
        require(isinstance(value, str) and value, "Media path must be a nonempty string")
        path = Path(value).expanduser()
        path = (self.base_dir / path).resolve() if not path.is_absolute() else path.resolve()
        require(path.is_file(), f"Missing media: {path}")
        return path

    def probe(self, path):
        result = subprocess.run([self.ffprobe, "-v", "error", "-show_streams", "-show_format",
                                 "-of", "json", str(path)], check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def audio_info(self, path, channels=None):
        path = self.path(str(path))
        if str(path) not in self.audio_probes:
            probe = self.probe(path)
            streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
            require(len(streams) == 1 and len(probe["streams"]) == 1, f"Expected one standalone audio stream: {path}")
            stream = streams[0]
            require(int(stream["sample_rate"]) == 48000 and stream["codec_name"].startswith("pcm_"),
                    f"Use aligned 48 kHz PCM WAV audio: {path}")
            require(path.suffix.lower() == ".wav", f"Use PCM WAV sources: {path}")
            require("duration_ts" in stream and "time_base" in stream, f"Exact audio duration unavailable: {path}")
            duration = int(stream["duration_ts"]) * Fraction(stream["time_base"])
            frames = int(duration * Fraction(FPS_NUM, FPS_DEN))
            self.audio_probes[str(path)] = (stream, frames, float(duration))
        stream, frames, duration = self.audio_probes[str(path)]
        if channels is not None:
            require(stream["channels"] == channels, f"Expected {channels} audio channels: {path}")
        return path, stream, frames, duration

    def ident(self, kind):
        self.counter += 1
        return f"{self.uid}-{kind}-{self.counter}"

    def bin(self, name):
        node = el(self.children, "bin")
        el(node, "name", name)
        return el(node, "children")

    def sequence(self, parent, name, frames, width, height, audio=False):
        node = el(parent, "sequence", id=self.ident("sequence"))
        el(node, "name", name)
        el(node, "duration", frames)
        rate(node)
        el(node, "in", 0)
        el(node, "out", frames)
        timecode(node)
        media = el(node, "media")
        video = el(media, "video")
        video_characteristics(el(video, "format"), width, height)
        track = el(video, "track")
        el(track, "enabled", "TRUE")
        el(track, "locked", "FALSE")
        audio_node = None
        if audio:
            audio_node = el(media, "audio")
            el(audio_node, "numOutputChannels", 2)
            sample = el(el(audio_node, "format"), "samplecharacteristics")
            el(sample, "depth", 24)
            el(sample, "samplerate", 48000)
            # A stereo master; each mono track is centered explicitly below.
            outputs = el(audio_node, "outputs")
            group = el(outputs, "group")
            el(group, "index", 1)
            el(group, "numchannels", 2)
            el(group, "downmix", 0)
            for n in [1, 2]:
                el(el(group, "channel"), "index", n)
        self.report["sequences"].append({"id": node.attrib["id"], "name": name,
            "width": width, "height": height, "frames": frames,
            "duration_seconds": frames / FPS})
        return node, track, audio_node

    def clip(self, track, name, source_frames, start, end, source_in):
        require(0 <= start < end and 0 <= source_in < source_in + end - start <= source_frames,
                f"Out-of-bounds clip {name}: source {source_in}:{source_in + end - start}/{source_frames}, timeline {start}:{end}")
        node = el(track, "clipitem", id=self.ident("clip"))
        el(node, "name", name)
        el(node, "enabled", "TRUE")
        el(node, "duration", source_frames)
        rate(node)
        el(node, "start", start)
        el(node, "end", end)
        el(node, "in", source_in)
        el(node, "out", source_in + end - start)
        return node

    def original_video_file(self, clip, source):
        file = el(clip, "file", id=self.ident("file"))
        el(file, "name", source["path"].name)
        el(file, "pathurl", source["path"].as_uri())
        rate(file)
        el(file, "duration", source["frames"])
        timecode(file)
        video_characteristics(el(el(file, "media"), "video"),
                              source["width"], source["height"])
        source_track = el(clip, "sourcetrack")
        el(source_track, "mediatype", "video")
        el(source_track, "trackindex", 1)

    def angles(self):
        parent = self.bin("00 ANGLES — grade each original once")
        for camera in self.sources:
            source = self.sources[camera]
            name = f"{self.prefix}_ANGLE_{camera.upper()}"
            seq, track, _ = self.sequence(parent, name, source["frames"],
                                         source["width"], source["height"])
            self.angle_ids[camera] = seq.attrib["id"]
            clip = self.clip(track, source["path"].name, source["frames"],
                             0, source["frames"], 0)
            self.original_video_file(clip, source)

    def nested_shot(self, track, camera, timeline_start, timeline_end, recorder_time):
        fit = self.sync[camera]["fit"]
        source_seconds = (recorder_time - fit["offset_seconds"]) / fit["time_scale"]
        source_in = frame(source_seconds)
        source = self.sources[camera]
        clip = self.clip(track, f"{self.prefix}_ANGLE_{camera.upper()}",
                         source["frames"], timeline_start, timeline_end, source_in)
        # The complete ANGLE definition precedes this reference in the project bin.
        el(clip, "sequence", id=self.angle_ids[camera])
        source_track = el(clip, "sourcetrack")
        el(source_track, "mediatype", "video")
        if not math.isclose(source["scale_percent"], 100):
            motion_scale(clip, source["scale_percent"])
        self.report["shots"].append({"camera": camera, "clip_id": clip.attrib["id"],
            "start_frame": timeline_start, "end_frame": timeline_end,
            "recorder_start_seconds": recorder_time, "source_seconds": source_seconds,
            "source_in_frame": source_in, "source_out_frame": source_in + timeline_end - timeline_start,
            "source_quantization_error_seconds": source_in / FPS - source_seconds,
            "maximum_within_shot_drift_seconds":
                (timeline_end - timeline_start) / FPS * abs(fit["time_scale"] - 1),
            "scale_percent": source["scale_percent"]})

    def audio_track(self, audio_node, path, name, spans, source_channel=1, pan=0, muted=False):
        path, stream, source_frames, _ = self.audio_info(path)
        require(1 <= source_channel <= stream["channels"], "Requested source audio channel is absent")
        track = el(audio_node, "track")
        el(track, "enabled", "FALSE" if muted else "TRUE")
        el(track, "locked", "FALSE")
        clips = []
        for span in spans:
            clip = self.clip(track, name, source_frames, span["timeline_start_frame"],
                span["timeline_end_frame"], span["recorder_start_frame"])
            if muted:
                clip.find("enabled").text = "FALSE"
            file_id = self.audio_files.get(str(path))
            if file_id:
                el(clip, "file", id=file_id)
            else:
                file_id = self.ident("file")
                self.audio_files[str(path)] = file_id
                file = el(clip, "file", id=file_id)
                el(file, "name", path.name)
                el(file, "pathurl", path.as_uri())
                rate(file)
                el(file, "duration", source_frames)
                audio = el(el(file, "media"), "audio")
                sample = el(audio, "samplecharacteristics")
                el(sample, "depth", int(stream.get("bits_per_sample") or 24))
                el(sample, "samplerate", int(stream["sample_rate"]))
                el(audio, "channelcount", stream["channels"])
            st = el(clip, "sourcetrack")
            el(st, "mediatype", "audio")
            el(st, "trackindex", source_channel)
            effect = el(el(clip, "filter"), "effect")
            for key, val in [("name", "Audio Pan"), ("effectid", "audiopan"),
                ("effectcategory", "audio"), ("effecttype", "audio"), ("mediatype", "audio")]:
                el(effect, key, val)
            parameter = el(effect, "parameter")
            for key, val in [("parameterid", "pan"), ("name", "Pan"),
                ("valuemin", -1), ("valuemax", 1), ("value", pan)]:
                el(parameter, key, val)
            clips.append(clip)
        el(track, "outputchannelindex", 2 if pan == 1 else 1)
        return clips

    def stereo_master(self, audio_node, master, spans):
        left = self.audio_track(audio_node, master, "MASTER_STEREO_L — calibrated 0dB", spans, 1, -1)
        right = self.audio_track(audio_node, master, "MASTER_STEREO_R — calibrated 0dB", spans, 2, 1)
        # FCP7 represents the stereo pair as two linked source-channel clips.
        for index, pair in enumerate(zip(left, right), 1):
            for clip in pair:
                for track_index, target in enumerate(pair, 1):
                    link = el(clip, "link")
                    el(link, "linkclipref", target.attrib["id"])
                    el(link, "mediatype", "audio")
                    el(link, "trackindex", track_index)
                    el(link, "clipindex", index)
                    el(link, "groupindex", 1)

    def program(self, parent, name, plan, spans, duration, audio_config, markers):
        validate_plan(plan, spans, self.sources)
        seq, track, audio = self.sequence(parent, name, duration, self.width, self.height, audio=True)
        for shot in plan:
            self.nested_shot(track, shot["camera"], shot["timeline_start_frame"],
                shot["timeline_end_frame"], shot["recorder_start_frame"] / FPS)
            self.report["shots"][-1].update({"sequence_name": name, "reason": shot["reason"]})
        master = self.audio_info(audio_config["master_stereo"], 2)[0]
        self.stereo_master(audio, master, spans)
        stems = []
        for item in audio_config.get("processed_mono_stems", []):
            keys(item, {"name", "path"}, "processed mono stem")
            path = self.audio_info(item["path"], 1)[0]
            self.audio_track(audio, path, item["name"] + " — MUTED STEM", spans, muted=True)
            stems.append(str(path))
        mapped_markers = []
        for item in markers:
            keys(item, {"recorder_seconds", "end_recorder_seconds", "title", "comment"}, "marker")
            a = frame(number(item["recorder_seconds"], "marker time"))
            z = frame(number(item["end_recorder_seconds"], "marker end")) if "end_recorder_seconds" in item else None
            require(a >= 0 and (z is None or z > a), "Marker times must form a positive range or point")
            for span in spans:
                if z is None:
                    if not span["recorder_start_frame"] <= a < span["recorder_end_frame"]:
                        continue
                    left, right = a, None
                else:
                    left, right = max(a, span["recorder_start_frame"]), min(z, span["recorder_end_frame"])
                    if right <= left:
                        continue
                at = span["timeline_start_frame"] + left - span["recorder_start_frame"]
                stop = -1 if right is None else span["timeline_start_frame"] + right - span["recorder_start_frame"]
                marker = el(seq, "marker")
                el(marker, "name", item["title"])
                el(marker, "comment", item.get("comment", "Recorder-time editorial marker"))
                el(marker, "in", at)
                el(marker, "out", stop)
                mapped_markers.append({**item, "timeline_in_frame": at, "timeline_out_frame": stop})
        for previous, following in zip(spans, spans[1:]):
            if previous["recorder_end_frame"] == following["recorder_start_frame"]:
                continue
            marker = el(seq, "marker")
            el(marker, "name", "REVIEW: removed interval")
            el(marker, "comment", f"Recorder {previous['recorder_end_frame']/FPS:.3f}s to {following['recorder_start_frame']/FPS:.3f}s. Review picture and audio continuity.")
            el(marker, "in", following["timeline_start_frame"])
            el(marker, "out", -1)
        self.report.setdefault("programs", []).append({"sequence_name": name,
            "spans": spans, "frames": duration, "duration_seconds": duration / FPS,
            "video_shots": len(plan), "markers": mapped_markers,
            "minimum_shot_seconds": min(s["timeline_end_frame"]-s["timeline_start_frame"] for s in plan) / FPS,
            "audio": {"audible": str(master), "master_gain_db": 0,
                      "representation": "Linked L/R source channels on two tracks, hard-panned L/R",
                      "muted_processed_stems": stems, "stem_mute": "track disabled and clip disabled"}})

    def sync_assembly(self, parent, config, raw_mics):
        keys(config, {"name", "duration_seconds", "chunk_seconds"}, "sync_assembly")
        require(raw_mics, "sync_assembly requires audio.raw_mono_mics")
        raw = []
        for item in raw_mics:
            keys(item, {"name", "path"}, "raw mono microphone")
            path, _, frames, _ = self.audio_info(item["path"], 1)
            raw.append((path, item["name"], frames))
        max_duration = min(n for _, _, n in raw)
        duration = frame(number(config["duration_seconds"], "sync duration")) if "duration_seconds" in config else max_duration
        require(0 < duration <= max_duration, "Sync duration exceeds the shortest raw microphone")
        chunk = frame(number(config.get("chunk_seconds", 60), "sync chunk_seconds"))
        require(chunk >= 1, "sync chunk_seconds must be positive")
        seq, first_track, audio = self.sequence(parent, config["name"], duration, self.width, self.height, audio=True)
        self.sparse_sequences.add(seq.attrib["id"])
        video = seq.find("media/video")
        for index, camera in enumerate(self.sources):
            track = first_track if index == 0 else el(video, "track")
            if index:
                el(track, "enabled", "TRUE")
                el(track, "locked", "FALSE")
            fit, source = self.sync[camera]["fit"], self.sources[camera]
            start = max(0, math.ceil(fit["offset_seconds"] * FPS))
            coverage_end = source["frames"] / FPS * fit["time_scale"] + fit["offset_seconds"]
            end = min(duration, math.floor(coverage_end * FPS))
            cursor = start
            while cursor < end:
                stop = min(end, cursor + chunk)
                source_in = frame((cursor / FPS - fit["offset_seconds"]) / fit["time_scale"])
                stop = min(stop, cursor + source["frames"] - source_in)
                if stop <= cursor:
                    break
                self.nested_shot(track, camera, cursor, stop, cursor / FPS)
                self.report["shots"][-1].update({"sequence_name": config["name"], "reason": "sync assembly; affine reset at each chunk"})
                cursor = stop
        spans = [{"recorder_start_frame": 0, "recorder_end_frame": duration,
                  "timeline_start_frame": 0, "timeline_end_frame": duration}]
        for path, name, _ in raw:
            self.audio_track(audio, path, name + " — ORIGINAL MONO", spans)
        marker = el(seq, "marker")
        el(marker, "name", "SYNC REFERENCE — continuous raw microphone tracks")
        el(marker, "comment", "Recorder clock; stacked cameras have natural start/end gaps. Disable upper tracks to inspect angles. This is a sync reference, not a loudness-calibrated delivery.")
        el(marker, "in", 0)
        el(marker, "out", -1)

    def validate(self):
        definitions, refs = {}, []
        for node in self.root.iter():
            ident = node.get("id")
            if ident:
                if len(node):
                    require(ident not in definitions, f"Duplicate definition: {ident}")
                    definitions[ident] = node.tag
                else:
                    refs.append((node.tag, ident))
        require(all(definitions.get(i) == tag for tag, i in refs), "Unresolved XML reference")
        for node in self.root.findall(".//pathurl"):
            require(Path(unquote(urlparse(node.text).path)).is_file(), f"Missing XML media: {node.text}")
        for node in self.root.findall(".//linkclipref"):
            require(definitions.get(node.text) == "clipitem", "Invalid audio link reference")
        for seq in self.root.findall(".//sequence"):
            if not len(seq):
                continue
            for track in seq.findall("media/video/track") + seq.findall("media/audio/track"):
                expected = 0
                for clip in track.findall("clipitem"):
                    start, end = int(clip.findtext("start")), int(clip.findtext("end"))
                    source_in, source_out = int(clip.findtext("in")), int(clip.findtext("out"))
                    sparse = seq.attrib["id"] in self.sparse_sequences
                    require((start >= expected if sparse else start == expected) and end > start, "Timeline gap or overlap")
                    require(source_out - source_in == end - start and 0 <= source_in < source_out <= int(clip.findtext("duration")), "Invalid source bounds")
                    expected = end
                require(expected <= int(seq.findtext("duration")) if sparse else expected == int(seq.findtext("duration")), "Track duration mismatch")
        self.report["structural_validation"] = {
            "unique_id_definitions": len(definitions), "resolved_references": len(refs),
            "source_paths_exist": True, "delivery_tracks_gap_free": True,
            "sync_assembly_has_intentional_camera_start_end_gaps": bool(self.sparse_sequences),
            "all_in_out_ranges_in_bounds": True,
            "premiere_import_verified": False,
        }

    def save(self, destination):
        self.validate()
        ET.indent(self.root, space="  ")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n'
                                + ET.tostring(self.root, encoding="utf-8") + b"\n")
        ET.parse(destination)
        report = destination.with_suffix(".manifest.json")
        self.report["xml_sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
        report.write_text(json.dumps(self.report, indent=2) + "\n")
        return report


def read_array(value, base_dir, field):
    if isinstance(value, str):
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        value = json.loads(path.read_text())
        if isinstance(value, dict):
            value = value[field]
    require(isinstance(value, list), f"{field} must be an array or a JSON file containing an array / {field} array")
    return value


def preview_plan(parent, requested_frames):
    plan, spans, duration = parent
    require(0 < requested_frames <= duration, "Preview length must fit its parent sequence")
    clipped_spans, clipped_plan = [], []
    for source, target in ((spans, clipped_spans), (plan, clipped_plan)):
        for item in source:
            if item["timeline_start_frame"] >= requested_frames:
                break
            stop = min(item["timeline_end_frame"], requested_frames)
            target.append({**item, "timeline_end_frame": stop,
                "recorder_end_frame": item["recorder_start_frame"] + stop - item["timeline_start_frame"]})
    return clipped_plan, clipped_spans, requested_frames


def build(config, base_dir, destination, ffprobe="ffprobe", overwrite=False):
    keys(config, {"schema_version", "project_name", "fps", "output_resolution", "cameras", "audio",
                  "speaker_camera_map", "wide_camera", "speaker_segments", "edit_policy", "sequences", "sync_assembly"}, "config")
    require(config.get("schema_version") == 1, "schema_version must be 1")
    configure_rate(config["fps"])
    executable = shutil.which(ffprobe)
    require(executable is not None, f"ffprobe not found: {ffprobe}")
    destination = Path(destination).expanduser().resolve()
    require(destination.suffix.lower() == ".xml", "Output must end in .xml")
    require(overwrite or (not destination.exists() and not destination.with_suffix(".manifest.json").exists()),
            "Output or manifest already exists; use a new path or --overwrite")
    base_dir = Path(base_dir).resolve()
    input_json_paths = set()
    external_arrays = [config.get("speaker_segments")]
    for spec in config.get("sequences", []):
        if isinstance(spec, dict):
            external_arrays.extend([spec.get("shots"), spec.get("markers")])
    for value in external_arrays:
        if isinstance(value, str):
            path = Path(value).expanduser()
            input_json_paths.add((base_dir / path).resolve() if not path.is_absolute() else path.resolve())
    require(not ({destination, destination.with_suffix(".manifest.json").resolve()} & input_json_paths),
            "Output and manifest must not overwrite editorial input JSON")
    b = Builder(config, base_dir, executable)
    audio = config["audio"]
    keys(audio, {"master_stereo", "processed_mono_stems", "raw_mono_mics", "recorder_aligned"}, "audio")
    require(audio.get("recorder_aligned") is True,
            "audio.recorder_aligned must explicitly confirm that all audio starts at recorder t=0, with processing latency compensated")
    policy = {"minimum_shot_seconds": 5, "opening_wide_seconds": 8, "closing_wide_seconds": 5,
              "relief_after_seconds": 65, "wide_hold_seconds": 5}
    overrides = config.get("edit_policy", {})
    keys(overrides, set(policy), "edit_policy")
    policy.update(overrides)
    policy = {k: number(v, k) for k, v in policy.items()}
    require(policy["minimum_shot_seconds"] * FPS >= 1 and policy["wide_hold_seconds"] * FPS >= 1
            and all(v >= 0 for v in policy.values()), "Invalid edit_policy durations")
    mapping = config.get("speaker_camera_map", {})
    require(isinstance(mapping, dict) and all(v in b.sources for v in mapping.values()), "speaker_camera_map contains an unknown camera")
    segments = read_array(config.get("speaker_segments", []), base_dir, "segments")
    previous = -1
    for segment in segments:
        require(isinstance(segment, dict), "Speaker segment must be an object")
        a, z = number(segment["start"], "segment start"), number(segment["end"], "segment end")
        require(0 <= a < z and a >= previous, "Speaker segments must be ordered and non-overlapping")
        require(isinstance(segment["speaker"], str), "Speaker must be a string")
        previous = z
    sequences = config["sequences"]
    require(isinstance(sequences, list) and sequences, "sequences must contain at least one delivery or test sequence")
    b.angles()
    parent = b.bin("01 EDITS — master audible, processed stems disabled")
    built = {}
    all_names = {seq["name"] for seq in b.report["sequences"]}
    for spec in sequences:
        keys(spec, {"name", "keep_ranges", "shots", "markers", "preview_of", "duration_seconds", "include_stems"}, "sequence")
        name = spec["name"]
        require(isinstance(name, str) and name.strip() and name not in all_names, "Sequence names must be nonempty and unique, including angle names")
        all_names.add(name)
        if "preview_of" in spec:
            require(not ({"keep_ranges", "shots"} & set(spec)), "A preview inherits keeps and shots")
            require(spec["preview_of"] in built, "preview_of must name an earlier sequence")
            planned = preview_plan(built[spec["preview_of"]], frame(number(spec["duration_seconds"], "preview duration")))
        else:
            require("duration_seconds" not in spec, "duration_seconds is only for previews")
            keeps = ranges(spec["keep_ranges"])
            if "shots" in spec:
                planned = explicit_plan(read_array(spec["shots"], base_dir, "shots"), keeps, b.sources)
            else:
                require(config.get("wide_camera") in b.sources, "Automatic planning requires an explicit wide_camera")
                require(segments and mapping, "Automatic planning requires speaker_segments and speaker_camera_map")
                planned = camera_plan(segments, keeps, mapping, config["wide_camera"], policy)
        validate_plan(planned[0], planned[1], b.sources)
        markers = read_array(spec.get("markers", []), base_dir, "markers")
        require(isinstance(spec.get("include_stems", True), bool), "include_stems must be boolean")
        seq_audio = audio if spec.get("include_stems", True) else {**audio, "processed_mono_stems": []}
        b.program(parent, name, *planned, seq_audio, markers)
        built[name] = planned
    if config.get("sync_assembly") is not None:
        require(config["sync_assembly"]["name"] not in all_names, "Sync sequence name must be unique")
        b.sync_assembly(b.bin("02 SYNC — original microphones, stacked cameras"), config["sync_assembly"], audio.get("raw_mono_mics", []))
    protected = {s["path"] for s in b.sources.values()} | {Path(p) for p in b.audio_probes}
    require(destination not in protected and destination.with_suffix(".manifest.json").resolve() not in protected,
            "Output must not overwrite input media")
    b.report["edit_policy"] = policy
    b.report["minimum_shot_quantization_tolerance_frames"] = max(1, math.floor(policy["minimum_shot_seconds"] * FPS))
    maximum = max(s["maximum_within_shot_drift_seconds"] for s in b.report["shots"])
    b.report["maximum_within_shot_drift_seconds"] = maximum
    if maximum > 0.04:
        b.report["warnings"].append("Some shots exceed 40 ms estimated intra-shot clock drift; shorten those shots/chunks or use a separately verified retiming workflow.")
    b.report["input_config_sha256"] = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    report = b.save(destination)
    return {"xml": str(destination), "manifest": str(report), "programs": b.report["programs"],
            "validation": b.report["structural_validation"], "warnings": b.report["warnings"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="JSON config; relative input paths resolve beside this file")
    parser.add_argument("--output", type=Path, required=True, help="New XML path; relative to current directory")
    parser.add_argument("--ffprobe", default="ffprobe", help="ffprobe executable name or absolute path")
    parser.add_argument("--overwrite", action="store_true", help="Replace only the requested XML and its manifest")
    args = parser.parse_args()
    try:
        config_path = args.config.expanduser().resolve()
        destination = args.output.expanduser().resolve()
        require(config_path not in {destination, destination.with_suffix(".manifest.json").resolve()},
                "Output and manifest must differ from config")
        result = build(json.loads(config_path.read_text()), config_path.parent, args.output, args.ffprobe, args.overwrite)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
