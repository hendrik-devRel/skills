# Local speech restoration workflow

## Dependencies and scope

Use Python 3.11 or later with NumPy, SciPy, and SoundFile, plus FFmpeg on `PATH`. The helper works locally; it does not upload audio. A task-local virtual environment keeps dependencies separate from the user's global Python:

```sh
python3 -m venv .venv-audio
.venv-audio/bin/python -m pip install numpy scipy soundfile
ffmpeg -hide_banner -h filter=adeclick
```

The supplied helper accepts mono WAV/WAVEX PCM16, PCM24, and 32-bit float audio at sample rates of at least 32 kHz. The original recipe was validated at 48 kHz; the portable helper is also tested at 44.1 kHz. Its fixed 8192-point FFT is not tuned for lower-rate speech, so lower rates are rejected rather than silently resampled. Check its help and input validation before processing another sample rate, subtype, or channel layout. Preserve multichannel relationships when choosing a different tool; do not silently downmix stereo or combine isolated microphones.

The helper preserves the audio sample count, rate, subtype, and gain, but **does not copy non-audio WAV metadata** such as BWF time references, iXML, or cue markers. If the edit relies on those fields, preserve them separately with an appropriate metadata-aware workflow and verify them before replacing production assets.

## CLI examples

Run from a task output/work directory. Point `audio_restore_script` to the installed skill's script. The example times and RMS thresholds below are illustrative; choose them after inspecting the actual input.

```sh
audio_restore_script="/path/to/audio-restoration/scripts/restore_audio.py"
audio_python=".venv-audio/bin/python"

"$audio_python" "$audio_restore_script" analyze "microphone.wav" \
  --report "analysis.json" --quiet-threshold-db -65

# Replace these with verified quiet regions in this source.
"$audio_python" "$audio_restore_script" restore "microphone.wav" "pilot.wav" \
  --noise-region 20:22 --noise-region 80:82 \
  --start-seconds 90 --duration-seconds 20 \
  --declick --declick-threshold 2 --max-reduction-db 8 --noise-scale 1

# pilot.wav starts at source time 90; explicitly align the comparison.
"$audio_python" "$audio_restore_script" preview "microphone.wav" "pilot.wav" "comparison.wav" \
  --cleaned-start-seconds 90 --start-seconds 90 --duration-seconds 12 \
  --gap-seconds 0.75 --gain-db 0

# After a successful pilot, omit start/duration to render the full recording.
"$audio_python" "$audio_restore_script" restore "microphone.wav" "cleaned.wav" \
  --noise-region 20:22 --noise-region 80:82 \
  --declick --declick-threshold 2 --max-reduction-db 8 --noise-scale 1
```

Use the same tested settings in the pilot and full render. The worked recipe below used `--max-reduction-db 12 --noise-scale 8`; test those stronger settings in a pilot before adopting them. Omitting `--declick` performs spectral reduction alone. `--max-reduction-db` defaults to 8 and `--noise-scale` to 1. `--noise-threshold-db` is an alternative to manual `--noise-region` flags: it automatically selects distributed quiet intervals below that RMS ceiling, optionally skipping `--exclude-start-seconds`. Inspect the report's selected intervals before adopting them.

Noise-region times always refer to the full source, including for a pilot. Each region must be at least the larger of 0.5 seconds or three FFT windows. Silent, invalid, overlapping, and out-of-range regions fail clearly. Short output pilots are supported when a sufficient reference exists elsewhere in the source. No suitable noise reference means another selection or restoration method is needed, not an invented profile.

Outputs must have new `.wav` paths. Existing outputs and source overwrites are refused. Restore and preview create JSON sidecars; restore accepts `--report` to choose another report path. Reports retain settings, selected references, source offset, complete decode/peak statistics, lag checks, and the noise profile needed to reproduce the pass. Temporary intermediates are removed after the operation. Numerical QA is not a listening review.

The preview is a float WAV containing original, silence, then cleaned at a single `--gain-db` value. Equal 5 ms fades avoid creating sharp excerpt boundaries; `--fade-ms 0` disables those preview-only fades. Choose that shared gain from the larger peak and leave headroom; an excessive gain is rejected. The command does not normalize the excerpts independently. It writes one pair; repeat with other source offsets or concatenate labeled pairs when multiple examples help. For convenient playback, encode the comparison to MP3 with FFmpeg while retaining the lossless preview.

