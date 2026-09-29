# Synchronization and podcast audio

Use this reference for independently recorded cameras, isolated microphones, speaker-led cuts, processed audio, and native-export audio QA. The methods below were exercised on a long two-person multicamera recording. Numerical settings are starting points from that test, not requirements for other voices, rooms, or delivery specifications.

## Establish the recorder clock

- Probe every source for exact duration, sample rate, channel layout, rational frame rate, starting timestamps, and embedded audio. Confirm microphone-to-person and camera-to-angle mappings from content; filenames, track numbers, folder dates, and camera timecodes are not sufficient evidence.
- Select one continuous recorder timeline as the reference. Check isolated microphone lengths and start alignment before summing them. Preserve originals; extract inexpensive analysis copies, such as 8 kHz mono PCM for alignment and 16 kHz mono for local transcription.
- Downsampled peaks and zeros describe the analysis copy. Check clipping, discontinuities, and exact sample counts on native-rate sources before reporting recording defects. Shared silence is a candidate for review, not proof of a dropout.

## Fit offset and clock drift

Define the convention in the manifest, in seconds:

```text
recorder_time = a * source_time + b
source_time   = (recorder_time - b) / a
drift_over_source = (a - 1) * source_duration
speed_percent_for_continuous_retime = 100 / a
recorder_coverage = [b, a * source_duration + b]
```

Positive `b` means source recording begins later on the recorder clock. Keep coefficients at full precision; rounded display values must not become edit inputs.

1. Find a coarse offset using speech-energy envelopes. A tested approach used 20 ms RMS blocks, log energy, subtraction of a roughly five-second moving baseline to reduce AGC differences, and FFT cross-correlation over a plausible search range.
2. Refine with normalized waveform correlation on dispersed 10–20 second speech windows. Search around the coarse prediction, subtract means, normalize by window energy, and retain correlation sign and magnitude. A polarity reversal can produce the correct negative correlation peak.
3. Compare the microphone sum and individual microphones. Crosstalk, propagation, room reflections, or phase cancellation can make the strongest peak misleading. Retain all candidates and reject search-edge peaks; do not silently force them into a fit.
4. Fit `offset = (a - 1) * source_time + b` robustly from windows spanning most of the recording. In the tested case, candidate pairs separated by at least 20 minutes, correlation above about 0.2, and a 4 ms consensus residual worked. Adapt those thresholds to signal quality and duration; fail clearly if there are too few independent anchors.
5. Test unused windows near the beginning, middle, and end. Record residuals against the frozen fit, including ambiguous or rejected windows. When one channel produces an echo peak, inspect other channels and an additional end window before changing the model. Nonlinear or discontinuous residuals may require separate sections rather than one affine fit.

Keep the fit anchors, rejected matches, holdout measurements, coverage intersection, and uncertainty in a machine-readable report. Small waveform residuals establish audio alignment; they do not independently establish camera sensor-to-audio latency or lip sync. Check visible speech or a clap where available.

## Quantize and apply synchronization

- Use rational rates, such as `60000/1001`, and half-open frame intervals `[in, out)`. Convert recorder boundaries to sequence frames once; derive continuous timeline starts from cumulative kept frame lengths to avoid gaps and overlaps.
- For each camera source in, invert the affine mapping from the snapped recorder boundary, then round to that source's frame grid. Validate every source in/out against available media and the selected camera's recorder coverage.
- Either retime a continuous camera by `100/a`, or reset its source in at each editorial cut and play that short shot at normal speed. The latter was adequate in the tested recording; it is not a substitute for measuring drift on long shots.
- Without retime, the additional drift over a shot of timeline duration `L` is `(a - 1) * L`. Evaluate actual affine error at both ends after frame rounding, including source-frame quantization and fit uncertainty, rather than reporting only the regression residual.
- Apply minimum shot holds in the same frame domain as the edit. At 59.94 fps, separately rounded boundaries for a nominal five-second turn can yield 299 frames. A later `ceil(5 * fps) = 300` cleanup must not swallow that genuine reply. Allow the rounding tolerance or review the short turn before merging it.
- Keep recorder time, camera-source time, and edited-program time distinct in transcripts, markers, and reports. For each kept span, store its recorder in/out and cumulative program start; subtract removed intervals exactly once.

## Infer turns conservatively

