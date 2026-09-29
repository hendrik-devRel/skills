# Streaming native-export audio verification

Use `scripts/streaming_preview_audio.py` for long H.264 review exports, or when a native export measures a constant audio delay against its matching PCM. It extends the trailer skill's short-pilot approach without decoding a whole episode into memory. Runtime: Python 3.10+ with NumPy and SoundFile, plus FFmpeg and ffprobe on PATH or supplied with `--ffmpeg`/`--ffprobe`. Use a suitable existing or isolated environment.

## Input clock and supported media

Wait for both native exports to finish. The candidate must have one H.264 picture stream and one stereo 48 kHz audio stream. The reference must be one uncompressed PCM audio stream, readable by SoundFile, at native stereo 48 kHz. A 16-bit native WAV is accepted. It must be the exact same native sequence/mix and export range, including clip effects and fades. Raw recorder audio, a differently cut master, or an earlier edit is not a substitute.

The helper requires picture, candidate audio and PCM presentation origins to be zero. It compares exact stream `duration_ts * time_base` with reference sample count at 48 kHz (two-sample duration tolerance). It never resamples the reference, guesses a source-clock offset or changes gain. A mismatch requires correcting the export range/source first.

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

## Measure pilot and full export boundaries independently

In a Premiere 26.5 pilot, `exportAsMediaDirect(..., 1)` targeted the half-open interval `[1920, 2160)` at 30000/1001 fps: 240 frames, 8.008 seconds, and 384,384 samples at 48 kHz. Setting the out point to exactly `2160 * 1001 / 30000` produced **241 picture frames** and **384,385 native PCM samples**. The MP4 and PCM therefore disagreed by much more than the two-sample tolerance; this was an export-boundary problem in addition to AAC delay.

For that measured setup, `setOutPoint(2160 * 1001 / 30000 - 1 / 48000)` gave exactly 240 picture frames and 384,384 native PCM samples. The matching PCM also equaled the expected edited dialogue samples across the intro join. Native AAC separately measured +1024 samples on both channels in all six windows. Fresh AAC from the corrected-range native PCM passed zero lag in all six stereo windows, both tail checks, and identical compressed-picture payload verification.

That adjustment did **not** generalize to the full episode. Applying the same `end - 1/48000` policy to the intended 179,944-frame export produced only 179,943 picture frames, despite Premiere reporting `No Error`. Native PCM had 288,198,309 samples, only 1.4 samples short of the intended picture duration, so its extent passed the original two-sample tolerance. The full endpoint falls between audio samples; the successful pilot ended on an integer sample. This is a measured difference, not evidence for another universal endpoint formula.

Record intended half-open frame bounds, requested seconds and native in/out readbacks. After completion, compare actual picture frame count, exact rational duration, PCM sample extent and final source image independently. Export picture and PCM with the same range, preserve the timeline edit, and restore saved in/out marks. A passing pilot or native success receipt does not establish full-length completeness. See the [complete UHD recovery case](founder-to-founder-uhd-export-case.md) for exact provenance, commands and verification results.

## Recover a proven missing native picture frame

Prefer a corrected native export when the discrepancy is unresolved. A separate short native tail can avoid reencoding a long valid prefix only when all these checks are possible:

1. Establish the intended final frame from the saved native timeline. Export native reference images for that frame and its neighbor, using points inside their intervals. A timestamp rounded fractionally before a frame boundary may export the preceding image.
2. Export the missing image with the same native preset and context beyond the endpoint. Confirm that its independently decodable first IDR is the intended image, not a preceding frame, black padding or a duplicate. A desired B-frame inside an earlier failed tail is not safe to copy in isolation.
3. Compare codec extradata, profile, resolution, frame rate, color metadata and time base. Inspect PTS, DTS and duration, including the original stream's reorder delay. Any timestamp adjustment must be derived for the independent appended packet; do not copy the case's DTS constants blindly or change existing picture timestamps.
4. Copy only the proven native packet into a new candidate. Where identical AVCC extradata permits concat with `-auto_convert 0`, verify that avoiding automatic bitstream conversion actually preserves every original packet's payload hash, PTS, DTS, duration, size and flags. A global picture payload hash alone does not prove timestamp preservation. Check the exact new frame count and duration, decode the seam/tail with strict error handling, and compare the last decoded image with the native tail image.
5. Replace the incomplete/delayed native AAC using the complete matching native PCM, then run the helper's unchanged duration, zero-lag, coverage, tail and picture-copy checks. A picture-complete intermediate that still contains old AAC is not a delivery. If a picture-only intermediate cannot satisfy the helper's input contract, mux its copied picture with fresh AAC from the complete PCM, then run `verify` and independently prove copied-picture identity.

Do not clone/freeze the preceding image, add black, trim audio, invent silence or relax verification to force agreement. If independent frame identity, safe decoding, codec compatibility or unchanged prefix packets cannot be established, use a corrected native export. Preserve failed exports as evidence with a clear do-not-publish note; keep the verified deliverable separate.