## Diagnose and choose references

Read the whole file to confirm cloud hydration and decodability. Inspect distributed one-second levels and high-resolution noise spectra. Check suspected click peaks in a short waveform and spectrogram; a high peak-to-RMS ratio is a candidate, not a diagnosis. The waveform alone usually cannot distinguish electrical ticks from mouth or gate artifacts.

Automatic quiet selection is a convenience for analysis. The quietest few seconds per minute may be unrepresentative if the microphone is gated or if the speaker talks continuously. Exclude startup when its floor differs, and reject references with brief voice/transients. A median across many reference spectra is more resistant to contamination than an average over one suspect interval. Do not train the noise profile on a complete spoken excerpt just because its average volume is low.

The algorithm compares local spectral power against a fixed measured noise profile. Strong signal components approach unity gain; components near the noise floor receive more reduction, up to the configured cap. Time/frequency smoothing reduces abrupt gain fluctuations. Noise power scaling is a tuning control: a multiplier of 8 raises the reference by about 9 dB, not 8 dB.

## Validated worked recipe

This recipe was tested on two separate 48 kHz, 24-bit mono podcast microphones, each 131,232,080 samples (45:34.001667). Both had weak drifting mains-like tones and brief broadband spikes. The user listened to the resulting previews and reported no remaining audible interference. That feedback applies to these recordings, not every input.

### Click repair

FFmpeg settings:

```text
adeclick=window=55:overlap=75:arorder=2:threshold=2:burst=1
```

The window is 55 ms, overlap 75%, and AR order 2% of the window. The autoregressive model estimates short damaged portions from surrounding samples. Thresholds 8 and 10 barely reduced the sampled spikes; threshold 2 produced materially better repairs with small measured changes to surrounding speech. Inspect speech before adopting that setting elsewhere.

Prepend and append 0.2 seconds of padding, process, then trim to the exact original sample interval. This addresses startup attenuation observed in short pilots. A floating-point intermediate avoids an unnecessary intermediate PCM24 quantization.

### Spectral reduction

- FFT size 8192; hop 2048; Hann analysis/synthesis windows with matching overlap-add reconstruction.
- Per-track robust median noise power profiles from distributed quiet seconds; startup excluded.
- The original reference selection excluded the first 180 seconds and used RMS ceilings of −67 and −72 dBFS for the respective microphones. Those ceilings depend on recording gain and are not transferable defaults.
- Final noise-profile power multiplier: 8; maximum spectral attenuation: 12 dB. A lighter multiplier 1 / 8 dB cap reduced overall quiet levels by only about 0.6 dB on this material.
- Smoothed power estimate: Gaussian sigma 0.65 frequency bins and 1 temporal frame. Smoothed gain: sigma 0.7 bins and 1 frame.
- Approximately 60-second processing chunks aligned to the hop grid, with 16 hops of context on each side. Discard context from the delivered samples.
- No full-file gain boost, normalization, compression, resampling, or speech synthesis.

### Measured result and limits

| Measurement | Microphone 1 | Microphone 2 |
|---|---:|---:|
| Median quiet-second RMS reduction | 2.85 dB | 2.60 dB |
| Median active-second RMS change | −0.026 dB | −0.015 dB |
| Selected spike high-frequency peak reduction | 5.08–6.99 dB | 8.37–14.95 dB |
| Early/middle/late speech lag | 0 samples | 0 samples |

Quiet seconds were below −70 dBFS and active seconds above −55 dBFS, after the first three minutes. These were energy-based selections. Spike measurements used a 5 kHz high-pass filter and a 20 ms window; they are not full-band perceived loudness or whole-file SNR measurements. All 45 processing seams per track agreed with longer-context renders within one PCM24 quantization step. Full decoding and clipping checks passed.

## Review and delivery

Create comparison pairs from the same source interval. Apply one shared gain to both versions, allow headroom for the larger peak, and add only short preview fades and a gap. Full-length stems keep their original gain. For three pairs, label or document each source offset and the original/cleaned order. Include removed-sound excerpts when useful for checking whether speech is being suppressed.

