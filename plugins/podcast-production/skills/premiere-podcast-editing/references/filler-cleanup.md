# Conservative filler cleanup in an existing native edit

Use this workflow when the user requests removal of spoken hesitation sounds from an already edited podcast. Preserve the previous sequence and project checkpoint. Keep existing camera selection, grading, framing, and microphone processing unless the brief also requests changes to them.

Requests such as “cut out the ems,” “remove the ums/erms/uhs,” and, in this context, “cut out the M's” refer to hesitation sounds. Identify them from speech context; do not delete literal letters or /m/ consonants from normal words.

## Establish scope and preserve the native edit

1. Save a checkpoint and snapshot the original sequence: identity, settings, duration, video/audio clip IDs, source project items, all four timing bounds, enabled state, routing, and effects.
2. Duplicate the original sequence in full as an internal editing source. This preserves its camera cuts, nested grades, and Motion scaling while allowing source-monitor marks to change without touching the original.
3. Create a separate empty duplicate for the new edit, retaining the original sequence settings. Verify that it is empty; a successful clone response does not establish that clearing succeeded.
4. Keep recorder time, original sequence time, and shortened sequence time distinct. Derive the original audio source-in from native readback, including its frame quantization; do not reuse an earlier rounded editorial timestamp.

An internal source nest preserves the existing picture exactly. Its source clock is the original edited sequence, not necessarily continuous recorder time. If the original has prior content removals, use its retained-range mapping to locate the corresponding audio.

## Find candidates without deleting meaningful speech

- Use existing local transcripts with word timestamps to locate `um`, `erm`, and `uh`. Focused transcription and a second model can improve context review; they do not make word boundaries exact.
- Preserve acknowledgments such as `mm-hmm`, `yeah`, `wow`, and meaningful hesitations or reactions. Protect neighboring articles, conjunctions, model names, word tails, and initial /m/ sounds; an /m/ consonant can resemble an isolated filler in a waveform.
- Do not expand the task into deleting repetitions, `like`, `you know`, or substantive phrases unless requested.
- Inspect the original isolated microphone and mastered audio around each candidate. ASR timestamps may include leading silence, stop inside a vocalization, or omit a filler entirely. A nearest low-energy valley can occur before the actual filler rather than after it.
- Distinguish the full isolated hesitation event from surrounding words. Allow clean handles and natural breath space. Retain candidates with overlapping speech, uncertain identity, or no safe boundary.
- Store candidate ID, original-clock bounds, context, evidence, proposed frame cuts, handle limits, and the decision/reason. The candidate list is analysis; only the reviewed executable interval list drives edits.

ASR agreement, waveform inspection, and measured silence are not listening. Report which forms of review actually occurred.

## Freeze one timing map for picture and audio

1. Express final removals as ordered, non-overlapping half-open frame intervals `[start, end)` at the exact rational sequence rate.
2. Compute complementary keep intervals once. Derive shortened timeline positions from cumulative kept frame counts; do not independently round a succession of decimal offsets.
3. Store every retained span's original-sequence in/out and shortened-sequence start/end, plus its original audio source mapping.
4. Convert cumulative output boundaries to sample positions, then derive each output segment length from neighboring sample positions. At fractional frame rates, samples per frame need not be an integer; rounding each segment independently can accumulate error.
5. Verify the final PCM sample count against the intended picture duration under the declared frame-to-sample rounding rule. Never trim or pad an unexplained sync error merely to match duration.

For continuous recorder-based audio, its source time equals the snapped original audio source-in plus original-sequence time. For an already edited original, apply the original sequence's own source map first.

## Blend the audio without changing the output clock

Use [the bundled audio helper](../scripts/assemble_filler_audio.py) when [its input contract](filler-audio-config.md) matches the frozen keep map. Preserve the calibrated master gain and retain separate processed stems if adjustment is useful.

- Render a new PCM file; leave original and previously delivered audio unchanged.
- Use short equal-gain blends supported by clean source handles. Approximately 20 ms quiet handles worked in one recording; choose lengths from the actual speech, noise, and room tone.
- Confine the blend to the planned boundary window while preserving the complete output sample clock and unaffected retained samples outside that window.
- Do not blindly concatenate with overlapping crossfades: ordinary overlap shortens the audio by each fade duration and can drift away from the picture.
- Do not bring removed speech back through a handle. If a side lacks a clean handle, use the helper's documented room-tone/fade fallback or retain the candidate.
- Check exact sample count, unaffected-region mapping, boundary discontinuities, peaks, and final loudness. Measure true peak on the rendered result rather than trusting a limiter setting.

Compare original and edited context around every join. Paired focused transcripts from two models can expose a lost adjacent phrase, but differences need inspection. Restore a cut when neighboring content appears damaged or cannot be verified; fewer safe removals are better than a complete-looking filler count.

## Rebuild the native shortened sequence

