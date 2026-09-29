#!/usr/bin/env python3
"""Synthetic XML tests; CLI fixtures use empty source placeholders in a temp folder."""
import copy
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import restructure_podcast_xml as helper


def fixture(wide_frames=1000, include_preview=False, media_root=Path("/synthetic-only")):
    root = ET.Element("xmeml", version="5")
    children = ET.SubElement(ET.SubElement(root, "project"), "children")
    cameras, known_files, count = {}, {}, 0
    def next_id():
        nonlocal count
        count += 1
        return f"fixture-{count}"
    def rate(node):
        r = ET.SubElement(node, "rate")
        helper.put(r, "timebase", 25)
        helper.put(r, "ntsc", "FALSE")
    def sequence(name, duration, ident):
        seq = ET.SubElement(children, "sequence", id=ident)
        helper.put(seq, "name", name)
        helper.put(seq, "duration", duration)
        rate(seq)
        video = ET.SubElement(ET.SubElement(seq, "media"), "video")
        ET.SubElement(video, "format")
        return seq, video
    def track(parent, active=True):
        t = ET.SubElement(parent, "track")
        helper.put(t, "enabled", "TRUE" if active else "FALSE")
        helper.put(t, "locked", "FALSE")
        return t
    def clip(parent, start, end, source_in, source_frames=1000, active=True):
        c = ET.SubElement(parent, "clipitem", id=next_id())
        for key, value in (("name", "synthetic fixture"), ("enabled", "TRUE" if active else "FALSE"),
                           ("duration", source_frames), ("start", start), ("end", end), ("in", source_in), ("out", source_in + end - start)):
            helper.put(c, key, value)
        rate(c)
        return c
    def file_node(c, path, channels=None, frames=1000):
        ident = known_files.get(path)
        if ident:
            ET.SubElement(c, "file", id=ident)
            return
        ident = next_id()
        known_files[path] = ident
        f = ET.SubElement(c, "file", id=ident)
        helper.put(f, "name", Path(path).name)
        helper.put(f, "pathurl", Path(path).as_uri())
        helper.put(f, "duration", frames)
        media = ET.SubElement(f, "media")
        if channels:
            a = ET.SubElement(media, "audio")
            helper.put(a, "channelcount", channels)
            helper.put(ET.SubElement(a, "samplecharacteristics"), "samplerate", 48000)
        else:
            ET.SubElement(media, "video")
    for cam, frames in (("camera_two", wide_frames), ("camera_one", 1000), ("camera_three", 1000)):
        path = str(media_root / f"{cam}.mp4")
        cameras[cam] = {"path": path, "frames": frames, "scale_percent": 100, "sync": {"time_scale": 1, "offset_seconds": 0}}
        seq, video = sequence("Original " + cam, frames, "angle-" + cam)
        c = clip(track(video), 0, frames, 0, frames)
        file_node(c, path, frames=frames)
    spans = [{"timeline_start_frame": 0, "timeline_end_frame": 40, "recorder_start_frame": 100, "recorder_end_frame": 140},
             {"timeline_start_frame": 40, "timeline_end_frame": 90, "recorder_start_frame": 200, "recorder_end_frame": 250}]
    master = str(media_root / "master.wav")
    stems = [str(media_root / f"verified-person-{i}.wav") for i in range(3)]
    programs = []
    for name in (["Synthetic main", "Synthetic unmodified preview"] if include_preview else ["Synthetic main"]):
        seq, video = sequence(name, 90, next_id())
        t = track(video)
        for camera, start, end, si in (("camera_two", 0, 10, 100), ("camera_one", 10, 30, 110),
                                       ("camera_three", 30, 40, 130), ("camera_two", 40, 50, 200), ("camera_three", 50, 90, 210)):
            c = clip(t, start, end, si, cameras[camera]["frames"])
            ET.SubElement(c, "sequence", id="angle-" + camera)
            helper.put(ET.SubElement(c, "sourcetrack"), "mediatype", "video")
        audio = ET.SubElement(seq.find("media"), "audio")
        helper.put(audio, "numOutputChannels", 2)
        master_clips = []
        for source, channels, source_channel, pan, active in [(master, 2, 1, -1, True), (master, 2, 2, 1, True)] + [(p, 1, 1, 0, False) for p in stems]:
            t = track(audio, active)
            current = []
            for s in spans:
                c = clip(t, s["timeline_start_frame"], s["timeline_end_frame"], s["recorder_start_frame"], active=active)
                file_node(c, source, channels)
                st = ET.SubElement(c, "sourcetrack")
                helper.put(st, "mediatype", "audio")
                helper.put(st, "trackindex", source_channel)
                effect = ET.SubElement(ET.SubElement(c, "filter"), "effect")
                helper.put(effect, "effectid", "audiopan")
                parameter = ET.SubElement(effect, "parameter")
                helper.put(parameter, "parameterid", "pan")
                helper.put(parameter, "value", pan)
                current.append(c)
            helper.put(t, "outputchannelindex", 2 if pan == 1 else 1)
            if source == master:
                master_clips.append(current)
        for pair in zip(*master_clips):
            for c in pair:
                for linked in pair:
                    helper.put(ET.SubElement(c, "link"), "linkclipref", linked.get("id"))
        programs.append({"sequence_name": name, "frames": 90, "spans": spans,
                         "audio": {"audible": master, "muted_processed_stems": stems}})
    manifest = {"fps": "25/1", "cameras": cameras, "programs": programs}
    config = {"schema_version": 1, "sequence_names": ["Synthetic main"],
              "video_tracks": [{"camera": c, "label": "Synthetic " + c} for c in cameras],
              "background": {"camera": "camera_two", "confirmed_wide": True, "coverage": "required"},
              "disabled_gap_handles": False, "max_coverage_clip_frames": 20,
              "audio": {"mode": "promote_processed_stems", "stems": [{"path": p, "label": "Verified speaker " + str(i)} for i, p in enumerate(stems)], "keep_unselected_stems_disabled": True}}
    return root, manifest, config


