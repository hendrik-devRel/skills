# Verification and review delivery

Render native picture to a new silent H.264 file. Mux fresh AAC from the approved PCM
while copying the compressed picture, then verify the actual final output bytes.
Keep native renders, PCM, and a manifest fingerprint so stale outputs can be detected.

Required checks include expected dimensions, rational frame rate, decoded frame count,
exact picture duration and origin, audio duration, finite PCM, clipping/headroom, and
correct channel layout. Check AAC priming and audio alignment against the current PCM
at separated speech windows, including the beginning, middle, and end.
Compare native and delivered compressed picture payloads to confirm picture preservation.
Strictly decode the complete final file and fail delivery on decode or alignment errors.
Inspect final contact sheets, cuts, word endings, and caption timing; audition important
joins where listening is available. State perceptual review limits honestly.

Stage exports and promote them only after checks pass. A file's existence, matching
file size, successful render response, or nominal duration alone does not establish success.

## Assemble exact native segments when memory limits a long render

Follow [Adobe resource checks](adobe-resource-checks.md) before splitting a composition.
Use contiguous half-open composition frame ranges covering the full program. Keep the
original composition/source/animation clock; render each range to a distinct silent file.
Configure render/output settings first and enable exactly one queue item last. Wait for
both rendering and its calling script to finish before purging image caches or dispatching
the next item. A timeout does not mean either has stopped.

The helper `scripts/concat_native_segments.py` accepts an explicit JSON plan:

```json
{
  "fps": [30000, 1001],
  "dimensions": [1080, 1920],
  "total_frames": 600,
  "output": "assembled-picture.mp4",
  "segments": [
    {"path": "part-01.mp4", "start_frame": 0, "frames": 300},
    {"path": "part-02.mp4", "start_frame": 300, "frames": 300}
  ]
}
```

Run `python3 /absolute/skill/path/scripts/concat_native_segments.py /absolute/plan.json`
with FFmpeg and FFprobe available. Relative media paths resolve beside the plan. The helper
requires silent H.264/yuv420p segments with matching codec parameters, exact frame counts,
frame-derived timestamps and zero file origins. It copy-concatenates with rational-derived
durations, then verifies every output timestamp and hashes every decoded YUV frame against
the ordered segment sequence. It streams bounded chunks, caps decoders at two threads,
preserves source hashes and refuses existing output paths. The JSON sidecar records evidence.

This verifies assembly, not whether each segment was rendered from the intended source
clock. Inspect frames on both sides of every segment boundary, including motion and text
continuity. Mux the full approved PCM only after picture checks pass; verify final audio
alignment and endings separately. Do not claim bit-identical video encoding: the check
establishes decoded-picture identity and compressed stream copy during concatenation.

## Patch a small native correction with provenance

When a local picture correction leaves the edit duration and audio unchanged, render an
exact full-frame window from the corrected native composition. Record a patch plan with
the preserved first-pass render, native patch path, new output path, total frame count,
rational frame rate, and zero-based start and frame count. Patch frame zero must correspond
to that exact composition frame; preserve the original source and animation clocks.

Require non-overlapping ranges, matching dimensions and frame rate, zero media origins,
and the expected decoded frame counts. Replace the recorded half-open frame ranges and
verify every output timestamp. If the patch operation re-encodes the complete picture,
disclose that fact: compare every outside frame with the original and every patch frame
with its native reference at documented decoded-pixel tolerances. Inspect the frames
immediately before, within, and after each replacement. PSNR is an alignment/compression
check, not proof of perceptual approval.

Keep input hashes, native project/version, exact ranges, encode settings, verification
results, and the new output hash in a sidecar. Preserve originals and publish the new file
only after checks pass. Then mux the unchanged approved PCM and run the usual final AV
checks. A matching compressed-picture hash at this mux step verifies preservation of the
patched input, not lossless preservation through the earlier patch encode.

## Deliver a playable review set

