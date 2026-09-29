# Kinetic pilot v01 — independent QA

**Result: PASS for the alpha overlay and the corrected preview (`AF-Kinetic-Pilot-v01-PREVIEW-SYNCED.mp4`, approved for promotion to `AF-Kinetic-Pilot-v01-PREVIEW.mp4`).**

The original After Effects preview had a measurable AAC encoder delay. Main rebuilt the preview audio from the native `dialogue-first10.wav`; the corrected preview passes the audio-timing checks below. This did not affect the silent alpha overlay used in Premiere.

## Files and integrity

- Preview: H.264, 1920×1080, 60000/1001 fps, 600 frames, 10.010 s, AAC audio.
- Alpha: ProRes 4444, 3840×2160, 60000/1001 fps, 600 frames, 10.010 s, `yuva444p12le` pixel format.
- Full FFmpeg decode with `-xerror` passed for both original assets and for the corrected preview. No decode errors or corrupted packets were reported.
- Alpha inspected across all 600 decoded frames at 960×540 sampling resolution. Every frame contains transparency; all four canvas edges are completely transparent. Maximum artwork coverage is 5.074% of the frame.
- Nonzero-alpha aggregate bounds at 960×540: **[63,343,407,509]**, approximately 6.56–42.40% of canvas width and 63.52–94.26% of canvas height. The graphic has at least 5.74% bottom margin and 6.56% left margin.
- Frames 411–419 are intentionally fully transparent between the hook stack and the next question; there are no unexpected empty-alpha frames.

## Frame entrances

Inspected alpha frames immediately before, at, one frame after, and three frames after these expected onsets:

| Word | Expected frame at 59.94 | Observed |
|---|---:|---|
| No | 0 | Present from frame 0 |
| CAD | 152 | Appears at 152; absent at 151 |
| bench | 164 | BENCH and extended orange plate appear at 164 |
| until | 186 | Previous stack clears; until appears at 186 |
| Astra | 242 | ASTRA appears at 242; underline begins drawing afterward |
| engineering | 440 | ENGINEERING appears at 440 |
| still | 464 | still appears at 464 |
| Definitely | 562 | Previous stack clears; orange answer plate appears at 562 |

These match the approved input onset table exactly. Existing text does not visibly shift as new words arrive. The underlining is restrained and the CAD plate correctly expands for BENCH.

`pilot-onset-quadruplets.jpg` contains the visual evidence. This confirms rendering against the onset table; it does **not** independently establish phoneme-level auditory accuracy.

## Layout and style

Viewed the preview contact sheet at four frames per second and larger CAD, Astra, and prompting frames. The lower-left phrase stacks stay clear of both speakers' faces. The rabbit picture-in-picture remains unobstructed. No duplicated original caption line or competing old topic label is visible in the pilot samples. Text stays within the canvas and has adequate spacing between lines.

The result uses the desired pattern: white words building in fixed positions, a conspicuous orange CAD BENCH block, a larger ASTRA with an orange underline, a large ENGINEERING line, smaller mono supporting words, and the orange DEFINITELY answer. At full resolution the smaller supporting text is readable; thumbnail contact sheets naturally make it look much smaller.

## Audio alignment

Original AE preview: six independent waveform windows spanning 0.25–9.5 s all measured **1024 samples late at 48 kHz** (21.333 ms), with correlations 0.99931–0.99980 after shifting. This was AAC encoder priming and could make word graphics appear about 1.28 video frames early.

Corrected preview rebuilt from native dialogue: the same six windows all measure **zero-sample lag at 48 kHz**, with correlations **0.99895–0.99995**. Full decode passes. Low-level differences are consistent with AAC encoding. Audio was compared numerically; no subjective listening claim is made.

See `pilot-preview-audio-lag-confirmation.json` for the initial issue and `pilot-preview-audio-synced-qa.json` for the passing correction.

## Timing review limits

The waveform and the two independent ASR passes support the spoken sequence, but waveform amplitude alone cannot distinguish the exact phoneme boundaries of “until,” “Astra,” “engineering,” and “still.” The first two ASR spans can absorb pauses; engineering/still estimates differ by up to 0.18 s between models. The pilot renders the chosen large-v3-turbo boundaries exactly. Those four arrivals remain the useful focus during the user's subjective review, rather than silently changing them based on energy peaks.

This QA covers the 10.010-second pilot, its sampled visible compositions, decoded alpha validity, and numerical audio timing. It does not claim a final episode-wide typography pass or subjective listening review.