Use microphone differences as evidence of speaker activity, not a substitute for editorial judgment. First inspect speech/noise distributions and gain imbalance on representative solo speech from each person.

- A tested analysis used 100 ms RMS blocks with 300 ms smoothing **in power space**, then converted to dB. Require both sufficient absolute energy and plausible relative level to reject distant microphone bleed. Fixed thresholds from a quiet recording will fail on louder preamps or uneven microphone placement.
- Separate activity labeling from camera decisions. Activity may include overlap, room sound, and short events; camera decisions should preserve a shot through pauses and backchannels.
- Useful initial hysteresis: fill activity gaps up to 400 ms, ignore isolated events shorter than 300 ms, require about two seconds of supported opposing dominance above an approximately 8 dB margin, and hold shots around five seconds. Cut slightly into the sustained turn if it looks natural. Tune on actual examples of both speakers and overlap.
- Do not switch for every “yeah,” breath, laugh, or acknowledgment. Do not delete short replies merely because they violate a preferred hold. Review camera assignment after quantization, particularly at program starts, removed gaps, and resumed speech.
- Reserve wide shots or reaction shots for editorial reasons. A microphone-energy label cannot establish eye contact, gesture quality, whether someone is demonstrating a screen, or whether a listener reaction deserves coverage.

## Find content boundaries with transcription and listening

Start with the opening, closing, and suspicious long gaps. Use an installed local transcription model when available and appropriate; inspect cached models before downloading anything. No cloud transcription is implied by an editing request.

Transcribe focused windows with word timestamps, adding each extraction's recorder offset back to every timestamp. A rough full transcript helps locate chapters, explicit “edit this out” remarks, setup, and screen references; proper names and exact boundaries still need review.

Retain lead-in breaths and word tails. Distinguish formal opening/signoff from useful pre-roll conversation, setup, demo loading, and outtakes. Keep uncertain material or mark it for review when the task is a conservative first edit. Spoken references to a graph or game do not prove a corresponding screen recording exists; inventory those assets and mark missing inserts.

## Process aligned stems without moving speech

If the usable source is a shared mix, use [shared-mix dialogue](shared-mix-dialogue.md) instead of inventing independent stems. Turn-based gain may balance people, but cannot isolate overlapping voices.

Keep full-length processed stems aligned to the chosen recorder clock so raw and processed versions share source ins. Derive exact target sample count `N` from the reference audio; if rates differ, resample and establish the common clock explicitly. Use integer sample counts rather than rounded decimal duration.

A useful tested starting chain was:

- Two-pole high-pass around 75 Hz; choose cutoff from the voice and rumble rather than applying it blindly.
- Per-person pre-gain determined from measurements, followed by gentle RMS compression: roughly 2.5:1, threshold around −22 dBFS after pre-gain, 10 ms attack, 180 ms release, soft knee. Makeup gain depends on the actual result.
- Optional crosstalk attenuation only with credible opposing speech and absent local speech. The tested case capped attenuation at 12 dB, required the other microphone to be over 20 dB louder for at least 0.8 seconds, protected local speech for 400 ms before and 700 ms after, and smoothed gain changes over about 300 ms.
- Preserve breaths and overlap; use no hard gate by default. If relative microphone evidence is weak, omit the automatic attenuation. Listen for pumping, clipped consonants, and disappearing quiet replies before accepting it.
- Compensated limiting as needed, with explicit final padding/trimming and timestamps reset to the sample clock. For FFmpeg, a final `apad,atrim=end_sample=N,asetpts=N/SR/TB` can enforce length, but cannot repair an uncorrected delay earlier in the chain.

Use 48 kHz/24-bit PCM deliverables when that matches the editing project. Keep processed mono stems editable and preserve raw sources. Follow the user's routing preference: an audible stereo master with muted optional stems is one arrangement; separate audible microphones with a shared output limiter is another. For speech-only microphone routing, use [separate microphones](separate-microphones.md). Verify that a combined master is not playing alongside the separate stems.

For centered speech, a dual-mono stereo master is valid; do not place different speakers at opposite ears unless requested. Use explicit summing gain rather than accepting an automatic mixer normalization setting. A stereo target around −16 LUFS and a true-peak ceiling no higher than −1 dBTP can be useful delivery starting points; apply the user's specification and measure the final kept program. Mono and dual-mono stereo loudness readings are not interchangeable.

