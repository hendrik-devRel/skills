#!/usr/bin/env python3
import copy
import csv
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from build_episode_edit import build, nd_timecode, source_range
from validate_episode_xml import validate


class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for role in ("guest", "host", "wide", "program", "guest_iso", "host_iso"):
            (self.root / f"{role}.media").touch()
        self.config = {"episode_name": "Synthetic test", "fps": "60000/1001", "width": 3840, "height": 2160,
            "master_start_seconds": 10, "master_end_seconds": 150, "output_dir": "out",
            "speaker_segments_csv": "speakers.csv", "sources": {}, "audio": {}}
        for role in ("guest", "host", "wide"):
            self.config["sources"][role] = {"path": f"{role}.media", "duration_seconds": 190,
                "fps": "60000/1001",
                "width": 1920 if role == "host" else 3840, "height": 1080 if role == "host" else 2160,
                "offset_seconds": -2, "drift_ratio": .99998}
        for role in ("program", "guest_iso", "host_iso"):
            self.config["audio"][role] = {"path": f"{role}.media", "duration_seconds": 200,
                "channels": 2 if role == "program" else 1}
        with (self.root / "speakers.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["start_master_seconds", "end_master_seconds", "state"])
            writer.writerows([(0, 65, "guest"), (65, 74, "host"), (74, 76, "overlap"),
                             (76, 110, "guest"), (110, 114, "silence"), (114, 200, "host")])

    def tearDown(self):
        self.temp.cleanup()

    def test_full_mixed_raster_and_independent_validation(self):
        result = build(self.config, self.root)
        full = result["sequences"]["FULL"]
        checked = validate(full["xml"], 3.5, 0)[0]
        self.assertEqual(checked["camera_frames"], full["camera_frames"])
        root = ET.parse(full["xml"])
        hosts = [c for c in root.findall(".//clipitem") if c.get("id").startswith("host-")]
        self.assertTrue(hosts)
        self.assertEqual(hosts[0].findtext("filter/effect/parameter/value"), "200.0")
        self.assertLess(full["max_within_shot_sync_error_bound_seconds"], .05)
        self.assertGreater(full["camera_percent"]["wide"], 0)

    def test_tightening_ripples_three_tracks_and_rejects_flashes(self):
        self.config["approved_removals"] = [
            {"start_master_seconds": 10.2, "end_master_seconds": 10.4, "reason": "unsafe boundary"},
            {"start_master_seconds": 25, "end_master_seconds": 25.6, "reason": "approved host filler"},
            {"start_master_seconds": 26, "end_master_seconds": 26.3, "reason": "cover cannot fit"},
            {"start_master_seconds": 148, "end_master_seconds": 149, "reason": "short final cover"}]
        result = build(self.config, self.root)
        self.assertEqual(len(result["accepted_removals"]), 1)
        self.assertEqual(len(result["rejected_removals"]), 3)
        tight = result["sequences"]["TIGHTENED"]
        validate(tight["xml"], 1, 1)
        self.assertLess(tight["duration_frames"], result["sequences"]["FULL"]["duration_frames"])

    def test_separate_trailer_and_no_invented_content(self):
        self.config["trailer_output_dir"] = "trailer"
        self.config["trailer_ranges"] = [{"start_master_seconds": 90, "end_master_seconds": 110},
                                         {"start_master_seconds": 30, "end_master_seconds": 50},
                                         {"start_master_seconds": 120, "end_master_seconds": 140}]
        result = build(self.config, self.root)
        trailer = result["sequences"]["TRAILER-DRAFT"]
        self.assertEqual(Path(trailer["xml"]).parent, (self.root / "trailer").resolve())
        validate(trailer["xml"], 1, 0)
        self.assertAlmostEqual(trailer["duration_seconds"], 60, delta=.04)

    def test_out_of_bounds_raises_without_clamping(self):
        bad = copy.deepcopy(self.config)
        bad["sources"]["guest"]["duration_seconds"] = 20
        with self.assertRaisesRegex(ValueError, "source bounds fail"):
            build(bad, self.root)
        bad = copy.deepcopy(self.config)
        bad["sources"]["wide"]["offset_seconds"] = -30
        with self.assertRaisesRegex(ValueError, "source bounds fail"):
            build(bad, self.root)

    def test_validator_detects_mutated_audio_state(self):
        result = build(self.config, self.root)
        path = Path(result["sequences"]["FULL"]["xml"])
        tree = ET.parse(path)
        tree.find(".//clipitem[@id='guest_iso-0']/enabled").text = "TRUE"
        tree.write(path)
        with self.assertRaisesRegex(AssertionError, "audio state"):
            validate(path)

    def test_audio_retime_rejected_and_ndf_is_nominal(self):
        with self.assertRaisesRegex(ValueError, "audio retime"):
            source_range({"offset_seconds": 0, "drift_ratio": 1.0001, "duration_seconds": 200,
                          "path": "audio.wav"}, 0, 100, 60000 / 1001, False)
        self.assertEqual(nd_timecode(216000, 60), "01:00:00:00 NDF")

    def test_iso_program_audio_keeps_editable_gain_and_reference_muted(self):
        self.config["audio_delivery_mode"] = "iso_mix"
        self.config["audio"]["guest_iso"].update(gain_db=5.5, pan=0)
        self.config["audio"]["host_iso"].update(gain_db=0, pan=0)
        self.config["approved_removals"] = [{"start_master_seconds": 25, "end_master_seconds": 25.6}]
        self.config["trailer_ranges"] = [{"start_master_seconds": 30, "end_master_seconds": 50},
                                         {"start_master_seconds": 80, "end_master_seconds": 100}]
        result = build(self.config, self.root)
        combined = validate(result["podcast_combined_xml"], expected_audio_mode="iso_mix", expected_audio=self.config["audio"])
        self.assertEqual(len(combined), 2)
        tree = ET.parse(result["podcast_combined_xml"])
        ids = [n.get("id") for n in tree.iter() if n.get("id") and (n.tag != "file" or n.find("pathurl") is not None)]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(tree.findall(".//file[pathurl]")), 6)
        for sequence in result["sequences"].values():
            validate(sequence["xml"], expected_audio_mode="iso_mix", expected_audio=self.config["audio"])
            root = ET.parse(sequence["xml"])
            tracks = root.findall(".//sequence/media/audio/track")
            self.assertEqual([t.findtext("clipitem/enabled") for t in tracks], ["FALSE", "TRUE", "TRUE"])
            for clip in tracks[1].findall("clipitem"):
                self.assertAlmostEqual(float(clip.findtext("filter/effect/parameter/value")), 10 ** (5.5 / 20), places=8)

    def test_unequal_or_unprobed_source_rate_is_rejected(self):
        self.config["sources"]["guest"]["fps"] = "25"
        with self.assertRaisesRegex(ValueError, "unequal source frame rates"):
            build(self.config, self.root)
        del self.config["sources"]["guest"]["fps"]
        with self.assertRaisesRegex(ValueError, "probed source fps"):
            build(self.config, self.root)

    def test_conflicting_enabled_override_and_invalid_gain_are_rejected(self):
        self.config["audio"]["program"]["enabled"] = False
        with self.assertRaisesRegex(ValueError, "conflicts with audio_delivery_mode"):
            build(self.config, self.root)
        del self.config["audio"]["program"]["enabled"]
        self.config["audio"]["guest_iso"]["gain_db"] = 20
        with self.assertRaisesRegex(ValueError, "gain_db outside"):
            build(self.config, self.root)

    def test_validator_checks_later_sequence_and_source_bounds(self):
        result = build(self.config, self.root)
        path = Path(result["sequences"]["FULL"]["xml"])
        tree = ET.parse(path)
        children = tree.find(".//project/children")
        later = copy.deepcopy(children.find("sequence"))
        later.find("media/audio/track/clipitem/enabled").text = "FALSE"
        children.append(later)
        tree.write(path)
        with self.assertRaisesRegex(AssertionError, "audio state"):
            validate(path)
        children.remove(later)
        clip = tree.find(".//sequence/media/video/track/clipitem")
        duration = int(clip.findtext("end")) - int(clip.findtext("start"))
        clip.find("in").text = "999999"
        clip.find("out").text = str(999999 + duration)
        tree.write(path)
        with self.assertRaisesRegex(AssertionError, "source range outside"):
            validate(path)

    def test_unsupported_rate_vfr_and_channel_layout_fail_before_output(self):
        bad = copy.deepcopy(self.config)
        bad["fps"] = "25001/1001"
        for spec in bad["sources"].values():
            spec["fps"] = bad["fps"]
        with self.assertRaisesRegex(ValueError, "round-trip"):
            build(bad, self.root)
        bad = copy.deepcopy(self.config)
        bad["sources"]["guest"]["variable_frame_rate"] = True
        with self.assertRaisesRegex(ValueError, "variable frame rate"):
            build(bad, self.root)
        bad = copy.deepcopy(self.config)
        bad["audio"]["program"]["channels"] = 4
        with self.assertRaisesRegex(ValueError, "unsupported channel layout"):
            build(bad, self.root)
        self.assertFalse((self.root / "out").exists())


if __name__ == "__main__":
    unittest.main()