1. Place the frozen keep ranges of the internal native source as video nests into the empty new sequence. Each nest retains the original camera choices, grades, and framing.
2. Use batch placement when available, supplying exact source in/out and shortened timeline positions. Build video while the target's audio tracks are empty: `linkAudio:false` may remove counterparts only after Premiere inserts them.
3. Inspect all batch results and reread the entire timeline. Some handlers swallow source-mark failures, and their response fields named `inPoint`/`outPoint` may actually describe timeline bounds.
4. Verify **all four** bounds for every clip: timeline `start`/`end`, source `inPoint`/`outPoint`. Decimal source marks produced one-frame discrepancies in the tested runtime despite plausible overall duration.
5. If ordinary setters cannot preserve exact bounds, use the verified native `Time.ticks` route on precisely identified new-sequence clips. Derive ticks as integer `frame_index × sequence.timebase`; read back every changed bound. Never apply a correction by clip index alone or to an unidentified sequence.
6. Import the new stereo PCM and place it at shortened timeline zero after video cleanup. Inspect actual channel mapping, gain, pans, duration, and enabled state. A successful WAV insertion is not proof of stereo routing.
7. Remove only verified unwanted audio counterparts. Confirm retained audio tracks and optional stems are in their intended enabled state, and that no doubled master or unused insertion is audible.

In one verified native build, the stereo PCM occupied A1 with both source channels and A2–A4 were empty. That is an observed valid layout, not a requirement for every project.

## Pilot picture transitions before adding many

Keep normal camera switches as hard cuts unless the brief calls for a transition. A very short dissolve can soften selected filler removals within the same underlying camera; assess whether it improves the face/gesture continuity or creates visible ghosting.

Determine the camera on each side from the inner angle clips, including the intended blend handles. Identical outer source-sequence items do not prove a same-camera join. If those handles cross a genuine camera switch, retain a hard cut unless the user requests otherwise.

Hendrik explicitly liked the V2 dissolve result and requested this workflow for reuse. For similar filler-cleanup requests, a useful starting point is that result's centered four-frame Cross Dissolve at 60000/1001 fps (about 67 ms), paired with a 20 ms fixed-duration audio blend where clean handles permit. At another frame rate, choose whole-frame timing near the intended visual duration and assess it in motion; four frames is not a universal duration. Adjust or omit a dissolve if a particular gesture produces distracting ghosting. The current user's creative direction takes precedence over this recorded preference.

1. Test one actual join through the ordinary transition tool first. Discover fresh clip IDs and inspect the intended incoming clip, adjacent outgoing clip, exact join frame, source handles, and active sequence.
2. Inspect the native result or exported XML for transition position, duration, and alignment. `success:true` or `accepted_unverified` does not prove the desired edit. Never automatically retry an uncertain transition.
3. The tested MCP wrapper could place `position:"start"` at a clip tail, while reversing the position still produced a one-sided black fade. Do not assume that changing the label fixes a centered two-clip dissolve.
4. If ordinary tools fail this pilot, use the skill's supported scripting fallback only for the missing operation. Guard the exact target sequence and track, verify each incoming/outgoing pair and expected start ticks, require actual adjacency, exclude the already-treated pilot, and prevent duplicate application.
5. Match the QE item by the exact intended clip's ticks and identity. A nearest-item fallback can target a neighbor after QE inserts transition items; never use a stale QE index.

The following call produced a centered four-frame dissolve in the tested runtime **when applied to the correctly identified incoming QE clip**:

```javascript
incomingQeClip.addTransition(transition, true, "4", "0", 0.5, false, true);
```

Treat that argument list as version-bounded evidence, not a universal API contract. The pilot exported a transition at frames 81–85 around join frame 83 with centered alignment. A four-frame `end-black` or `start-black` transition is a different result even when its duration is correct. Re-pilot on another version or clip type.

Apply only reviewed same-camera joins. Avoid a blanket “all transitions” operation: it may touch genuine camera cuts, the opening, or the final clip. Perform one final native XML audit confirming the exact requested join set, centered durations, and no tail fade. Where FCP7 exports clip bounds as `-1` beside transitions, resolve them through the adjacent transition before comparing the edit map.

## Verify and hand over

- Compare the original sequence's before/after track snapshot; it should remain unchanged. Verify the new sequence separately, including all source bounds, total kept duration, graded nests, channel routing, and offline state.
- Review the actual native edit around content joins and retained acknowledgments. Verify an exported native preview against the edited PCM and picture map, including export priming/timestamp behavior where relevant.
- Audio analysis and paired transcription do not establish pleasant sound. State whether listening and full or sampled native playback were completed.
- Save the native project with the new sequence selected. Retain the old version, internal source, interval manifest, audio QA, transition audit, and any restored-cut decision notes.
- Report actual removals and retained ambiguities. Do not claim export, listening, or full-episode QA merely because rendering has started or timeline checks passed.
