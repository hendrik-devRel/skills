# Assemble an approved trailer with the full episode

Use this when the user accepts a standalone trailer and wants it uploaded for review, then prepended to an editable full-episode timeline. Preserve the accepted standalone artifact; a soundtrack carryover belongs to the new combined assembly.

## Resolve the two source versions

Identify the approved trailer by exact file/version and verify its existing export evidence. Identify the authoritative native full-episode sequence independently: a later saved grade or audio treatment may never have been exported to a new full-length MP4. Importing an older full-episode render would lose those changes and camera editability.

Reuse verified local originals when available. Record the native source project hash, sequence ID, rational frame rate, frame count, dimensions, working color space, angle nests, dialogue routing and media availability. Save the user's current project and create a new assembly sequence. Preserve the standalone full episode and trailer.

## Upload the approved standalone

Use the available `frameio-upload-assets` skill for the exact authorized destination and file set. Confirm the live project/folder, create or reuse the requested isolated subfolder, check duplicate names, upload the approved file, and verify filename, duration/processing state and a working asset URL. Keep upload completion separate from Premiere assembly completion. An internal asset URL is not automatically a public review link.

Do not upload new transition auditions, experiments, source media or a combined export unless they are in the user's requested set.

## Preserve the native edit while making room

Prefer native project/sequence import and duplication over reconstructing an edited episode from an initial XML. Imported dependencies should retain camera-level grades and source handles. Read the available schemas and verify the actual imported sequence and nested angles; an import acknowledgment alone does not prove completion.

A source inspection of one installed Premiere MCP build established these limits:

- `import_sequences` accepts `projectPath` and `sequenceIds`, forwarding them to `app.project.importSequences`. That wrapper can report success without validating the host result.
- `duplicate_sequence` calls the native clone operation; resolve and verify the new sequence before changing it.
- `add_to_timeline(insertMode:"insert")` calls one target track's `insertClip`. It does not explicitly shift all tracks or markers, or configure sync locks. Its reported success only identifies the inserted clip.
- `linkAudio:false` removes automatically placed counterpart audio after placement. It is not protection against audio already overwritten by that placement.
- `move_clip` calls the existing clip object's `move(deltaSeconds)`, avoiding a remove/reinsert that could lose effects. Linked movement and host timing still require readback.

These are inspected adapter behaviors, not a guarantee about another version or a native all-track ripple test. Verify the current tool implementation when it matters.

Before shifting, snapshot every clip's track, ID, start/end, source in/out, enabled state and relevant effects/keyframes; also snapshot track mutes/locks and all markers. Derive the prefix from the approved trailer's exact frame count and rational rate. Make the change only in the duplicate.

For explicit clip movement, work from latest to earliest and target each snapshot's absolute start plus the prefix. Re-read the current position before applying a delta, so a linked counterpart already moved by Premiere is not moved twice. Verify all tracks, including muted reference audio, founder IDs and higher overlays; verify unchanged source bounds, durations, camera grades and clip effects.

When three trailer stem tracks must precede the episode dialogue, add tracks deliberately and inspect their final order before placing media. Track insertion indices can describe placement below an existing track in a particular API; the same numeric index must not be assumed to mean a new track at the top. Rename and re-read the actual track order.

Offset markers and chapters as well. If the available marker tool cannot move a timestamp, snapshot the markers, recreate shifted copies with their names, comments, colors and durations, verify them, then remove only the old markers in the duplicate. That fallback fits ordinary Comment markers. Preserve additional semantics for chapter, web-link or other marker types rather than silently converting them. Rebuild publication chapter labels from exact shifted frames, not already-rounded seconds.

A completed native assembly verified all 315 original clips at their new prefix-offset bounds and 57 Comment markers with unchanged names, comments, types and colors; timestamp differences were within one Premiere tick. The untouched full sequence and three graded angle sequences matched their pre-assembly snapshots. Six muted reference clips changed only an unnamed bypass parameter from time-varying with no keys to static false; its value and the Level keyframes remained unchanged. Treat such serialization changes as a documented exception to inspect, not a reason to ignore broad effect differences. Counts are case evidence, not expected values for another episode.

## Revise an existing assembly

When a later approved trailer has the same duration, duplicate the existing combined sequence and replace the affected prefix assets; preserve the full episode's positions, grades, source bounds and markers. Resolve picture and audio revisions together. In the V09 worked revision, replacing only the picture would have restored a clipped final word because the older assembly still referenced the previous Rahul turn stem. The accepted picture depended on a newer repaired dialogue stem as well as its updated names/end card. Verify the intended stem sum against the accepted mix before changing the assembly.

Inspect replacement adapter behavior and read back the result before retrying. In one installed `replace_clip` wrapper, `preserveEffects:true` duplicated the audio clip's intrinsic Channel Volume component. Replacement with `preserveEffects:false` was appropriate only because these PCM stem clips had verified default intrinsic processing and no custom effects or keyframes to retain. The corrected clips each contained exactly one Volume and one Channel Volume component, with every parameter equal to the original baseline. Do not use that flag blindly on processed clips. The same wrapper reported a Motion Scale restore failure for a picture replacement whose readback already showed the correct unchanged Scale 100; the error did not mean the media replacement had failed.

A video-only stream copy can prevent a replacement movie's embedded AAC from becoming a duplicate track. Verify that it has no audio stream and retains the approved video's packet payloads and timing. Keep the editable graphics project available separately. Compare the new assembly and all original sequences against pre-change snapshots. In the V09 case, all 315 episode clips and 57 markers were unchanged; three original camera clips regenerated only their opaque TrackItem IDs while their media, source bounds, grades and other exposed properties remained exact. Distinguish identity serialization from substantive edit changes.

## Carry music beneath the welcome

