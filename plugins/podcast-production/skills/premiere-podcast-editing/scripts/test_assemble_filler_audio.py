#!/usr/bin/env python3
"""Synthetic-only verification; all generated media lives in a temporary directory."""
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
import wave

import numpy as np

import assemble_filler_audio as ae


def write_source(path, values):
    with wave.open(str(path), "wb") as writer:
        writer.setparams((values.shape[1], 3, ae.SR, len(values), "NONE", "not compressed"))
        writer.writeframes(ae.pcm24_bytes(values))


class AudioEditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="podcast-audio-edit-test-")
        self.folder = Path(self.tmp.name)
        self.source = self.folder / "source.wav"
        t = np.arange(4 * ae.SR) / ae.SR
        values = np.column_stack((.32 * np.sin(2 * np.pi * 233 * t), .25 * np.sin(2 * np.pi * 317 * t)))
        write_source(self.source, values)
        self.original_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def tearDown(self):
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original_hash)
        self.tmp.cleanup()

    def run_edit(self, manifest, name="result.wav"):
        if isinstance(manifest, dict):
            manifest = {"fps": "60000/1001", **manifest}
        return ae.assemble(manifest, self.source, self.folder / name)

    def assert_qa(self, report):
        self.assertTrue(report["verification"]["passed"])
        self.assertLessEqual(abs(report["duration_error_samples"]), .5)
        self.assertLessEqual(report["verification"]["outside_fades_max_abs_error"], ae.LSB)
        self.assertLessEqual(report["verification"]["sample_peak_overshoot"], ae.LSB)
        for correlation in report["verification"]["outside_fades_correlation_by_channel"]:
            if correlation is not None:
                self.assertGreater(correlation, .999999999)

    def test_exact_cumulative_samples_and_no_mapping_shift(self):
        manifest = {"keep_recorder_frames": [[3, 37], [50, 101], [117, 199]],
                    "joins": [{"fade_ms": 20, "safe_outgoing_handle_ms": 10,
                               "safe_incoming_handle_ms": 10},
                              {"fade_ms": 30, "safe_outgoing_handle_ms": 15,
                               "safe_incoming_handle_ms": 15}]}
        report = self.run_edit(manifest)
        self.assertEqual(report["output_samples"], ae.frame_sample(167))
        self.assertEqual([join["fade_ms"] for join in report["joins"]], [20, 30])
        self.assert_qa(report)

    def test_one_round_not_independently_rounded_segments(self):
        manifest = {"keep_recorder_frames": [[0, 1], [2, 3], [4, 5]],
                    "joins": [{"safe_outgoing_handle_ms": 10, "safe_incoming_handle_ms": 10}] * 2}
        report = self.run_edit(manifest)
        self.assertEqual(report["output_samples"], 2402)
        self.assertNotEqual(report["output_samples"], 3 * ae.frame_sample(1))
        self.assertTrue(all(10 <= j["fade_ms"] <= 20 for j in report["joins"]))
        self.assert_qa(report)

    def test_discontinuity_blended_without_peak_overshoot(self):
        values = np.full((4 * ae.SR, 2), .8)
        values[ae.frame_sample(60):] = -.8
        write_source(self.source, values)
        self.original_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        report = self.run_edit({"keep_recorder_frames": [[0, 59], [61, 180]],
                               "joins": [{"fade_ms": 20, "safe_outgoing_handle_ms": 10,
                                          "safe_incoming_handle_ms": 10}]})
        out = ae.PCM(report["output"])
        join = report["joins"][0]
        samples = out.read(join["output_samples"][0] - 2, 964)
        self.assertLess(float(np.max(np.abs(np.diff(samples, axis=0)))), .004)
        self.assertLessEqual(float(np.max(np.abs(samples))), .8 + ae.LSB)
        self.assert_qa(report)

    def test_room_tone_does_not_reintroduce_deleted_filler(self):
        # Kept content/approved ambience are quiet; deleted interior is a loud synthetic filler.
        values = np.full((4 * ae.SR, 2), .003)
        values[ae.frame_sample(40):ae.frame_sample(60)] = .95
        write_source(self.source, values)
        self.original_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        report = self.run_edit({"keep_recorder_frames": [[0, 40], [60, 160]],
                               "room_tone_recorder_frames": [170, 175],
                               "joins": [{"mode": "crossfade", "fade_ms": 24}]})
        self.assertEqual(report["joins"][0]["mode"], "room_tone")
        self.assertLess(report["verification"]["output_sample_peak"], .003 + ae.LSB)
        self.assertIsNotNone(report["joins"][0]["fallback_reason"])
        self.assert_qa(report)

    def test_safe_handle_cap_and_no_filler_beyond_approved_handles(self):
        values = np.full((4 * ae.SR, 2), .005)
        lo, hi = ae.frame_sample(40), ae.frame_sample(60)
        values[lo + 336:hi - 336] = .95
        write_source(self.source, values)
        self.original_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        report = self.run_edit({"keep_recorder_frames": [[0, 40], [60, 160]],
                               "joins": [{"fade_ms": 30, "safe_outgoing_handle_ms": 7,
                                          "safe_incoming_handle_ms": 7}]})
        self.assertEqual(report["joins"][0]["fade_ms"], 14)
        self.assertLess(report["verification"]["output_sample_peak"], .005 + ae.LSB)
        self.assert_qa(report)

    def test_missing_safe_handles_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "insufficient safe handles"):
            self.run_edit({"keep_recorder_frames": [[0, 40], [60, 160]]})
        self.assertFalse((self.folder / "result.wav").exists())

    def test_reject_invalid_inputs_and_existing_outputs(self):
        for keeps in ([[0, 40], [40, 50]], [[0, 40], [30, 50]], [[0, 1000]], [[0.0, 40]]):
            with self.assertRaises(ValueError):
                self.run_edit({"keep_recorder_frames": keeps})
        self.run_edit({"keep_recorder_frames": [[0, 20]]})
        with self.assertRaisesRegex(ValueError, "never overwritten"):
            self.run_edit({"keep_recorder_frames": [[0, 20]]})

    def test_mono_stem_same_timeline(self):
        values = np.linspace(-.3, .3, 4 * ae.SR)[:, None]
        write_source(self.source, values)
        self.original_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        report = self.run_edit({"keep_recorder_frames": [[3, 37], [50, 101]],
                               "room_tone_recorder_frames": [150, 151],
                               "joins": [{"mode": "room_tone", "fade_ms": 10}]})
        self.assertEqual(report["channels"], 1)
        self.assertEqual(report["output_samples"], ae.frame_sample(85))
        self.assert_qa(report)

    def test_extensible_pcm24_and_rf64_inputs(self):
        values = np.column_stack((np.linspace(-.9, .9, 16000), np.linspace(.7, -.7, 16000)))
        payload = ae.pcm24_bytes(values)
        fmt = struct.pack("<HHIIHHHHI", 0xFFFE, 2, ae.SR, ae.SR * 6, 6, 24, 22, 24, 3)
        fmt += bytes.fromhex("0100000000001000800000aa00389b71")
        body = b"fmt " + struct.pack("<I", len(fmt)) + fmt
        body += b"data" + struct.pack("<I", len(payload)) + payload
        extensible = self.folder / "extensible.wav"
        extensible.write_bytes(b"RIFF" + struct.pack("<I", len(body) + 4) + b"WAVE" + body)
        actual = ae.PCM(extensible)
        self.assertEqual(actual.frames, len(values))
        self.assertLessEqual(float(np.max(np.abs(actual.read(0, len(values)) - values))), ae.LSB)
        # Small synthetic RF64 exercises its 64-bit size path without a multi-gigabyte fixture.
        basic_fmt = struct.pack("<HHIIHH", 1, 2, ae.SR, ae.SR * 6, 6, 24)
        ds64_size = 28
        riff_size = 4 + 8 + ds64_size + 8 + len(basic_fmt) + 8 + len(payload)
        ds64 = struct.pack("<QQQI", riff_size, len(payload), len(values), 0)
        rf64 = self.folder / "rf64.wav"
        rf64.write_bytes(b"RF64\xff\xff\xff\xffWAVEds64" + struct.pack("<I", ds64_size) + ds64
                         + b"fmt " + struct.pack("<I", len(basic_fmt)) + basic_fmt
                         + b"data\xff\xff\xff\xff" + payload)
        actual = ae.PCM(rf64)
        self.assertEqual(actual.frames, len(values))
        self.assertLessEqual(float(np.max(np.abs(actual.read(0, len(values)) - values))), ae.LSB)
        report = ae.assemble({"fps": "60000/1001", "keep_recorder_frames": [[0, 10]]}, extensible,
                             self.folder / "extensible-edited.wav")
        self.assert_qa(report)

    def test_safe_margins_round_down_and_bad_manifest_fails(self):
        self.assertEqual(ae.safe_ms_samples("5.019"), 240)
        self.assertEqual(ae.safe_ms_samples("5.021"), 241)
        with self.assertRaisesRegex(ValueError, "JSON object"):
            self.run_edit([])


    def test_explicit_supported_fps_is_required(self):
        for fps in (None, "59.94", 59.94, "30000/1001", "60000/1000"):
            with self.subTest(fps=fps):
                manifest = {"keep_recorder_frames": [[0, 20]]}
                if fps is not None:
                    manifest["fps"] = fps
                with self.assertRaisesRegex(ValueError, "fps"):
                    ae.assemble(manifest, self.source, self.folder / "bad-fps.wav")
                self.assertFalse((self.folder / "bad-fps.wav").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
