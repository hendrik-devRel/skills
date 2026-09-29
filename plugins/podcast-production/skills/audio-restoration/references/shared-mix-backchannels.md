# Shared-mix vocal backchannel trials

Use this workflow for a brief acknowledgment, hum-like vocal reaction, or other unwanted backchannel in recorded conversation. Keep the original audio and existing edit; build a separate trial in the scope requested. The electrical-noise recipe remains appropriate for independently established buzz, hiss, or clicks.

## Establish what is available

- Inspect the event in surrounding conversation. A short voiced burst with changing pitch can be a vocal reaction; it is not evidence of continuous mains hum. Low pitch alone does not establish the speaker's identity. Keep uncertain attribution explicit in the episode notes.
- Audit candidate sources before choosing a reference: channel layout, activity, relative level, waveform similarity after sample alignment, and listening. Differently named files can contain the same near-dual-mono shared mix with a few samples of offset. Very quiet, noisy mixed leakage is not a clean isolated-speaker reference.
- Mark whether the reaction falls between useful phrases or overlaps wanted speech. Confirm both boundaries against consonants, breaths, and word endings. A time-local gain reduction affects every sound in that interval.

## Choose a narrow treatment

**Between phrases:** test a modest linked-channel gain dip when the selected region contains no speech that needs to remain at its original level. A starting comparison is a −6 dB plateau with 50 ms cosine entry and exit ramps, adjusted to the event and available phrase gap. These are trial settings, not a validated universal preset. Keep ramps inside the selected interval; shorten them or decline the dip if there is insufficient room.

**Overlapping wanted speech:** do not apply the between-phrase dip automatically. If the unwanted harmonics are distinguishable in time and frequency, try a conservative spectral selection and attenuation. Shared spectral components will also attenuate the wanted voice. A local source-separation comparison is another experiment, but requires independent review of speaker identity, leakage, artifacts, bandwidth, timing, and gain. Neither a denoiser nor an estimated separator output establishes a recovered microphone ISO. Do not use a backchannel as a stationary noise print or apply a blanket low-frequency notch.

## Keep the sample clock and review the result

- Record the selected half-open sample interval `[start, end)`, source offset, gain, and ramp length. Convert times to sample indices once using a documented rounding rule; retain the source sample rate, channel layout, and frame count.
- Apply one identical gain envelope to every linked channel. It must return to unity at the selected boundaries and equal unity outside the interval. Preserve decoded PCM sample values outside the treatment; avoid whole-file normalization, dithering, or format conversion that would invalidate that check.
- Render separate original, processed, and removed-sound previews with identical context and playback gain. Compute removed sound as original minus processed on the same sample clock, preferably in floating point. Any preview boost must be identical across versions and disclosed separately from the replacement audio.
- Verify exact sample count, unchanged samples outside the interval, linked-channel envelope behavior, finite samples, headroom, and boundary continuity. Keep the unchanged source hash and event settings with the local trial report.
- Audition the complete phrase at matched level and then the removed signal. Reject or reduce treatment if it removes wanted words, weakens speech endings, creates an audible dip, or makes the conversation unnatural. Numeric attenuation and unchanged timing do not establish naturalness. Record listening status honestly; a measured pilot does not establish that every similar event is suitable for treatment.

## Apply reviewed events across an edit

When the user requests treatment throughout the recording, proceed within that scope while preserving the original project, delivered audio, and pilot. Create a new version. A successful pilot supplies a candidate treatment, not an automatic pitch threshold or a blanket noise-reduction pass.

- Keep a reviewed event manifest with recorder-clock start/end, attenuation, fade length, reason, confidence, surrounding context, overlap status, and review method. Store uncertain or rejected candidates separately. Automated screening, ASR, and speaker similarity can help find candidates; they do not alone establish nonlexical content, speaker identity, or absence of wanted speech.
- Map each accepted source interval through the actual native dialogue clips. For unit-speed clips, use `program_time = source_time - source_in + clip_start`; retain exact native ticks or rational time until the final sample conversion. Verify the selected source, enabled state, channel pairing, and playback speed. Excluded source regions have no output event. Skip and report events straddling a native cut instead of truncating their ramps onto a different phrase. A repeated source excerpt can legitimately produce an event in each distinct program occurrence.
- Deduplicate reviewer entries, then sort the projected half-open sample intervals and reject unresolved overlaps before rendering. Apply one envelope per output sample: duplicate passes must not turn a 6 dB dip into 12 dB. Keep a report of source-to-program mappings and skipped events.
- Use the intended native PCM as the timing and gain reference, including existing joins and automation. Preserve its format and exact frame count. For streamed processing, index each gain envelope from its absolute event start; do not restart a ramp at a file block boundary. Verify output against the intended envelope and prove decoded samples outside the event union are unchanged.
- Keep per-event original, processed, and removed-sound review examples with identical surrounding phrases and playback gain. Check events in their actual edited context as well as the source: adjacent clips, fades, music, or a different montage can change whether a dip is appropriate. Report measured checks and listening status separately.
- If picture timing is unchanged, reuse the verified encoded picture with the new verified native PCM delivery audio. Check sample alignment, codec priming and padding, exact picture payload/frame count, and complete decoding after muxing; a matching displayed duration is insufficient. Compare the native replacement export to the intended processed PCM so existing gain or fades are not accidentally applied twice.
- Report the ranges screened, candidates individually reviewed, events treated, skipped cuts, and unresolved cases. Distinguish automated coverage from continuous listening and avoid claiming all reactions were removed when uncertain or overlapping cases remain.

## Organizing shared speech onto tracks

Speaker-named tracks can organize speaking turns cut from the same shared mix. Label them as speaking-turn organization, not isolated microphones or extracted speaker stems. Overlapping voices remain mixed within each clip. Avoid playing duplicate copies simultaneously; check that the active clips reconstruct the chosen mix at the intended level, including joins. Preserve uncertain or overlapping turns without inventing a speaker assignment.

## Tool references

[Adobe's spectral selections](https://helpx.adobe.com/ie/audition/using/selecting-audio.html) support free-form frequency selection and adjustable effect intensity. [iZotope's dialogue example](https://www.izotope.com/en/learn/how-to-remove-background-noise-from-dialogue-recordings.html?page=2) uses attenuation where the unwanted event overlaps dialogue. These describe available techniques, not evidence that a particular vocal reaction can be removed cleanly.
