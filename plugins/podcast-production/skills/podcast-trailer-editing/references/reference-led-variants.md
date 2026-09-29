# From opening references to distinct trailer studies

Use this workflow when the user wants several creative alternatives informed by public podcast openings. The number of versions, sampling density and finishing level come from the brief. Five versions should differ in their central idea, excerpt order or pacing; changing fonts and colors on one montage is a style comparison, not five content edits.

## Collect visible reference evidence

Choose a representative episode from each requested show and verify the official website's link to the video. Record title, displayed publication date, page/video URLs, displayed duration, retrieval date and any conflicting date or duration evidence. A website's audio player and its YouTube video can have different intros and chapter clocks.

When the user prefers computer screenshots, sample the public player through the documented browser controls. Video downloads are unnecessary for this mode. Inspect the opening transcript for wording and context; do not infer a highlight montage from a promotional thumbnail or a written summary. Some episodes start directly with the interview.

For requested sampling near four images per video second:

1. Pause and seek through visible player controls. Measure the playback-time advance of a small keyboard-step pilot. Six steps happened to advance about 0.25 seconds in one YouTube session; measure it again for the current player. A keyboard-step increment does not establish the encoded source frame rate.
2. Capture one sample per intended quarter-second position. Read actual playback time and paused state immediately before and after each capture when available. Record filename, requested/observed time, capture time, viewport and player rectangle, and any pending-seek or decode-ready evidence. If seeking has not settled, wait using the supported browser mechanism and recapture the decoded picture.
3. Verify screenshot geometry before a long batch and after a layout or player-mode change. A clipped screenshot call can scroll or reposition the page on some backends. Compare the saved image with the observed player rectangle; check for a sticky header across the picture. A full-viewport capture followed by a documented local crop is a useful fallback. Retain the original screenshot and crop coordinates.
4. Check the time manifest for missing positions, large jumps, unexpected playback, and before/after drift. Describe the actual coverage. Paused quarter-second sampling is not real-time four-fps screen recording, and contact sheets are not inspection of every source frame.

Make an overview plus dense sheets around entrances, cuts and the brand transition. Inspect the sheets and selected full-size images; log which were actually reviewed. Separate authored graphics from YouTube controls, seek popups, captions, chapter labels and player watermarks. A persistent overlay must be identified from visible evidence before attributing it to the editor.

Write observations as timestamp brackets: immediate question versus later-quote preview, phrase holds, reaction cuts, type hierarchy, transitions and where the main interview begins. Keep those findings separate from recommendations for the user's show. Screenshots establish visual behavior; they do not establish music, sound effects or listening quality. Keep public reference captures in the project evidence folder, outside the reusable skill.

## Give each version its own faithful edit map

Use [trailer production](trailer-production.md) for source context and native-clock checks. Select a distinct premise for each version—for example, consequence, concrete operational problem, workflow principle, founder motivation, or customer insight. A quiet direct premise and a produced two-excerpt preview can be useful contrasts without copying another show's branding.

Maintain one rational-fps manifest per version, or a version-keyed manifest, containing:

- Source identity and clock, recorder/source in/out frames, program in/out frames and speaker/camera identity.
- The ordered clips, mapped words, display onsets, title duration and reasons for omissions or reordering.
- Camera sync offset, any source-to-edited-audio keep-map, music choice/gain, and the current input hashes.
- Whether each graphic is a verbatim word reveal, factual context label or editorial heading.

Read the surrounding exchange for every selected section. Preserve material qualifications, question/answer relationships and the referents of pronouns. Do not make one founder's origin story appear to belong to another founder or company. A context label can clarify the subject; a heading must not look like a fabricated quote. Editorial headings can precede a concept, but actual word reveals use the mapped speech onsets.

Round edit boundaries on the target frame grid once. Derive picture, audio and graphics from the same map. A source-edge correction that changes clip duration also changes later program positions: regenerate the affected manifest, audio and native composition before continuing. Word-selection tolerances around cuts do not prove that a phoneme is intact. Clamp each displayed word to its owning clip/card so a boundary word cannot linger into an unrelated shot.

## Editable multi-camera studies in After Effects

If the Premiere bridge is unavailable during already authorized variant work, an editable AE composition can carry the full study. Preserve the Premiere checkpoint and obey any connector stop condition. Use the available `use-after-effects` workflow and current tool catalog; do not bypass a disabled bridge. State that the variants live in the AEP and identify any remaining Premiere integration accurately.

Create uniquely named compositions at the actual canvas, rational frame rate and mapped duration. Keep the three camera angles, or the actual number supplied, as separately identifiable footage layers/precomps; retain individual clip trims and names rather than flattening all picture into one movie. Preserve grades or record any deliberate study-specific picture treatment. Camera source audio should be disabled when separate dialogue/music layers supply the soundtrack, preventing duplicate dialogue.

