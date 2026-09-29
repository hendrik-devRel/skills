# Separate microphones with speech-only output

Use when the user wants the listener's microphone silenced while the other person speaks. This is audio automation, independent of camera selection. A wide shot or listener reaction must not mute the actual speaker. Follow the requested balance between strict listener muting and preserving reactions; genuine overlapping words need different treatment from bleed, mouth noises, and grunts.

## Preserve the current edit

Inspect the live sequence first and preserve a saved checkpoint or clearly named prior version. Read actual clip source in/out and program bounds; the user may have trimmed or split clips since the original edit manifest. Keep raw recordings, timing, picture effects, and transitions intact. For a correction to the current version, preserve the user's manual changes rather than reconstructing the sequence from an old manifest.

Identify whether apparently separate tracks contain individual microphones or the left/right channels of a combined master. Two mono-looking waveforms are not proof of separate people. Verify each source path, channel mapping, clip enable state, track mute/solo, pan, and output assignment.

Place one microphone on each clearly named track, centered to the common Mix output. Remove the copied combined master from this new version once the separate stems are verified. Do not mix master and stems together. Full-length processed stems should retain the recorder clock and exact sample count. A pre-edited filler-cleanup WAV needs its own source-to-program map; render each microphone separately from the same approved keep ranges and blend handles.

## Determine who owns each speaking turn

When the user asks to mute the other microphone throughout a clear speaking turn, sustain that turn's ownership through normal pauses. Reopen the listener microphone for a real reply or interruption supported by its own signal and conversational context. Do not independently reopen it for each positive speech-detector result. Relative microphone energy is useful but cannot distinguish every mouth sound, breath, or quiet word; combine it with sustained own-microphone dominance and focused review.

The first exercised pass combined raw and +12 dB boosted Silero probabilities, permissive relative-level thresholds, and 400/700 ms padding. Its native gates reached exact zero correctly, but the user still heard listener sounds. Speech bleed 10–14 dB below the active microphone repeatedly reopened the listener gate. Broad padding joined those bursts into long open intervals. This approach did not satisfy strict listener muting; do not reuse it as the default for that request.

Speech recognition on an isolated microphone can still transcribe the other person's voice through bleed. A mixed or isolated transcript alone cannot assign a word to a person. Repeated waveform similarity at a fixed short delay, even with inverted polarity, is useful bleed evidence. In the worked opening, the listener waveform matched the host at roughly 3.75 ms inverted delay. Use such evidence to reject false reopenings. Under a strict-muting brief, an ambiguous nonverbal listener event is not an automatic protected exception. Keep verified brief-word exceptions narrow and explicit.

Fit short fades to the actual handoff and protect consonants without applying blanket long padding. Roughly 80–100 ms with nine control points is a starting point, with shorter anti-click fades at an exact user-made boundary. A confirmed sustained host turn should have an uninterrupted zero plateau on the guest microphone, and vice versa. Both microphones can open for verified overlapping words. Camera holds are supporting context, not the audio switch map; their minimum shot duration can suppress real short replies.

Use the user's example as an acceptance check before broad application. In this episode the guest microphone must remain zero for the opening 0–33.38335 seconds, until the user's split at the first reply. Count listener reopenings inside that interval, not merely the number of keys or zero samples elsewhere. A technically valid envelope can still fail the requested editorial behavior.

## Apply editable native envelopes

Keep recorder, edited-WAV source, and program clocks explicit. Main clips using full recorder stems take keys in absolute source time, including their source in-point. Keys for newly assembled bonus WAVs use that file's edited clock beginning at zero. Map through the audio helper's actual integer source/output sample report, including cumulative frame rounding and blend handles.

At a removed interval, a mapped gate must not destroy the outgoing audio blend. If an outgoing microphone is open and incoming audio is silent, preserve the complete blend handle, then fade down on the silent side. Check both gate values at every join rather than adding unnecessary fades everywhere.

Premiere's intrinsic `Volume > Level` raw value is not dB. In the tested Premiere 26.5 build, 0 dB read back as approximately `0.17782793939114`; raw `0` gave exact silence. Read the current unity value and confirm the component/property rather than assuming this constant on every version. Ordinary dB-based audio-keyframe tools may not express exact silence.

For the tested intrinsic Level control, convert a desired linear amplitude envelope with `rawLevel = measuredRawUnity * linearEnvelopeGain`. Include keys evaluated exactly at each clip's source-in and source-out, and reject keys outside those bounds. Store source timestamps as exact tick strings. Float value readback differed by at most about `6e-9`; compare with an appropriate small tolerance (the test allowed `2e-7`) while requiring zero plateaus to evaluate as zero.