class StructuralTests(unittest.TestCase):
    def apply(self, root, manifest, config):
        config = helper.parse_config(config, Path("/synthetic-only"))
        report = helper.adapt(root, manifest, config)
        helper.validate_structure(root, check_media=False)
        return report

    def test_confirmed_wide_and_three_centered_dialogue_tracks(self):
        root, manifest, config = fixture()
        report = self.apply(root, manifest, config)
        seq = next(s for s in helper.definition_map(root, "sequence").values() if s.findtext("name") == "Synthetic main")
        video = seq.findall("media/video/track")
        self.assertEqual(len(video), 3)
        self.assertFalse(helper.complement([(helper.integer(c, "start"), helper.integer(c, "end")) for c in video[0].findall("clipitem")], 90))
        self.assertEqual(len(seq.findall("media/audio/track")), 3)
        self.assertTrue(all(helper.enabled(t) for t in seq.findall("media/audio/track")))
        self.assertTrue(all(helper.enabled(c) for c in seq.findall("media/audio/track/clipitem")))
        self.assertEqual({p.findtext("value") for p in seq.findall("media/audio/track/clipitem/filter/effect/parameter")}, {"0"})
        self.assertEqual(report["programs"][0]["audio"]["master_tracks_removed"], 2)
        self.assertTrue(report["programs"][0]["visible_camera_and_source_map_unchanged"])
        # Underlying wide coverage after a removed range must jump to recorder 200+.
        c = next(c for c in video[0].findall("clipitem") if helper.integer(c, "start") == 50)
        self.assertEqual(helper.integer(c, "in"), 210)

    def test_no_wide_adds_only_disabled_gap_coverage(self):
        root, manifest, config = fixture()
        config["background"] = None
        config["disabled_gap_handles"] = True
        config["audio"] = {"mode": "preserve"}
        report = self.apply(root, manifest, config)
        for stat in report["programs"][0]["video_tracks"]:
            self.assertEqual(stat["added_background_clips"], 0)
            self.assertGreater(stat["added_disabled_gap_clips"], 0)
        new = [c for c in root.iter("clipitem") if c.get("id").startswith("separate-")]
        self.assertTrue(new and all(not helper.enabled(c) for c in new))

    def test_preserves_file_refs_needed_by_unmodified_preview(self):
        root, manifest, config = fixture(include_preview=True)
        report = self.apply(root, manifest, config)
        self.assertEqual(len(report["relocated_shared_file_definitions"]), 1)
        self.assertTrue(report["original_angle_sequences_unchanged"])

    def test_required_wide_rejects_missing_underlying_source(self):
        root, manifest, config = fixture(wide_frames=215)
        with self.assertRaisesRegex(ValueError, "lacks required underlying coverage"):
            self.apply(root, manifest, config)

    def test_available_wide_reports_natural_gap(self):
        root, manifest, config = fixture(wide_frames=215)
        config["background"]["coverage"] = "available"
        report = self.apply(root, manifest, config)
        self.assertEqual(report["programs"][0]["video_tracks"][0]["unavailable_coverage_ranges"], [[55, 90]])

    def test_rejects_unconfirmed_wide(self):
        root, manifest, config = fixture()
        config["background"]["confirmed_wide"] = False
        with self.assertRaisesRegex(ValueError, "visual confirmation"):
            self.apply(root, manifest, config)

    def test_rejects_unverified_usb_or_silent_combo_mapping(self):
        root, manifest, config = fixture()
        config["audio"]["stems"][0]["path"] = "/synthetic-only/unverified-COMBO-or-USB.wav"
        with self.assertRaisesRegex(ValueError, "known processed mono stems"):
            self.apply(root, manifest, config)

    def test_rejects_double_selected_stem(self):
        root, manifest, config = fixture()
        config["audio"]["stems"].append(copy.deepcopy(config["audio"]["stems"][0]))
        with self.assertRaisesRegex(ValueError, "double dialogue"):
            self.apply(root, manifest, config)

    def test_rejects_manifest_recorder_map_that_differs_from_audio(self):
        root, manifest, config = fixture()
        manifest["programs"][0]["spans"][0]["recorder_start_frame"] += 1
        manifest["programs"][0]["spans"][0]["recorder_end_frame"] += 1
        with self.assertRaisesRegex(ValueError, "recorder spans disagree"):
            self.apply(root, manifest, config)

    def cli_fixture(self, directory):
        base = Path(directory)
        inputs, outputs = base / "inputs", base / "outputs"
        inputs.mkdir()
        outputs.mkdir()
        root, manifest, config = fixture(media_root=inputs)
        config["audio"] = {"mode": "preserve"}
        for node in helper.definition_map(root, "file").values():
            Path(helper.file_path(node, {})).touch()
        raw = ET.tostring(root)
        manifest["xml_sha256"] = hashlib.sha256(raw).hexdigest()
        xml, report, adaptation = inputs / "edit.xml", inputs / "manifest.json", inputs / "adaptation.json"
        xml.write_bytes(raw)
        report.write_text(json.dumps(manifest))
        adaptation.write_text(json.dumps(config))
        output = outputs / "separate.xml"
        argv = ["restructure_podcast_xml.py", str(xml), "--manifest", str(report),
                "--config", str(adaptation), "--output", str(output)]
        return argv, xml, report, output

    def run_cli(self, argv):
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return helper.main()

    def test_cli_writes_outside_skill_and_preserves_inputs_and_existing_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            argv, xml, manifest, output = self.cli_fixture(directory)
            before = xml.read_bytes()
            self.assertEqual(self.run_cli(argv), 0)
            audit = output.with_suffix(".separate-tracks.json")
            first = (output.read_bytes(), audit.read_bytes())
            self.assertEqual(xml.read_bytes(), before)
            result = json.loads(first[1])
            self.assertFalse(result["native_import_verified"])
            self.assertEqual(result["programs"][0]["audio"], {"mode": "preserve", "changed": False})
            self.assertEqual(self.run_cli(argv), 1)
            self.assertEqual((output.read_bytes(), audit.read_bytes()), first)

    def test_cli_rejects_changed_source_xml_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            argv, xml, manifest, output = self.cli_fixture(directory)
            xml.write_bytes(xml.read_bytes() + b"\n")
            self.assertEqual(self.run_cli(argv), 1)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".separate-tracks.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
