#!/usr/bin/env python3
"""Small CLI regression suite; generated audio and outputs live in a temporary folder.

Run with the same Python environment as restore_audio.py. The de-click test skips
when FFmpeg is absent. These checks establish numerical behavior, not listening quality.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import soundfile as sf

SCRIPT = Path(__file__).with_name("restore_audio.py")


class RestoreAudioTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="audio-restoration-test-")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)

    def fixture(self, sr=48000, subtype="PCM_24", name="source.wav"):
        t = np.arange(sr*6)/sr
        rng = np.random.default_rng(41)
        noise = 0.002*rng.normal(size=len(t))+0.002*np.sin(2*np.pi*60*t)
        speech = (0.11*np.sin(2*np.pi*173*t)+0.06*np.sin(2*np.pi*346*t))
        speech *= ((t >= 2)&(t < 5)) * (0.7+0.3*np.sin(2*np.pi*2*t))
        samples = noise+speech
        samples[round(3.3*sr)] += 0.35
        path = self.folder/name
        sf.write(path, samples, sr, subtype=subtype)
        return path

    def command(self, *args, succeeds=True):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                capture_output=True, text=True)
        if succeeds:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("Traceback", result.stderr)
        return result

    def restored(self, source, name="restored.wav", *options):
        output = self.folder/name
        self.command("restore", source, output, "--noise-region", "0:1", "--noise-region", "1:2", *options)
        return output

    def test_formats_noise_timing_and_source_unchanged(self):
        for sr, subtype in [(48000, "PCM_24"), (44100, "PCM_16"), (48000, "FLOAT")]:
            with self.subTest(sr=sr, subtype=subtype):
                source = self.fixture(sr, subtype, f"source-{sr}-{subtype}.wav")
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
                output = self.restored(source, f"restored-{sr}-{subtype}.wav")
                before, after = sf.info(source), sf.info(output)
                self.assertEqual((before.frames, before.samplerate, before.subtype),
                                 (after.frames, after.samplerate, after.subtype))
                x, _ = sf.read(source)
                y, _ = sf.read(output)
                self.assertTrue(np.isfinite(y).all())
                self.assertLess(np.linalg.norm(y[sr//2:sr]), np.linalg.norm(x[sr//2:sr])*0.85)
                speech_change = 20*np.log10(np.linalg.norm(y[2*sr:3*sr])/np.linalg.norm(x[2*sr:3*sr]))
                self.assertLess(abs(speech_change), 0.5)
                report = json.loads(Path(str(output)+".json").read_text())
                self.assertTrue(report["qa"]["lag_checks"])
                self.assertTrue(all(q["lag_samples"] == 0 for q in report["qa"]["lag_checks"]))
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), digest)

    def test_analyze_auto_references_and_preview_gain(self):
        source = self.fixture()
        analysis = self.folder/"analysis.json"
        self.command("analyze", source, "--report", analysis, "--quiet-threshold-db", "-45")
        report = json.loads(analysis.read_text())
        self.assertEqual(len(report["windows"]), 6)
        self.assertGreater(report["quiet_candidate_count"], 0)
        self.assertTrue(report["prominent_noise_lines"])
        output = self.folder/"auto.wav"
        self.command("restore", source, output, "--noise-threshold-db", "-45", "--exclude-start-seconds", "1")
        metadata = json.loads(Path(str(output)+".json").read_text())
        self.assertTrue(all(pair[0] >= 1 for pair in metadata["noise_reference_regions_seconds"]))
        preview = self.folder/"preview.wav"
        self.command("preview", source, output, preview, "--start-seconds", "2", "--duration-seconds", "1",
                     "--gap-seconds", "0.25", "--gain-db", "-6", "--fade-ms", "0")
        x, sr = sf.read(source)
        y, _ = sf.read(output)
        joined, rate = sf.read(preview)
        gain = 10**(-6/20)
        self.assertEqual(rate, sr)
        self.assertEqual(len(joined), round(sr*2.25))
        np.testing.assert_allclose(joined[:sr], x[2*sr:3*sr]*gain, atol=1e-8, rtol=1e-6)
        np.testing.assert_array_equal(joined[sr:round(sr*1.25)], 0)
        np.testing.assert_allclose(joined[round(sr*1.25):], y[2*sr:3*sr]*gain, atol=1e-8, rtol=1e-6)
        faded_preview = self.folder/"faded-preview.wav"
        self.command("preview", source, output, faded_preview, "--start-seconds", "2", "--duration-seconds", "1",
                     "--gap-seconds", "0.25", "--gain-db", "-6")
        faded, _ = sf.read(faded_preview)
        envelope = np.ones(sr)
        fade_samples = round(0.005*sr)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = envelope[:fade_samples][::-1]
        np.testing.assert_allclose(faded[:sr], x[2*sr:3*sr]*gain*envelope, atol=1e-8, rtol=1e-6)
        np.testing.assert_allclose(faded[round(sr*1.25):], y[2*sr:3*sr]*gain*envelope, atol=1e-8, rtol=1e-6)
        self.assertEqual(json.loads(Path(str(faded_preview)+".json").read_text())["fade_samples"], fade_samples)

    def test_chunk_grid_and_short_pilot(self):
        source = self.fixture()
        long_chunks = self.restored(source, "large.wav")
        short_chunks = self.restored(source, "small.wav", "--chunk-seconds", "0.75")
        a, sr = sf.read(long_chunks)
        b, _ = sf.read(short_chunks)
        np.testing.assert_allclose(a, b, atol=2e-6, rtol=0)
        pilot = self.restored(source, "pilot.wav", "--start-seconds", "2.137", "--duration-seconds", "0.01")
        excerpt, _ = sf.read(pilot)
        first = round(2.137*sr)
        self.assertEqual(len(excerpt), round(0.01*sr))
        np.testing.assert_allclose(excerpt, a[first:first+len(excerpt)], atol=2e-6, rtol=0)
        self.command("preview", source, pilot, self.folder/"pilot-preview.wav", "--cleaned-start-seconds", "2.137",
                     "--start-seconds", "2.137", "--duration-seconds", "0.01")

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is absent")
    def test_declick_keeps_frame_count_and_lag(self):
        source = self.fixture()
        output = self.restored(source, "declicked.wav", "--declick")
        report = json.loads(Path(str(output)+".json").read_text())
        self.assertEqual(sf.info(source).frames, sf.info(output).frames)
        self.assertTrue(all(q["lag_samples"] == 0 for q in report["qa"]["lag_checks"]))
        x, sr = sf.read(source)
        y, _ = sf.read(output)
        frame = round(3.3*sr)
        self.assertLess(abs(y[frame]), abs(x[frame])*0.75)
        self.assertFalse(list(self.folder.glob(".audio-restoration-*")))

    def test_refusals_do_not_overwrite_or_publish_partial_files(self):
        source = self.fixture()
        output = self.restored(source)
        original = output.read_bytes()
        self.command("restore", source, output, "--noise-region", "0:1", succeeds=False)
        self.assertEqual(output.read_bytes(), original)
        self.command("restore", source, source, "--noise-region", "0:1", succeeds=False)
        invalid_options = [("--noise-region", "0:0.1"), ("--noise-region", "8:9"),
                           ("--noise-region", "nan:1"), ("--noise-threshold-db", "-300"),
                           ("--noise-region", "0:1", "--max-reduction-db", "nan"),
                           ("--noise-region", "0:1", "--start-seconds", "100"),
                           ("--noise-region", "0:1", "--noise-scale", "-1")]
        for index, options in enumerate(invalid_options):
            target = self.folder/f"invalid-{index}.wav"
            self.command("restore", source, target, *options, succeeds=False)
            self.assertFalse(target.exists())
            self.assertFalse(Path(str(target)+".json").exists())
        short = self.folder/"short.wav"
        sf.write(short, np.zeros(100), 48000, subtype="PCM_24")
        self.command("restore", short, self.folder/"short-output.wav", "--noise-threshold-db", "-20", succeeds=False)
        stereo = self.folder/"stereo.wav"
        sf.write(stereo, np.zeros((48000, 2)), 48000, subtype="PCM_24")
        self.command("analyze", stereo, succeeds=False)
        nonfinite = self.folder/"nonfinite.wav"
        sf.write(nonfinite, np.array([0.0, np.nan, 0.0]), 48000, subtype="FLOAT")
        self.command("analyze", nonfinite, succeeds=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