Prefer ordinary tools for clip enabling, track mute, naming, and inspection. If a bulk raw-value envelope operation is missing, use a guarded native script: match sequence GUID, clip ID, source path, track index, and all four tick bounds before mutation; snapshot existing keys; replace only the copied clip's Level keys; then read back every timestamp/value and evaluate midpoint plateaus and ramps. Use exact `Time.ticks` strings. At 48 kHz, one sample is 5,292,000 Premiere ticks.

Manual muting may be stored in the intrinsic Volume effect's separate boolean **Mute** parameter, including automation keys. `clip.disabled == false` and a static `getValue()` result do not prove there is no mute automation. Inspect every non-Level parameter and its keys, and preserve them when replacing only Level automation. A user-made split can inherit all of the original clip's keys, including keys outside its new source bounds; snapshot the full old arrays, then bound new Level keys to the used source interval.

The tested interpolation enum `0` was nonlinear in raw amplitude: a 0→unity ramp read about 21% of unity at its midpoint. Nine closely spaced ramp controls still constrained the curve; offline amplitude-linear interpolation was not a bit-exact prediction between keys. Check native ramps for overshoot, timing, and clicks, and require exact zero/unity plateaus. Do not silently bake a different curve and call it the native result.

On a newly constructed separate-microphone version, enable the intended clips and tracks after envelope verification. When correcting a user's current version, preserve existing manual clip and mute automation. The editable volume curve supplies turn-by-turn silence while each track remains independently adjustable.

## Control and verify the combined output

Individual stem peak limits do not constrain their sum during overlap. Use one shared output limiter and set makeup gain once. Reuse existing verified Mix limiting when present; if needed, add Hard Limiter to an empty **Mix** insert in Premiere's Audio Track Mixer. The tested version offered **True Peak** mode, linked channels, ceiling, input boost, look-ahead, and release controls. Inspect actual controls; a different version may only offer sample-peak limiting.

In the tested CUA session, a floating MCP Bridge window kept capturing window observations even after selecting the mixer from Window. Closing it through its **Panel options → Close Panel** exposed the project; a second fresh observation was sometimes needed. Reopen **Window → Extensions → MCP Bridge (CEP)** before native calls and verify connection. Mixer numeric fields occasionally rejected AX clicks as offscreen; current screenshot coordinates plus select-all/type/Return worked and were confirmed by AX readback. `Command-W` closed the floating Track Fx Editor. Coordinate any temporary bridge closure with other editing tasks.

Account for center-pan law when replacing a dual-mono master with two centered mono tracks. In the worked episode, +4.4 dB limiter input boost produced only about +1.39 dB measured gain against the dual-mono reference: Premiere attenuated each centered mic by about 3.01 dB. The first native export measured about −19 LUFS instead of the intended −16 LUFS. Correct the common output gain from measured native audio; do not move speakers to opposite ears to recover level. The tested limiter used a −1.5 dB true-peak ceiling, 7 ms look-ahead, 100 ms release and a 0 dB Mix fader. Verify the correct mixer sequence and that no unintended inserts or duplicate gain stages are active.

An audio-only native export efficiently exercises all microphone automation and mixer effects without re-rendering unchanged picture. Adobe's `Sequence.exportAsMediaDirect(outputPath, presetPath, 0)` exports the entire sequence; use an inspected installed audio-only preset. The tested bundled 48 kHz stereo 16-bit WAV preset was adequate for QA. Preserve the 24-bit editing sources. Check the file even when the API returns `No Error`; after a timeout, inspect existing output before retrying.

Do not treat the True Peak switch as a guarantee. The worked main export measured −0.50 dBTP at two brief transients despite a −1.8 dB limiter ceiling and −1.8 dBFS sample peak; an independent meter and 4× float resampling confirmed the overshoots. Lower the output ceiling when measured headroom is insufficient, then re-export and remeasure. A whole-file `ebur128=peak=true` meter plus focused 4× float peak checks avoids doing unnecessary loudness-normalization processing merely to measure an export. The normalizing `loudnorm` filter took several minutes on this long program even with output discarded.

Measure the actual native export's sample count, loudness, true peak, stereo relationship, and alignment against the planned sum. Compare unaffected speech and exact mute plateaus separately from ramps and limiter reduction. Provide representative native excerpts for turn changes, soft replies, overlap, and loud passages. Statistical checks and local transcription do not establish subjective listening quality.

Save the project with clearly named separate-mic sequences and document the source/clock mapping, exceptions, native key verification, and export measurements. Coordinate active-sequence changes, bridge visibility, and blocking exports with any other task using the same Premiere project.
