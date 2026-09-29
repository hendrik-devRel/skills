# Shared-mix dialogue and camera clocks

Use this reference when a conversation has several people but the supplied files do not establish independent microphones. Three participants do not imply three isolated stems. Names such as COMBO, USB or Live Mix describe recorder routing, not verified speaker identity.

## Establish what was recorded

Probe and sample every plausible source early, mid-recording and late. A file with valid duration can be nearly silent, while several other files can contain the same mixed conversation. Compare activity, channel content and sample alignment before mapping files to people. When only a shared stereo mix is usable, keep it as the authoritative editable dialogue source. Do not duplicate that mix onto speaker-labeled tracks and call the copies isolated microphones, or use diarization to pretend to remove another person from overlapping speech.

Speaker turns can still guide camera cuts and gain automation. Use context and actual pictures to map voices to people; diarization labels alone do not identify camera angles. Keep camera scratch audio disabled in the editorial mix unless explicitly selected as a source.

## Level turns without changing the source clock

Measure sustained speech within each turn, then apply a slowly changing gain envelope to the shared mix with **the same gain on both channels**. A speech/activity mask may exclude pauses from measurement; it must not become a gate that deletes room tone, breaths or quiet replies. Overlapping voices remain inseparable in this route.

A tested three-person workflow used 100 ms RMS bins and the 75th percentile of active bins to estimate each long turn's speech level. Turns of at least 8 seconds with at least 20 active bins supplied estimates; shorter turns borrowed nearby, confidently identified turns by the same person. Review unreliable speaker boundaries and preserve the previous gain through ambiguous passages. These thresholds are examples to tune, not universal defaults.

The worked chain used bounded per-turn gain (up to ±12 dB), about 1-second cosine ramps, a continuous-state 65 Hz high-pass and a gentle stereo-linked compressor (2:1, 5 ms attack, 200 ms release). It then measured and applied final program loudness/true-peak processing. Settings such as −16 LUFS integrated and a −1.6 dBTP processing target were chosen for that delivery; use the current brief and measure the exact kept export. Turn-level gain is not an audio clip crossfade.

Keep exact native sample rate, channel count, sample count and source zero through processing. Use float intermediates and assert the final count; investigate a short output rather than silently padding over lost speech. A causal high-pass changes phase, so compare the processed audio to a reference passed through the same filter when measuring timeline lag. Test distributed speech and transition windows, both channels, and the final kept program.

Large boosts also raise room sound, interjections and breaths. Low percentile RMS is a descriptive noise-floor estimate, not a measured signal-to-noise ratio. Numerical speaker balance does not establish pleasant dialogue: audition quiet late turns, overlap, turn boundaries and loud passages, and state any remaining listening review.

## Keep the two AAC comparisons distinct

For original camera scratch audio, record the measured convention explicitly:

`recorder_seconds = a * camera_audio_presentation_seconds + b`

In one recording, all three camera AAC tracks yielded `a = 1` and `b = +1024/48000 = +0.021333… s`, with independent holdout windows. Under this convention, camera content at time `t` matches recorder content at `t + b`; camera source placement is `(recorder_time - b) / a`. Re-measure every recording. Zero presentation timestamps and a 1024-sample result alone do not prove encoder priming caused it.

Picture remains frame-quantized. At `30000/1001` fps, that measured offset is 0.63936 frame; nearest-frame placement differs from the audio-derived target by about 12.03 ms. Report the actual rounding residual and inspect native lip-sync for camera sensor latency. Audio correlation does not prove sample-exact picture sync.

An exported AAC file requires a separate comparison against the **matching native PCM export**, using native sequence zero and its exact export range. A positive candidate lag there means encoded audio is late relative to native PCM; it is not the camera-clock coefficient above. Use [streaming export-audio verification](streaming-export-audio.md) for long outputs. Never repair both measurements with one habitual 1024-sample shift.