Report the actual settings, file format/count, measured change, and whether a listening review occurred. If a different noise remains, localize it and change the relevant repair step rather than increasing every control. The saved example contains no source media or private source paths.

De-clicked pilots and full renders can differ slightly even with identical settings because the autoregressive windows start in a different context. A pilot verifies suitability and timing, not bit-identical future output. Review corresponding passages in the full render and run its own numerical checks.

## Maintaining the helper

Run `scripts/test_restore_audio.py` with the same Python environment after modifying the helper. It generates temporary synthetic fixtures, including 44.1 kHz PCM16 and 48 kHz PCM24/float, and checks noise reduction, format/frame preservation, alignment, chunk consistency, short pilots, source/output overwrite protection, matched preview gain/fades, and invalid-input handling. The de-click test requires FFmpeg; inspect skipped-test notices.

The initial portable helper passed all five test groups. An independent use of the skill on a 22-second real speech excerpt preserved all 1,056,000 samples, WAVEX PCM24/48 kHz mono, and zero lag in early/middle/late checks, with unchanged source SHA-256 and no clipping or invalid samples. The review also confirmed that automatically quiet seconds can contain speech or transients: narrowed references were more appropriate. These are bounded behavioral checks, not a listening-quality guarantee for new recordings.

## Shared stereo hiss pilots

When the complaint concerns one speaker but the recorder supplied a shared mix, work from the active production dialogue asset at the native edit's sample offset. Speaker-named partitions do not establish microphone isolation, and muted reference tracks may predate accepted repairs. Inspect the current mix and prior gain/compression before attributing hiss to one person.

For a user-requested experiment, preserve a verified saved-project/active-audio backup and deliver a short matched-gain comparison before replacing episode media. Keep original, light and moderately stronger candidates at identical duration and shared gain, with clearly labeled playback offsets and removed-sound excerpts. A backup project may still depend on camera originals; distinguish it from a self-contained media archive.

The bundled helper is mono-only. For stereo restoration, use an appropriate stereo-capable method; a shared time-frequency attenuation mask can preserve left/right relationships better than independently fluctuating masks. Estimate the profile from inspected noise references, retain real context for STFT processing, and trim exactly. If reducing hiss while protecting voice warmth, frequency-dependent attenuation may be useful; treat cutoffs and caps as trial choices rather than defaults. Reject transcript-defined gaps that still contain voice in the waveform or spectrogram.

Report achieved noise-band and full-band changes separately, using the same original-selected quiet bins, and distinguish both from the algorithm's maximum attenuation. A small overall speech RMS change and zero sample lag do not establish perceptual transparency. A short successful pilot also does not validate a fixed profile across a long recording with changing gain or noise floors. Record the user's listening decision before treating an experimental setting as an accepted recipe.

### Applying an accepted trial across speaking turns

When treatment is requested only for one voice in a shared mix, build explicit sample-domain intervals from reviewed speaking turns and map them through every retained editorial range. Camera shots alone do not establish the active speaker. Preserve other-speaker utterances carved out of a longer turn; use inward treatment ramps at boundaries and report deliberately unprocessed ambiguous reactions. The process still affects overlapping voices inside selected turns.

Check noise references from distributed turns before carrying a pilot profile across a long mix. If their noise spectra and gain are comparable, retaining the accepted profile is safer than automatically increasing reduction; quiet samples can contain breath or room sound. Use one stereo mask and a consistent absolute STFT hop grid for chunked processing, then compare every treatment-intersecting seam with a longer-context render. Verify unchanged samples outside the treatment envelope, exact end tails, both channels, and native export audio. Preserve each existing asset's subtype rather than assuming all dialogue stems share the same bit depth.

For a trailer built from dialogue partitions plus music/residual, treat the intended dialogue partition and reconstruct the sum. Check that the resulting mix difference equals only that partition's difference; denoising the full trailer mix can alter music. When only audio changes, preserve the approved compressed picture where practical and separately verify the encoded audio's timing and true peak. Save a new native project/sequence and keep the prior accepted versions; completion of audio processing does not imply a full-length video export or publication.