Oversampling before limiting can reduce intersample overshoot. The tested chain used 192 kHz limiting with a −1.5 dBFS ceiling, then returned to 48 kHz and measured true peak. A limiter setting alone does not prove final true peak; lossy export can change it. Iterate only when measurements or listening justify adjustment.

## Prove timing and audio quality separately

1. Probe every output's rate, channels, bit depth, duration time base, and exact sample count. Convert `duration_ts * time_base * sample_rate` when the time base is not one sample. Equal duration is necessary but does not prove alignment.
2. Correlate multiple speech windows distributed across each raw/processed pair. Use a coarse lag search if necessary, then sample-level refinement; avoid silence and exclude filter startup transients.
3. Make the reference phase-aware. A minimum-phase high-pass can move the correlation maximum by a few samples without a timeline delay. Apply the same high-pass to the raw reference before interpreting lag. Report correlation, zero-lag correlation, and best lag; also compare summed processed stems to the final master.
4. Measure integrated loudness, loudness range, sample/true peak, and clipping on the delivered program or exact preview interval. Do not compare a two-minute export with whole-episode loudness. Record exact filters, gains, channel layout, and measurement range.
5. Listen to representative solo speech from each person, overlap, soft replies, transitions, and loud passages. If playback was not actually performed, report statistical QA honestly and provide listening excerpts. Neither a transcript nor a correlation score demonstrates pleasant sound.
6. Export a short native Premiere review and decode it. Compare each channel against the mastered source using the **snapped manifest source in**, not an earlier unsnapped editorial timestamp. Check lag, gain, correlation, duration, loudness, and true peak. Identical dual-mono channels cannot reveal a left/right swap, so inspect routing structurally too.
7. Check audio around picture-cut boundaries and actual content joins. Quiet source edges and a tiny sample jump support a clean join but do not replace hearing the rendered join. Use a short fade/crossfade when appropriate, preserving words and the intended gap length.

## Conditional AAC export-delay diagnosis

For long exports, [the streaming helper](streaming-export-audio.md) provides bounded-memory, both-channel timing and complete audio/tail checks against the matching native PCM. It can encode a separate AAC replacement while copying picture. Distinguish original camera-to-recorder clock measurements from this native-export comparison; equal 1024-sample values do not establish the same direction or cause.

One tested native MP4 export decoded 1,024 samples late at 48 kHz (21.333 ms), although its PCM timeline was aligned. The audio edit list started at media time zero and did not discard encoder priming. This was an export-container defect in that file, not a universal Premiere or AAC rule.

- First measure the lag against the correct PCM excerpt. Inspect audio/video start times, packet PTS/DTS, `initial_padding`/skip-sample side data, and the audio track's MP4 `edts/elst` entries and media time scale. A value of 1,024 alone is not sufficient proof.
- If the source or timeline is wrong, correct that cause. If only the encoded container is proven wrong, keep the native project and PCM timing intact. Test a metadata correction on a separate copy while retaining the original export.
- A lossless edit-list adjustment can skip proven priming without recompressing. Parse track identity, atom sizes, edit-list version, signed media-time fields, and media/movie time scales. Do not reuse a byte offset, assume a four-byte field, or blindly add 1,024 to every file. Preserve intentional leading edits and duration semantics.
- Validate decoded correlation returns to the intended delay, both-channel gain remains correct, end coverage and duration remain valid, and full audio/video decode succeeds. Verify all compressed audio/video packet payload hashes and all video PTS/DTS/durations against the original.
- Compare **stored** packets with edit-list processing disabled where needed (FFprobe `-ignore_editlist 1`). Presentation packet counts can differ because a corrected edit exposes an already encoded tail packet; stored payload equality proves no re-encoding. Audio presentation timestamps are expected to change; video timestamps are not.
- Replace the canonical review only after the candidate passes, preserving the original and coordinating any active readers. Document the correction as export-only. If the container structure or evidence is ambiguous, keep the original, report the measured issue, and use a supported export/remux path instead of an unverified binary patch.

The handoff should distinguish measured sync and signal checks, actual listening/visual review, transcript-assisted editorial decisions, and remaining limitations. A validated preview does not establish that the entire episode was rendered or watched.
