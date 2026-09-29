# Select passages that deliver a complete idea

Read this when choosing or tightening standalone podcast clips. The reference describes an editorial method, not a predictor of reach. A Short should reward the viewer who never opens the full episode. A trailer can instead leave several questions unanswered to invite that longer watch.

## Build two evidence maps

Keep the episode and the surrounding content strategy separate:

- **Recording evidence:** original media, recorder transcript, identified speakers, surrounding questions, qualifications and the actual spoken example. This establishes what the speaker said.
- **Relevance evidence:** the user's content catalog, audience, earlier episodes, campaign themes and authorized internal notes. This helps explain why a passage matters and which audience would care. It does not validate a speaker's statistic or authorize adding a product claim.

For CodeRabbit, the successful pass connected recorded passages to review, validation, planning, accountability and founder decisions. It also looked beyond developer productivity to marketing operations, PMs, company origin and creative judgment. Reuse that breadth when appropriate; do not force every future episode into these subjects.

Read the whole discussion or a sufficiently complete transcript before settling on the loudest sentence. Search terms can locate subjects, but inspect the paragraphs before and after each hit. A qualification or the real payoff may arrive a minute after the memorable number.

## Find different reasons to watch

Draft more candidates than the requested deliverable count. For each, record:

| Candidate field | Editorial purpose |
|---|---|
| Angle and intended viewer | State the useful idea and who can act on it. |
| Original source range and clock | Make the selection retrievable before any timeline edit. |
| Speakers and identity evidence | Distinguish the opening questioner from the dominant answerer. |
| Opening premise | Check whether a new viewer understands the first sentence. |
| Development and example | Identify the mechanism, story or concrete detail that earns the runtime. |
| Payoff | Name the decision, implication or answer the viewer receives. |
| Protected qualifications | Record approximations, exceptions, hypotheticals, attribution and uncertainty. |
| Boundary doubts | Note uncertain words, a dependent pronoun, a clipped onset, a nearby next question or an overlap. |
| Possible visual support | Describe a diagram or emphasized phrase without fabricating product UI or statistics. |
| Why it differs from the other candidates | Detect an entire set repeating the same argument. |

Useful portfolio roles include a striking anecdote, an operational principle, a technical explanation, a responsibility dilemma, a product-management lesson and a founder story. These are prompts for variety, not quotas. Compare the actual takeaways across the shortlist. Five versions of “AI creates more code” are not five distinct angles.

Prefer a coherent contiguous answer when it contains its own setup and payoff. A question-and-answer exchange can be stronger than a monologue: retain the question when it establishes the problem, stakes or intended contrast. If shortening several ranges, preserve their order and causal relationship unless a deliberate alternative is clearly understandable and faithful.

## Let the thought determine duration

The worked set ranged from about 62 to 119 seconds. Most ran 90–120 seconds because the useful unit was a story or an explanation, while two ideas finished sooner. That is evidence of an editorial choice for this material, not an optimal-duration benchmark.

Before adding time, identify what it contributes: context, an example, a qualification or a payoff. Before cutting time, identify what is lost. Do not pad a complete 65-second answer to reach 90 seconds, or reduce a two-minute argument to its provocative opening while dropping its exception. Confirm current platform requirements separately when preparing publication; this skill does not freeze platform limits or promise engagement.

A candidate is ready for a first cut when a new viewer can follow the premise, the answer develops rather than merely repeats, and the ending resolves the idea. End before a new topic if it would make the Short feel incomplete. Preserve a natural breath or response where it belongs to the exchange.

## Refine the transcript without laundering uncertainty

Treat rough ASR as navigation. Extract candidate audio with context handles; approximately 1–3 seconds were useful in the worked pass, but extend them when a sentence needs more context. Keep the original ASR and a separate production record containing corrected words, source timings, selected ranges, speaker proposals, correction reasons and unresolved doubts.

Use a stronger local transcription pass with word timestamps when available. Focus another pass on doubtful regions without prompting it toward the desired answer. Inspect the surrounding recording and repeated uses of technical terms. Context can support orthographic corrections such as a known person's name, “Claude Code,” or “harness”; it cannot prove a completely unclear phrase.

