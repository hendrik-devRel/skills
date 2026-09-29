# Streaming native-export audio verification

Use `scripts/streaming_preview_audio.py` for long H.264 review exports, or when a native export measures a constant audio delay against its matching PCM. It extends the trailer skill's short-pilot approach without decoding a whole episode into memory. Runtime: Python 3.10+ with NumPy and SoundFile, plus FFmpeg and ffprobe on PATH or supplied with `--ffmpeg`/`--ffprobe`. Use a suitable existing or isolated environment.

## Input clock and supported media

Wait for both native exports to finish. The candidate must have one H.264 picture stream and one stereo 48 kHz audio stream. The reference must be one uncompressed PCM audio stream, readable by SoundFile, at native stereo 48 kHz. A 16-bit native WAV is accepted. It must be the exact same native sequence/mix and export range, including clip effects and fades. Raw recorder audio, a differently cut master, or an earlier edit is not a substitute.

The helper requires picture, candidate audio and PCM presentation origins to be zero. It compares exact stream `duration_ts * time_base` with reference sample count at 48 kHz (two-sample duration tolerance). It never resamples the reference, guesses a source-clock offset or changes gain. A mismatch requires correcting the export range/source first.

A native `No Error` receipt and a successful pilot range do not establish full-export completeness. Record intended frame bounds and native in/out readbacks, then independently check actual picture frame count, rational duration, PCM extent and the final intended image. An endpoint adjustment that worked on an integer audio-sample boundary can fail at a fractional boundary. This audio helper cannot recover missing picture: establish a complete native picture candidate before audio replacement, without freezing a frame, padding silence, trimming speech or relaxing the duration tolerance.

```sh
"$EDIT_PYTHON" "$EDIT_SKILL/scripts/streaming_preview_audio.py" verify \
  --preview "$NATIVE_MP4" --reference "$MATCHING_NATIVE_WAV" \
  --window-count 12 --report "$NEW_QA_JSON"
```

Set all path variables explicitly. Use `--window-count 6` for a short representative pilot; 12 is the full-length default. Automatic selection chooses one activity-rich window per equal-duration bin, at most six seconds by default. For a long recording, the first and last windows stay within 30 seconds of the endpoints. Activity scoring locates candidates; it is not semantic speech recognition.

An optional `--windows` JSON array specifies `[start_seconds, end_seconds]` pairs in the native export clock. Supply exactly the selected window count, ordered and nonoverlapping, 0.1–10 seconds each, with its midpoint inside the corresponding duration bin and room for the lag search. Low-energy or ambiguous windows are inconclusive, not passing sync. This strict stereo contract needs measurable reference signal in both channels.

## Checks and replacement

The candidate audio is decoded **once from zero through EOF**, in 65,536-frame chunks with strict decoder-error handling. No input seek or trim can conceal priming or a truncated tail. Only bounded comparison windows, a two-second rolling tail and small 100 ms RMS statistics are retained; the RMS summary grows with duration, rather than storing every sample.

Each channel must correlate at least 0.97 in every selected window, away from the search boundary, at exactly **zero integer-sample lag**. Default search is ±150 ms. Positive lag means candidate audio is delayed relative to native PCM. This is distinct from the original camera-to-recorder clock fit.

Sequential decoded audio must cover every reference sample. AAC can expose 0–1023 extra samples from its final packet; one missing reference sample fails. The last two seconds and final 4096 reference samples are compared at their original sample positions before any padding. Active tails require aligned correlation and gain within 1 dB. A tail below −55 dBFS is reported as quiet and checked by sample extent; this does not prove perceptual similarity of near-silence.

For a proven export-only problem, produce a separate candidate:

```sh
"$EDIT_PYTHON" "$EDIT_SKILL/scripts/streaming_preview_audio.py" replace \
  --preview "$NATIVE_MP4" --reference "$MATCHING_NATIVE_WAV" \
  --window-count 12 --out "$NEW_CORRECTED_MP4" --report "$NEW_QA_JSON"
```

Replacement stream-copies picture and encodes fresh AAC-LC at 320 kb/s from the authoritative PCM. It applies no `-shortest`, `-t`, offset or audio filter. Staged output is created beside the destination, checked with the same timing/tail procedure, and published only on a pass. Compressed video payload SHA-256, exact picture duration/origin and listed picture metadata must match. This proves identical compressed picture payload, not visual quality or every video packet timestamp. Inputs are checked for size/inode/modification-time changes before publication. Existing output/report paths are refused; publication uses a hard link, so the destination filesystem must support it. Failed staging removes temporary media and retains a failure report.

The MP4 muxer receives an exact `-movie_timescale`: the least common multiple of 48,000 and the native video time-base denominator. This gives 240,000 ticks/second for `1/30000` video ticks or 720,000 for `1/90000`. FFmpeg's default 1,000-tick movie clock can round the audio edit duration by more than two samples even when decoded timing and tail coverage pass. Preserve the two-sample duration tolerance and fix the container clock; do not trim samples, shift speech or relax the check to accept millisecond rounding. The helper rejects an exact clock outside the muxer's supported integer range.

If an already completed fresh-AAC candidate fails only that rounding check, an exact-clock stream-copy remux may preserve the encode. Keep it separate until verification passes, compare both compressed audio and video payload hashes before/after, and compare picture with the authoritative native export. Do not treat an unfinished staging file as a completed source or publish from an unverified copy.

## Validation scope

A native 8.008-second pilot measured +1024 samples on both channels across six windows. Fresh AAC from the matching native PCM passed zero lag in all six windows, correlations above 0.99988, tail checks and unchanged compressed picture. Its 384,384 reference samples decoded to 385,024 AAC samples, with 640 final padding samples and unchanged 8.008-second presentation duration. This verifies that measured pilot, not a universal AAC correction or a completed full-length delivery.

The eight tests in `scripts/test_streaming_preview_audio.py` check correlation lag signs, chunk/partial-byte handling, selected capture and tail indices, invalid window placement, missing-tail signal and exact movie clocks. The codec regression generates 241 frames at 30000/1001 fps with a nearest-sample PCM reference: the default millisecond movie clock fails duration QA, while the fixed replacement preserves picture and represents the audio duration exactly with the original two-sample tolerance. This generated fixture requires FFmpeg with libx264 and is skipped when unavailable; the helper itself stream-copies H.264 and does not require an H.264 encoder.

Lossy AAC is not expected to equal PCM sample-for-sample. Distributed timing checks and full sequential sample coverage do not replace listening to dialogue joins, measuring delivered loudness/true peak, checking native lip-sync, or reviewing picture. Record those as separate evidence.
