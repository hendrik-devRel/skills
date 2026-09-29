# Reusable multicam podcast editing workflow

## 1. Define the editorial contract

Clarify whether the user wants:

- a full episode cut, a quote reel, or both;
- all conversation preserved or a tightened editorial pass;
- an XML for import, a native Premiere project, rendered media, or a combination;
- color transforms included as instructions, source effects, or baked output.
- recorder stereo mix or separately editable isolated microphones as the audible program; gain/pan adjustments versus a separately approved final loudness/dynamics pass.

Default to two sequences when tightening: `FULL MULTICAM CUT` and `TIGHTENED MULTICAM CUT`. Never silently replace the full sequence.

Store episode-specific values in a configuration: source paths and role identities, source dimensions/rates/durations, master coverage and editorial in/out, per-source sync coefficients and residuals, calibrated microphone thresholds, protected passages, color interpretation, and output names. A full episode can exclude verified pre-roll and post-roll while retaining the entire intended conversation; report those boundary trims separately from internal tightening.

## 2. Inventory the episode

Search recursively for video, audio, camera sidecar XML, recorder metadata, transcripts, and existing NLE projects. Probe each media file for:

- path, codec, container, duration, frame rate, raster, audio channels, sample rate;
- embedded timecode and creation timestamp;
- camera model, gamma, gamut, and picture profile when available.

Identify cloud placeholders before reading multi-gigabyte media. Materialize only files required for the current pass.

Check actual filesystem capacity, not the cloud account quota or Finder's logical size. Use small local audio-analysis caches and review frames; do not duplicate full camera masters to prepare an edit.

Create a source map with stable role names such as:

| Role | Typical source | Editorial use |
|---|---|---|
| Guest close-up | Verified guest camera | Guest speech and reactions |
| Host close-up | Verified host camera | Host questions and reactions |
| Wide two-shot | Verified main/wide camera | Openings, transitions, overlaps, repairs |
| Recorder mix | Verified stereo recorder WAV | Program in recorder-mix mode; disabled reference in ISO-mix mode |
| Guest ISO | Verified guest microphone | Speaker detection; editable program or disabled safety according to mode |
| Host ISO | Verified host microphone | Speaker detection and filler analysis; editable program or disabled safety according to mode |

Confirm the role map from evidence. Folder labels help, but waveform speech activity, thumbnails, and user statements outrank filenames.

Select and record `audio_delivery_mode`: `recorder_mix` enables the stereo mix and disables both ISOs; `iso_mix` enables the separately editable microphones and disables the original mix. Choose from actual audio quality and requested editability, not the Kent precedent. The synchronization clock can remain the original recorder mix in either mode. Keep dialogue centered unless a different pan is intended, measure relative speaker loudness and peak headroom before gain changes, and verify the native routing. Relative balancing is not final loudness normalization; do not silently add compression, limiting or baked derivatives.

## 3. Establish synchronization

Choose a master clock, usually the recorder WAV or wide camera. For every source:

1. Compare embedded timecode when trustworthy.
2. Cross-correlate scratch audio against the master near the beginning.
3. Repeat correlation near the middle and end.
4. Fit a linear source-time mapping when drift is measurable:

   `source_time = source_anchor + drift_ratio × (master_time - master_anchor)`

Do not assume equal file duration proves frame-accurate sync. Small recorder/camera clock differences can accumulate into visible lip-sync error across an hour.

Record offsets and drift coefficients in the project summary or generator configuration.

Use an explicit direction for each mapping, e.g. `source_seconds = intercept + slope * master_seconds`. Record sampled correlation quality and residuals, not just a fit. A pre-existing transcript from a different recorder also needs this mapping. If compensating small drift by resetting source slip at each picture cut instead of a continuous retime, report that and bound the maximum within-shot error; long shots may need a different treatment. Never time-stretch the master audio just to match a camera clock.

## 4. Classify speakers

Downsample isolated microphones to a lightweight analysis format, commonly mono 8–16 kHz PCM. Build short-window loudness envelopes for each ISO and estimate each track's noise floor.

Classify windows as guest, host, overlap, or silence using relative energy and minimum speech duration. Apply hysteresis so camera choices do not chatter between speakers. Room bleed is expected: require the intended microphone to dominate rather than merely contain speech.

Use transcription for semantics and filler timing, not as the only speaker detector. Filter transcript words through the ISO speaker map.

Do not reuse absolute energy or dominance thresholds between recordings. Validate host and guest identity against known question/answer passages. If isolated tracks are silent or inseparable, keep ambiguous spans wide and identify uncertain speaker decisions for review instead of presenting a false diarization.

## 5. Build the full camera cut

Use the active speaker's close-up as the baseline. Introduce the wide angle intentionally:

- opening and re-entry moments;
- question-to-answer transitions;
- overlap, interruption, laughter, or ambiguous speech;
- sustained pauses and physical reactions;
- periodic visual resets during long answers.

Typical pacing:

- close-up hold: at least 2–4 seconds unless turn-taking requires less;
- wide hold: 4–8 seconds for a visual reset;
- periodic wide reset: typically after 45–75 seconds as a starting point; measured episode pacing and explicit user preferences can override this;
- avoid any accidental shot below 1 second.

For a two-person studio conversation, a wide-shot share around 24–30% often feels present without weakening speaker intimacy. Treat that as a diagnostic range, not a mandate. If the user says the wide angle feels absent, measure camera duration instead of relying on clip count; many tiny wide clips can still feel invisible.

## 6. Build a conservative tightened pass

Transcribe the host isolated microphone with word timestamps. Generate candidates for:

- explicit host fillers such as `um` and `uh`;
- awkward internal pauses that do not communicate emphasis;
- abandoned host sentence starts when removal does not change meaning.

Do not remove:

- guest speech;
- meaningful hesitation, comic timing, or emotional beats;
- pauses at topic boundaries that help comprehension;
- words detected only through room bleed.

For every candidate, retain at least several words of context on both sides. Refine boundaries to quiet waveform points or zero crossings. If two proposed repairs are less than about two seconds apart, keep only the stronger one unless a human has reviewed the resulting rhythm.

### Hide each ripple join

1. End the outgoing shot at the last retained pre-removal frame.
2. Remove the same master-time interval from all audio and video tracks.
3. On the first retained post-removal frame, switch to a camera different from the outgoing angle.
4. Prefer the wide angle for most repairs; use a guest reaction periodically for variety.
5. Hold the incoming cover for 2.5–4 seconds.
6. Smooth any pre-join or post-cover beat shorter than the minimum shot duration.

Starting the same cover camera before the removal and continuing it afterward can reveal a visual jump within that camera. Aligning the camera change with the audio join hides the skipped frames.

Add one sequence marker per accepted removal and export a CSV containing source time, sequence time, removed duration, trigger, context, and cover camera.

## 7. Construct Premiere XML

Generate legacy Premiere/FCP XML (`xmeml`) with:

- explicit NTSC/timebase settings matching source cadence;
- sequence raster and audio format;
- stable file IDs and URL-encoded absolute `file://localhost/...` paths;
- one contiguous video track for the assembled camera cut;
- program/ISO enabled states matching the recorded audio delivery mode;
- original mix and isolated microphones retained as editable sources, with inaudible references disabled;
- source in/out values computed from the synchronization mapping;
- source color notes in clip labels or metadata;
- removal markers on the tightened sequence.

Round consistently to timeline frames. Make each clip's timeline duration equal its source out minus source in after rounding.

This frame-equality rule and the packaged generator assume equal, constant source/sequence cadence. Require explicitly probed source frame rates. If cameras differ in rate or are variable-frame-rate, stop this helper path and establish a verified conform/retime workflow; do not relabel source cadence. Editable audio level effects use linear gain, not dB values. Check the serialized values with the config-aware validator and then confirm their interpretation in Premiere; a valid XML does not prove a native effect imported correctly.

Use integer frame counts and raw seconds as the source of truth. Display timecodes must identify nominal rate and drop/non-drop convention; do not approximate seconds by rounded frames-per-minute. Preserve each source raster rather than reporting every camera at sequence size. In a 4K sequence, a 1080p host angle needs explicit 200% scaling and an upscaling note; verify the imported image fills the frame.

## 8. Color handling

Inspect camera metadata and sidecars rather than judging only from the washed-out appearance.

- Apply the correct input transform to log footage at source/master-clip level so every edit inherits it.
- For Sony S-Log3/S-Gamut3.Cine, use a matching technical transform such as Sony LC-709 Type A when appropriate.
- Do not apply that transform to S-Cinetone, Rec.709, or recorder-switched footage.
- After normalization, match exposure, white balance, contrast, and skin tone across angles.
- Keep creative look adjustments separate from technical input transforms.

## 9. Validate and hand off

Run XML parsing plus structural validation. Check:

- sequence and track duration;
- frame-contiguous clips with no gaps or overlaps;
- positive source ranges whose duration matches the timeline duration;
- source files exist and paths are URL-decoded correctly;
- marker count equals final removal count;
- camera shares match the report;
- minimum shot duration is respected.

Also check source out never exceeds actual media duration, audio enabled states and gain/pan match the selected delivery mode, every sequence is validated (not just the first), and the latest native project corresponds to the final XML. Premiere imports can expose a nested wrapper as well as the real assembled sequence: inspect clip counts and track structure before reporting success. A resolvable filename does not prove hydrated/playable media. Validate new files with a media probe and targeted decoding.

Create a concise README explaining import, relink, audio track state, color transforms, and which sequence is preserved. Keep all lightweight project artifacts in the user's cloud-synced episode folder when remote access is expected.

For native Premiere delivery, save a new project, reopen or read back its sequence state, and verify picture and audio at representative early/middle/late points. Do not claim a LUT was applied based only on a clip label or XML comment: verify the actual source/master effect or color-management setting. Preserve unrelated open projects and unsaved edits.