Provide one review MP4 per clip, matching caption files, editable projects, a source/edit
manifest, and concise verification records. Preserve earlier versions. Generate a local
gallery and handoff index from the same final manifest so names and durations stay consistent.
Give each Short a readable topic/title and one row connecting its format/version, playable
review link, editable project path and exact composition/sequence name, approved audio
file/version, delivery status and editorial priority. Label review files and editable sources
explicitly; an MP4 link alone does not locate the working composition. Include the speaker-color
legend once and mark missing or unverified items honestly.
Use players matching the delivered aspect ratio, with controls, metadata preload, no autoplay, and pause-other-player
behavior. Include posters from the delivered files and encoded relative asset links.
Highlight a few editorial recommendations while retaining the complete set for comparison.
Keep implementation details and shared-mix limitations in an expandable source note.
Regenerate the gallery after timing changes. Open it, check playback and local links,
and confirm the intended videos—not obsolete studies—are actually being shown.


## Verify the editor can continue

Before handing off a completed native project, test a representative Short from the saved
project: locate the final composition through the index, find a spoken phrase by its layer
name, and identify its speaker and approved audio source. In a disposable duplicate, change
a camera within a retained source span and adjust a title or speaker label without rebuilding
the edit. Confirm the alternate angle covers the interval, stays synchronized and keeps camera
audio disabled. Preview the change, then discard the duplicate or restore the saved checkpoint.
Check that the remaining index entries resolve to the intended current projects/compositions.

Record which manual operations were actually verified. Native layers merely existing, a
successful script or a rendered preview does not prove that another editor can make these
changes. If native access is unavailable, deliver the files and explicitly mark this check
unverified rather than claiming an editable handoff was tested.


## Artifact structure and completion evidence

Keep episode-specific artifacts together: raw/context ASR, corrected production words, candidate decisions, an edit manifest, mapped audio/stems, native operation plans, the saved project checkpoint, proofs, native renders, final MP4/SRT files, per-clip QA and a delivery summary. Preserve failed/superseded first passes with their provenance when they explain a repair. Do not put full recordings, private context-library exports or machine-specific paths into a portable skill.

Use individual statuses for planned, rendered, verified and delivered clips. A summary should identify output hashes, exact frames/durations and the reports supporting success. For native patches, keep both the historical authoring checkpoint and any later saved regeneration checkpoint; do not silently replace provenance when the render queue changes.

A practical review page has one correctly proportioned player per clip, a short reason to watch, duration, MP4/SRT links and an editable-source note. Recommend a few contrasting starting clips. Separate draft social copy from direct quotes and keep it unpublished unless posting is requested. Static file/link checks and browser playback checks are different evidence; when browser access is blocked, preserve a usable local link and report the unverified playback rather than working around the block.

## What to check at difficult boundaries

Inspect source/program joins, speaker handoffs, temporary wide inserts, the first/last word of each excerpt and every segment or patch boundary. Sampled opening/middle frames missed an actual wide-panel transparency problem in the worked set. Confirm opaque letterbox backgrounds and the correct camera underneath. Check text contrasts against bright lamps and shelves; an orange backing can preserve readability when white text loses contrast. Avoid duplicate keywords appearing before the word is spoken.

For captions, record uncertain wording rather than treating a successful ASR response as editorial approval. For graphics, native visible bounds and font readback establish geometry, but actual motion/contrast still needs a proof. For audio, include the last two seconds and exact sample tail in addition to separated speech windows. Measuring zero mux lag does not establish lip-sync of the underlying camera offset.

Use [streaming export audio](streaming-export-audio.md) for the bundled verify/replace helper's strict supported formats, exact MP4 movie timescale and limitations. Both helper modes require an existing candidate containing one H.264 video stream and one 48 kHz stereo audio stream. For a silent native render, first mux a separate candidate from the authoritative PCM using an exact movie timescale, then call `verify`; do not pass the silent file directly to `replace`. Strictly decode the final picture as well: the audio helper alone does not verify every video frame. Track loudness/true peak and subjective listening separately when required for delivery.
