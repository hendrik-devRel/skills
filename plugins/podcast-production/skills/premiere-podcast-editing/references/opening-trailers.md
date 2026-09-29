# Opening trailers from an existing episode

For a 30–60 second trailer, three to five coherent dialogue moments can establish a hook, a useful question or contrast, and an unresolved point. Use the actual episode transcripts and surrounding passages to choose moments; this is an editorial starting point, not a fixed clip count.

## Preserve what the exchange establishes

Keep questions with their original responses and meaningful reactions. Preserve qualifications such as “seems,” “in this case,” and “I still have not found.” Label an informal anecdote or one game-building experiment when the excerpt otherwise sounds like a controlled benchmark. A short context label can supply an omitted subject without inventing a quote or strengthening the claim.

## Use the current edit's clocks

The formal episode, bonus introduction, cleaned bonus, and recorder master can all have different clocks. Derive each selected range from current native clip bounds and verified retained-range mappings; earlier transcript/editorial timestamps only locate candidates. Store both original-source intervals and output positions as integer frames at the rational sequence rate. A trailer may reorder excerpts, so preserve that ordered mapping explicitly.

Refine phrase boundaries with source context and waveform evidence; ASR word times alone are not exact cuts. Use one picture/audio map. Short centered blends with clean handles can smooth joins without shortening the planned output. This case used 20 ms raised-cosine audio blends confined to the fixed output clock. Do not reintroduce clipped speech through the handles or accumulate ordinary overlapping-crossfade duration losses. Restore or revise a cut if comparison suggests a neighboring word was damaged.

## Retain the approved picture; verify graphics in pixels

Build a separate trailer from the existing graded picture nests so the source camera edit and color remain available. Small labels can preserve context without covering faces. Check a representative title before multiplying it across the sequence.

In the tested Premiere Pro 2026 setup, a native MOGRT text pilot reported success but rendered blank. This is version-bounded evidence, not a general MOGRT limitation. Transparent UHD PNG labels with matching editable SVG sources were a practical construction fallback. Their canvas matched the sequence and their type remained readable at 1080p. Verify the imported graphics' placement, scale, alpha, and actual rendered text.

## Distinguish construction from verified delivery

Check all native clip bounds and the expected total duration. Export QA should sample every join and label, plus the opening and closing; compare exported audio timing and gain against the edited PCM. Apply the shared skill's audio, decode, and native-export checks. Report sampled picture review, ASR comparisons, and measurements accurately; they do not establish a full listening review.

The worked trailer was exported through Premiere at 1080p, 60000/1001 fps: 3,120 frames, 52.052 seconds. Native bounds and opacity ticks, 27 rendered picture samples, full audio/video decode, and exported audio against the PCM were checked. A measured 1,024-sample AAC delay was corrected only in a separate export copy's audio edit list; unchanged compressed packets and video timing, zero audio lag across six windows, and complete ending coverage were verified. This case does not justify applying that offset to an unmeasured export. The episode artifacts retain the original export and verification reports; a full subjective listening review was not performed.
