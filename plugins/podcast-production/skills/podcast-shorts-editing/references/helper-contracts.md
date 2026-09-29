# Bundled helper contracts

These scripts operate on local files; none opens or controls Adobe. Give them explicit task paths and new output names. They are portable copies of proven helpers so this skill can be installed independently. When fixing shared helper logic, inspect and reconcile the sibling editing skills rather than leaving divergent copies unnoticed.

## Native segment assembly

`concat_native_segments.py PLAN.json` requires Python 3.10+, FFmpeg and FFprobe. Read [verification and delivery](verification-delivery.md#assemble-exact-native-segments-when-memory-limits-a-long-render) for the JSON schema.

It accepts completed silent H.264/yuv420p native segments, not arbitrary footage to retime. All segments need matching codec metadata, dimensions and rational timing. Their composition ranges must be contiguous from frame zero and exactly cover the plan. Each file begins at zero media time while its native rendering retains the original composition clock.

The helper checks every timestamp and frame count, streams decoded pixels in bounded chunks, concatenates using frame-derived durations, and compares the entire decoded output with the ordered input frames. It does not prove the native segments were rendered from the correct source ranges. Input hashes must remain unchanged. Existing outputs/reports are refused; staged publication uses hard links and therefore needs a destination filesystem that supports them. It caps decoding at two threads and never accumulates a whole video in RAM.

Optional `--ffmpeg` and `--ffprobe` select explicit executables. Output sidecar is `<output>.concat-qa.json`. A failure leaves existing media intact. Review adjacent boundary frames and then verify final muxed audio separately.

## Streaming audio verification or replacement

`streaming_preview_audio.py` requires Python 3.10+, NumPy, SoundFile, FFmpeg and FFprobe. Reuse a verified environment or use a task-local environment; do not assume the default Python has audio dependencies.

Both `verify` and `replace` need a completed candidate with exactly one H.264 video stream and one 48 kHz stereo audio stream. The reference is the exact corresponding 48 kHz stereo PCM WAV with the same edit, fades, gain and zero origin. Neither mode accepts a silent picture-only input. These are strict helper limits, not universal podcast format requirements.

```sh
python3 /absolute/skill/scripts/streaming_preview_audio.py verify \
  --preview /absolute/new-candidate.mp4 \
  --reference /absolute/matching-dialogue.wav \
  --window-count 6 --window-seconds 3 \
  --report /absolute/new-audio-qa.json
```

Six distributed windows were used for this short-form delivery; longer or more complex material can use twelve. Explicit `--windows` accepts the documented output-clock intervals. Automatic activity selection is not semantic speech recognition. Read [streaming export audio](streaming-export-audio.md) for bounds, tail checks, flags and exact supported inputs.

For initial delivery from silent native picture, mux a **new staged candidate** using picture stream copy and fresh AAC from the matching PCM. Derive the movie timescale as `lcm(48000, denominator(video_time_base))`; do not substitute the decimal frame rate or FFmpeg's default millisecond clock. Use explicit video/audio maps and preserve complete streams—no `-shortest`, arbitrary offset, duration trim or gain filter to force a pass. Verify exact picture count/origin/timing, audio alignment and tail, full AV decoding and unchanged compressed picture before promotion.

Use `replace --out NEW.mp4` only when a completed candidate's export audio needs replacement by its authoritative PCM. This stages, verifies and publishes a separate corrected file. It does not fix an incorrect camera offset, bad source selection, a clipped phoneme, or noise in the reference.

The audio helper checks zero integer-sample lag in separated windows, exact stream duration within two audio samples, complete sequential reference coverage, active tail similarity and no reference truncation. Replacement compares compressed video payload and listed metadata. It does **not** strictly decode every picture frame, measure true peak, or certify intelligibility. Run the required separate final AV/frame and listening checks.

The included `test_streaming_preview_audio.py` exercises lag sign, bounded sequential capture/tails, window validation and an exact-clock AAC regression. Run with a Python environment containing NumPy/SoundFile. The codec fixture is a few seconds of generated 64×64 media and does not open Adobe or touch source recordings.

## Read-only macOS resource snapshots

`resource_snapshot.py` uses Python's standard library and macOS system utilities. It samples physical RAM, kernel memory-pressure level, current swap occupancy, compression, disk headroom and process RSS without changing processes, settings or caches.

```sh
python3 /absolute/skill/scripts/resource_snapshot.py \
  --project-path /absolute/project \
  --samples 4 --interval 10 --output /absolute/new-resource-check.json
```

Use bounded foreground sampling and unique output paths. Read [Adobe resource checks](adobe-resource-checks.md) before interpreting fields or coordinating render recovery. A normal snapshot is not a prediction that a later long render will fit.

## What is deliberately not packaged as a universal script

The episode-specific builders selected fixed recording passages, referenced local fonts/media, and generated native batches against one live Adobe project. Copying those paths and IDs into a new project would be unreliable. The [source/audio contract](source-and-audio.md), [portrait architecture](portrait-design.md), reusable layout JSON and [worked case](worked-eight-clip-case.md) preserve the decisions needed to rebuild the plan from new footage. A generated plan is not evidence of native execution.
