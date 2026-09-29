# Kinetic typography for a podcast trailer

For the complete repeatable procedure, scripts and editable example, read the [podcast-trailer-editing skill](../../podcast-trailer-editing/SKILL.md). This page retains the concise integration guidance for podcast edits.

Use this mode for speech-timed words, expressive type hierarchy, and selective emphasis. The CodeRabbit pilot below is a proposed style example, not blanket approval for every episode.

## Reference and timing

Inspect the supplied reference videos across their duration, then sample every frame around representative entrances. A screenshot shows hierarchy but cannot establish animation timing. In the September2026 NVIDIA reference, words appeared directly on speech into a fixed phrase layout; previously visible words stayed still. Orange plates expanded as highlighted words arrived. The supplied Merge trailer primarily supplied pacing and end-card references, with no observed dialogue typography.

Export the current native edit's pilot picture and audio. Existing transcript clocks can become stale after user edits. Obtain word timestamps from this export, quantize to the sequence's rational frame rate, and review uncertain boundaries. ASR may absorb pauses into words. Do not call ASR timestamps an auditory frame-perfect check.

## Visual pilot

The user's specified fonts were Plus Jakarta Sans SemiBold and IBM Plex Mono. Verify actual application font resolution, including variable font weight600; a matching font menu name alone can be ambiguous. IBM Plex Mono may be Adobe-synced under an opaque filename rather than installed in the usual Fonts folder.

Prepare complete phrase layouts before revealing individual words. Preserve each word's final position instead of recentering the text as it builds. Adapt layout to faces, hands and existing inserts. A useful CodeRabbit starting point at UHD is principal words180–258px, secondary words110–164px and mono connectors88–98px. These are starting values, not universal dimensions. Use mostly white, a restrained dark edge/shadow, one orange emphasis per thought, and occasional underlines. The pilot used #FF570A and a five-frame underline draw at59.94fps. Do not add bounce or overshoot without support from the reference or brief.

## Editable construction

When the installed After Effects integration is available, follow its skill and operation catalog. Build native named text and shape layers; layer in-points are sufficient for direct word reveals. Sparse keys can draw underlines. Inspect batch warnings as well as failure counts: a locked guide layer can reject a property change while the batch still reports success.

Provide an editable AEP and a transparent video-only overlay. A native review composition can combine the typography with a current Premiere picture-and-sound export. Keep reference footage as a guide layer in the overlay composition. Confirm the rendered alpha actually excludes picture and audio. A practical delivered format is UHD ProRes4444 at the sequence frame rate. Keep the camera and isolated microphone lines in Premiere below the overlay.

Protect the latest user edit by working in a duplicate. A subsequence from the pilot in/out marks can produce a bounded review sequence with the original camera, audio and insert clips. In Premiere26.5, createSubsequence re-enabled captions that had been hidden in the source duplicate. Inspect the resulting pilot and toggle its original caption display off through the UI if it duplicates the new words. Caption-track visibility/readback was unavailable through the scripting DOM in this case. Also disable only the static graphics that the pilot replaces.

## Verification and handoff

Inspect a native composite at each distinct layout and around word entrances. Check faces/inserts, actual fonts, alpha edges, duration and audio routing. Verify that source text can be changed and rendered; describe whether shapes resize automatically or require manual width edits.

Check exported preview audio against the native WAV numerically. One AE H264 preview in this workflow contained1024samples of delay at48kHz; the silent overlay was unaffected. Replacing only the preview audio with the original native WAV through FFmpeg, while stream-copying video, removed the measured lag. Measure before and after; do not blindly apply a fixed offset to other files. Retain the original export and distinguish container/audio correction from changes to the edit.

Save the AEP, overlay, review MP4, word timing data and concise handoff. If the native bridge becomes unavailable, follow its reconnection/stop instructions and report which native verification remains incomplete. A completed preview is still reviewable; do not claim an unperformed native export.

Worked pilot and evidence: `/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/HANDOFF.md`. These paths, timings and sequence IDs belong only to this episode.