Classify changes explicitly:

1. **Orthography or supported homophone:** correct a known name or repeated technical term, preserving the utterance. Record the reason.
2. **Editorial summary:** a heading or schematic may condense an idea, but should not look like a verbatim quote. Keep its scope and qualifiers faithful.
3. **Uncertain nonessential aside:** if removing it preserves the claim, omit the complete clause and verify the surrounding join. Do not substitute invented speech.
4. **Uncertain but retained speech:** keep the audio and use only supported emphasis words, or leave that region without a verbatim caption. Record that the captions are selective; do not present the export as a fully verified transcript. A request for complete accessibility captions still requires resolving or clearly marking that uncertainty.

Generate captions from the retained, corrected word list rather than raw ASR segments. Raw segments often include context handles, removed clauses or the next question. Re-map each word into the final program clock after the selected ranges have been fixed.

## Cut semantics first, then protect phonemes

Transcript start/end times are estimates. A low-energy waveform trough is useful boundary evidence, but cannot on its own tell whether a consonant, a quiet syllable or a word ending is complete.

- Inspect the opening with enough pre-roll to catch quiet first words. A rough candidate starting at “And so” or “I would” can already be inside the first word.
- Keep an uncertain aside's referent and connecting grammar intact. A shorter join that corrupts “internal tool” fails even if the sentence seems grammatical in the transcript.
- Preserve the entire last word before fading. An earlier trailer cut “merge” to “mer”; extending the tail fixed the editorial intent. Do not use that historical half-second extension as a universal amount.
- Check the next speaker and next question. A few extra frames may finish the word; more may begin an unwanted new sentence. Use source handles to make this decision rather than a fixed tail length.
- Apply short fades or blends after choosing valid boundaries. They can smooth a discontinuity, not restore a removed phoneme or make a misleading splice honest. Distinguish the treatment actually used in the final audio from a trial setting.

Verify joins by listening when possible. Focused retranscription, waveform checks and zero-lag correlation provide complementary evidence, not subjective approval. If listening is unavailable, keep the join reviewable and state the remaining limit rather than describing it as inaudible.

## Audit the words viewers notice most

Review the headline, large number, graphic labels and first/last sentences independently from the general transcript. They are easy places to accidentally strengthen a claim.

Examples from the worked pass:

- “~1,000 open PRs” preserved a conversational approximation; an exact audited count was not established.
- “40% of new capacity” preserved the denominator. A later hypothetical 60–70% was not a current allocation.
- “Every PM can ship. Should the feature exist?” asked whether the feature should ship. The rejected headline “Every PM ships. But should they?” instead questioned PM participation.
- The fine-tuning argument retained its proprietary-data exception and stayed scoped to the speaker's use case.
- An experimental invariants/code-owner practice remained an approach being tried, without a guarantee against bypass.

Time a numerical highlight to the spoken number. Paragraph headings can organize a premise earlier, but a caption that appears several seconds before its word is not speech-synchronized. Use the actual speaker turns for the camera and nameplate; an overall candidate label such as “Harjot” is not sufficient when Rahul asks the opening question.

## Use references as design evidence

Compare the requested examples directly when available: opening sentence, pacing, how much context they retain, crop, caption behavior, visual hierarchy and ending. Record whether an observation came from full playback, a sampled frame or a screenshot. A screenshot's visible scrubber label may be a hovered position, not the clip's duration.

Public likes or views do not isolate the effect of length, captions or editing. Do not attribute another creator's performance to a design feature without supporting analytics. The earlier Dwarkesh, Latent Space and other examples informed possible treatments; they did not establish a universal performance formula. Audience response to the user's own delivered set is evidence of their preference, not proof of future reach.

## Preserve enough to repeat the decisions

Keep an episode-local candidate sheet, source-linked production transcript, correction decisions, final range/turn/word manifest and short editorial QA note. Record accepted headlines and rejected misleading ones. Store private source paths and full transcript content with that project; the reusable skill needs the method and compact examples, not an unpublished catalog or complete recording transcript.

See [worked-eight-clip-case.md](worked-eight-clip-case.md) for the accepted portfolio and the limits of its verification.
