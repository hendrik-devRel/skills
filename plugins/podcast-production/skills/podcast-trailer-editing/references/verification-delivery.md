# Verification and delivery

## Keep the evidence layers distinct

- **Native sequence:** clip/source bounds, camera nests, grades, track order, microphones, music and enabled states.
- **Editable animation:** fonts, native text and shapes, timing/position controls, complete AEP dependencies.
- **Silent alpha overlay:** output dimensions/rate/duration, actual transparency, no unwanted audio or guide footage.
- **Review MP4:** visible composite and sound with verified timing. A preview rendered in AE from exported Premiere picture is useful, but is not a final native Premiere export.

Check the artifact relevant to each claim. A tool success or file extension alone proves none of these properties.

## Picture and word checks

Probe streams and decode the complete pilot with FFmpeg `-xerror`. Check expected frame count against the rational rate. For a ten-second test at 60000/1001, the worked pilot intentionally used 600 frames / 10.010 s. Other target durations should be resolved explicitly to the frame grid.

Inspect each phrase layout at useful intermediate/complete times. Look for face/hand/insert overlap, broken font substitution, small text readability, clipped letters, opaque rectangles where alpha should exist, duplicate subtitles and old topic labels. Native screenshots or exported frames should show the actual Premiere composition.

Keep declared-box containment and actual face/body clearance as separate verdicts. Check matched picture at word entrances, completed phrases and camera cuts, with denser samples around leaning, gestures and the tightest visible margins. A passing fixed-box alpha report cannot establish that the speaker stayed outside that box. Revise the rectangle and layout if a later pose enters it. Preserve the old render, create a new version, then rerun every-frame alpha containment and all-word entrance/exit checks for that overlay before reviewing the corrected composites. Report sampled picture coverage separately from full-frame numerical coverage.

Sample immediately before, at, and just after representative word onsets. Confirm existing words remain fixed and plate expansion occurs with its word. Confirm phrase clears and intended blank intervals. This establishes that the renderer followed the onset table, not that an ASR estimate matched the spoken phoneme exactly.

For a complete rendered-word audit, compare each frame with the union of the glyphs scheduled by the locked onset/exit table, including the frame before each entrance and both sides of each clear. Keep per-word entrance/hold checks as well as aggregate pixel coverage. Coincident identical glyphs across adjacent cards can hide a duplicate or wrong layer instance in a pixel union; also audit native layer text, in/out frames and transforms.

Lossy ProRes color values can vary slightly on otherwise stationary glyph edges. A single white-pixel cutoff may flag a few pixels crossing the threshold without any movement. Inspect the flagged coordinates and actual intensity differences before changing a test. If compression rounding is confirmed, use a documented narrow intensity hysteresis or tolerance while retaining strict spatial occupancy, native timing and per-word checks. Do not widen safety rectangles, accept unexplained spatial differences, or relax onset checks to make a report pass: tolerance must not hide premature, missing or duplicate words. Preserve the original failing evidence and the diagnosis.

Check alpha numerically when needed: transparent canvas edges, plausible artwork bounds, intended empty frames, and absence of a full opaque guide image. The worked pilot had all 600 frames decoded, only the expected nine-frame empty interval, and artwork below faces. These are evidence for that pilot, not universal alpha thresholds.

Match the output's straight or premultiplied alpha interpretation when making review composites. Premultiplied RGB needs either a premultiplied blend or one unpremultiply before a straight-alpha blend; applying alpha twice darkens edges and can mislead readability review. Confirm the native Premiere result after insertion, since an external composite does not establish its import interpretation.

## Audio checks and measured delay recovery

Compare the preview's decoded audio with the current native PCM. Use several separated dialogue windows, preserve a clear lag sign convention, and report low-energy/ambiguous windows rather than treating them as passing sync. High correlation after a fixed shift can identify export delay; varying lag suggests a different edit, resampling/drift issue or an unreliable comparison.

For long outputs, use the companion Premiere skill's [streaming audio helper](../../premiere-podcast-editing/references/streaming-export-audio.md). It avoids loading full-length PCM into memory and checks both channels, full sequential sample extent and the original-position tail. Original camera AAC alignment against the recorder is a separate clock measurement; it does not authorize shifting the trailer export or word layers.

The worked AE H264 preview was 1024 samples late at 48 kHz across six independent windows, despite identical video timing. The silent overlay was unaffected. Correct only a measured export problem. Do not apply a habitual 21.333 ms shift to future edits.

One tested recovery is to stream-copy the rendered video and encode fresh audio from the exact native pilot WAV. This avoids changing word layers or camera timing to compensate for the export. Use separate input/output files and preserve the original render. A command equivalent to the successful recovery is:

```sh
ffmpeg -i ae-preview.mp4 -i native-pilot.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 256k -ar 48000 \
  -movflags +faststart -shortest corrected-preview.mp4
```

Use existing real paths and quote shell paths safely; helpers should invoke subprocess argument arrays. Confirm the WAV starts at the same pilot zero, covers the complete output, and represents the intended mix. `-shortest` can conceal a truncated source; verify final video packet/frame count and audio coverage before promotion. Recheck lag and correlation across multiple windows. In the worked correction all six windows measured zero-sample lag, correlations 0.99895–0.99995, and full decode passed.

Numerical audio agreement does not replace subjective listening for cut quality, masking, plosives or phrasing. State which checks were actually completed. Preserve existing audio gain/routing when text is the requested change.

## Export while editing continues

For a long native episode export, Adobe Media Encoder can render in the background while editing continues. Verify AME availability, sequence, full range, output destination and chosen delivery settings. Shared CPU/GPU/disk resources can slow previews. A direct Premiere export ties up Premiere; short pilot exports may still be convenient. Queue only when requested or otherwise authorized for the actual deliverable, and distinguish queued, rendering and completed states.

Adobe reference: [Export to Media Encoder](https://helpx.adobe.com/sg/premiere/desktop/render-and-export/export-files/export-directly-to-adobe-media-encoder.html). Use current installed tools and primary Adobe guidance if export behavior differs.

## Packaging and iteration

Save versioned native project/sequence, AEP, alpha, final preview and current word/layout specification. A silent transparent overlay in Premiere with its editable AEP is a valid handoff; Dynamic Link is not required merely to prove editability. Retain the raw preview when making an export-only correction. Source AEPs may reference absolute media paths; include dependencies and check relinking when moving machines. Fonts and Adobe/MCP installations are separate requirements.

Provide one concise handoff index linking each deliverable to its review/export, native project and main sequence/composition, approved audio version, source dependencies, and status or next action. Identify whether dialogue is isolated microphones or shared-mix speaking-turn selections, where word controls live, and which alpha render belongs to which AEP. Link supporting timing/QA records without making the editor reconstruct the entry point from a long production log.

For an editor handoff, test practical revision in a disposable copy: locate a spoken phrase from its visible name/cue context, change a word and its accent, and adjust a title entrance using native controls. Confirm the review composition reflects the change, then discard only the test copy. Check that alternative camera angles remain reachable where supplied. Record any missing control or dependency; the presence of an AEP and many editable layers alone does not establish an easy handoff.

Report the selected pattern, exact sequence name, preview and editable source. Mention unresolved native verification honestly. When feedback changes wording or footage, revise the relevant timing/layout interval, rerender, and repeat affected checks. Do not redo all episode analysis after a small title revision unless source edits changed its assumptions.

This skill's worked example records the real failure cases as well as the successes. Prefer its corrected procedure over replaying failed attempts literally.