For an **unretimed footage layer**, source time at a composition time is `comp_time - startTime`. To place source in-point `S` at program in-point `P`, set `startTime = P - S`. **Set `startTime` first, then set the final `inPoint` and `outPoint`.** Changing `startTime` afterward can move the already assigned trim interval. Read back all three properties and verify the expected source frame at both ends. Apply a recorder-to-camera sync offset exactly once when deriving `S`; time-remapped or nested-offset footage needs its own explicit mapping.

When using Time Remap for a held ending, add the desired keys before removing automatic endpoint keys. Removing every key can disable or hide the property. Remove only obsolete keys using their current times/indices, then read back enablement, key times and mapped source values. Inspect the rendered held frame; a successful key operation alone does not prove the intended picture is held.

Reserve space for typography during picture composition. A deliberate side column, band or uniform picture reframing can give each study a different visual structure. Derive its limits from the actual shot and moving bodies; nominal canvas containment alone is insufficient. Use native font measurement and visible glyph bounds, including descenders, strokes and accent padding. Check the longest word before building every card. See [body-clear layout](continuation-body-clear.md) for dynamic clearance and [native kinetic text](native-kinetic-workflow.md) for editable text and shapes.

Identity labels must follow camera/speaker changes, including a short final question. Inspect the first appearance, completed phrases, final word, shot changes and title. Native readback proves placement properties; rendered frames prove the visible result.

## Validate the soundtrack and new source edges

Preserve the current dialogue processing and reaction cleanup. With a shared recording mix, separately named speaker files are speaking-turn selections from that same mix, not isolated microphones. Retain this provenance in filenames/manifests and avoid adding them to a duplicate copy of the dialogue.

Build dialogue and music at the intended sample rate and exact mapped length. Short fixed-clock cosine edge fades can suppress discontinuities without shifting picture, but their duration must suit the actual handles. The successful study used five-millisecond fades; that is not a universal speech-trimming rule. An edge fade does not repair a cut through a word or through the middle of a vocal reaction.

Check each new opening, join and ending against the exact processed-source window and surrounding transcript. Use short local cached ASR where useful, plus waveform/spectrum evidence at active edges. ASR can stretch a word across silence or place its start after a real voiced onset. A high-energy edge may be a wanted phoneme, a prior word's decay or a nonlexical burst; inspect context before moving it. Choose quiet handles around the wanted phrase when the evidence supports them. A reordered clause can need different head and tail boundaries instead of reusing one shared cut.

A listener reporting a clipped word overrides earlier confidence in a transcript boundary: reopen the ending even if ASR, the edit map and zero-lag checks passed. Recover the missing phoneme or consonant decay from the original processed source; freezing or padding the truncated audio cannot restore it. Listen to the original source and revised seam in context when audio audition is available. Fresh ASR and waveform/spectrogram evidence support that review; they do not prove phoneme completeness. Inspect the next word because a blind fixed extension can import the following phrase. Preserve the complete wanted word and place any short de-click fade inside the verified quiet handle. If the requested duration needs more tail, end speech cleanly and hold the picture with music or room tone separately. Recheck the corrected export. If it has not been auditioned, report that speech-ending completeness remains unverified by listening.

Before shifting an internal picture cut for clipped speech, inspect the incoming excerpt’s actual quiet handle; an ASR gap does not establish silence. If the restored tail fits without overlapping wanted speech, an audio L-cut can preserve picture, kinetic text, music and total duration. Recover the original processed source, including any word region attenuated by the old fade, and exclude the following source word. For a known additive mix at matching sample clock and gain, apply the same corrected-minus-original dialogue delta to the original mixed PCM. Update the corresponding speaking-turn file for native replacement, retaining its shared-mix provenance. Verify that the delta is localized, samples outside the repair are unchanged, music remains unchanged within quantization, and no clipping or unwanted speech appears.

Verify exact sample counts, finite samples, headroom, source-window reconstruction with the intended fades, and that speaker-turn files sum to dialogue and dialogue plus music sums to the mix within output quantization. Check exact boundary jumps and unwanted dialogue during the title. These tests establish construction; they do not certify subjective naturalness. Describe listening, ASR and numerical evidence separately. Recheck the changed seams and refresh hashes after a correction; passing an obsolete WAV does not validate its replacement.

After externally replacing an imported audio file, compare its native project duration with the current file before relying on a reload response. A successful reload can leave stale duration metadata. If that occurs, relink a uniquely versioned copy, then read back the imported duration and placed layer trims and verify a rendered audio sample.

## Finish and preserve the reusable work

Render representative native proofs, then the requested full reviews. Follow [verification and delivery](verification-delivery.md) for decode, picture, typography and exported-audio checks. Distinguish checked generated WAVs from later native-rendered/encoded media. Deliver the version names, editable project/compositions, previews, edit maps and the actual QA scope.

For an authorized Git backup of the workflow, update the installed skill and the matching repository files deliberately. Preserve unrelated repository drift. Keep the reusable documentation and helpers general: no private episode media, transcripts, account data, machine-specific project paths or research screenshot dumps. Validate changed skill files, check installed/repository parity and review the scoped diff. Follow the user's stated commit/push timing; uncommitted documentation is not a completed Git backup.