Use a bounded, separate stem operation when the approved trailer's final title already fades its music to silence.

1. Inspect the title interval in the actual speech stems. Confirm silence or otherwise protect dialogue; do not infer silence solely from a title image.
2. Locate the original music and unused continuation. A music-plus-residual stem can contain original mix arithmetic; it is not necessarily a pure music source.
3. Decode a short source window at the stem's sample rate and compare several constant-gain windows. Measure stereo timing/phase and gain, with an explicit lag sign convention. Do not assume that different MP3 decoders/resamplers produce identical samples.
4. In the speech-free title interval, blend the accepted residual into the aligned same-source continuation. For correlated music use complementary weights that sum to one, avoiding coherent double-bed gain. Keep the original PCM prefix bit-identical.
5. Duck before the first welcome syllable, then let a short tail fade beneath the opening shot. Derive the level and length from the actual music/dialogue rather than adopting a universal preset.
6. Deliver a continuous assembly-only replacement stem, with exact sample bounds, source offset, gain envelope, and matched before/after auditions. Put the full episode's opening in auditions only; it must not be duplicated inside the music stem.

One verified offline trial used a 1.8-second cosine blend in the last two title seconds, changed the continuation from approximately −15 to −26 dB before the welcome, and faded it out over 1.5 seconds of the episode. Three stereo windows supported a one-sample source lead with correlation above 0.999. Those are measured case values, not defaults. Written PCM, preserved prefix bytes, finite samples/headroom and strict decoding passed; native assembly and subjective listening were separate checks.

For that episode's V09 revision, the user requested a slightly longer overlap. A separate 2.5-second tail retained the previous stem exactly through the join sample and changed only the post-join fade. Its matched auditions both included the accepted final-word repair, isolating the difference in carryover length. This one-second extension is a case-specific choice, not a new general default; judge the welcome's pace and music level independently.

Keep the video frame boundary authoritative. At 30000/1001 fps, 1,737 frames equals 57.9579 seconds; a supplied 48 kHz PCM of 2,781,980 samples lasts 57.9579167 seconds. Record such sub-sample rounding differences instead of shifting correctly timed picture or speech.

## Integrate and hand over

Keep actual microphone ISOs separate where supplied. Speaker-named turn stems from a shared recording do not isolate overlapping people. Use either the accepted full mix or its reconstructing turn/residual stems, never both simultaneously. Replace the assembly music/residual track with the new carryover stem; do not add another copy of the source music underneath.

If the approved trailer picture is imported as a rendered clip, describe its limits honestly and keep its editable source sequence/AEP available. For requested camera-level trailer adjustments, reconstruct or import the verified camera tracks and silent overlays, then compare against the accepted render before claiming editability.

Verify the combined duration, prefix gap, all moved native bounds, markers, enabled audio tracks, alpha interpretation and media availability. Export a bounded transition preview and compare its audio against the prepared PCM. Sample the title-to-wide cut and opening welcome. A long full-episode render is not necessary merely to hand over an editable sequence unless requested.

The inspected Premiere build and its vendor-supplied Frame.io integration used `Sequence.exportAsMediaDirect(outputPath,presetPath,1)` for the sequence in/out range. Set and restore range marks carefully, read them back, and verify duration after export; see [native kinetic workflow](native-kinetic-workflow.md). Do not trust a `clear_sequence_in_out` acknowledgment without readback. One installed wrapper claimed a fallback to start/end but produced an invalid negative in-point and a zero out-point. Recovery used the typed `set_sequence_in_out_points` tool with explicit seconds `inPoint:0` and `outPoint:exactSequenceDurationSeconds`, followed by readback and save. Preserve pre-existing marks when required; setting the whole range is appropriate only for the intended delivery state. Check whether AME is installed before calling a background export tool. If it is absent, a short direct export can be appropriate; do not represent it as a background render.

Match the reference PCM origin to the exported in-point, including its sample-grid readback. In the worked 29.97 fps assembly, preview frames 1617–1887 yielded 270 frames / 9.009 seconds. The 48 kHz in-point rounded to sample 2,589,787; the episode entered at relative sample 192,192 / 4.004 seconds. This differs from an earlier nine-second audition with a different origin and should not be compared without remapping.

Avoid a fractional audio-sample in-point falling just below the intended video frame. At 30000/1001 fps and 48 kHz, a frame spans exactly 8008/5 samples, so frame indices divisible by five align to both grids. For a bounded native preview, choosing frames 1615–1915 gives integer sample endpoints 2,586,584–3,067,064 and an expected 300 frames / 480,480 samples / 10.01 seconds. This is a range-selection technique; still read back the actual marks and verify the exported frame/sample counts and reference origin. Selecting such a range alone is not evidence that native render QA passed.

Eight distributed speech and music windows from that native AAC preview matched the expected stems with correlation 0.9994–0.999998 and fitted gain within 0.053 dB, but all were 1,024 samples late (21.333 ms). The timeline was not moved to compensate for an export issue. When a uniform codec delay is measured, use the matching PCM to replace only the preview audio, then verify again, as described in [verification and delivery](verification-delivery.md). Preserve video payload and document whether the replacement PCM was exported natively or reconstructed from verified unchanged stems. In the completed case, a fresh native PCM16 AIFF exported the same 432,432 samples with zero measured lag against the stem reconstruction and differences within one PCM16 step. Re-encoding only that native PCM to AAC produced zero lag in all eight review windows; all 270 video packet payloads and timestamps were identical to the original export. Strict decoding and headroom checks passed. This is numerical QA, not a claim of continuous human listening. Do not apply a habitual delay correction or claim source alignment from correlations alone.

Save the named native sequence/project and report separately: approved standalone upload, new audio stem, native assembly status, and any export/review checks. Retain episode-specific files and logs outside the reusable skill repository.
