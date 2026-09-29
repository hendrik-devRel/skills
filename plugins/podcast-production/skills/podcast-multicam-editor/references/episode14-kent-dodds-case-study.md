# Episode 14 — Kent C. Dodds case study

This case documents the CodeRabbit studio edit used to derive the reusable workflow.

## Source layout

- Guest/Kent close-up: `guest/C0041.MP4` with Sony sidecar XML.
- Host/Hendrik close-up: `host/C0010.MP4` with Sony sidecar XML.
- Mainframe/wide two-shot: `main/562_0037.MXF` with sidecar XML.
- Program audio: `seperate-audio-tracks/42 - 3 Jul 2026/Stereo Mix.wav`.
- Kent ISO: `Track1-Combo 1.wav`.
- Hendrik ISO: `Track2-Combo 2.wav`.
- The recorder's pre-switched `Default_...` video was retained as a reference but not used as the primary image source.

The two FX3 MP4 angles were S-Log3/S-Gamut3.Cine. The FX6 mainframe angle was S-Cinetone. The edit therefore labels the FX3 clips for the Sony technical LUT and explicitly labels the wide shot not to receive that LUT.

## Full edit

The first non-destructive full cut used isolated-microphone energy to choose the active speaker. It preserved the whole conversation and included the wide angle for transitions, overlap, and periodic resets.

Measured camera usage in that pass placed the wide angle at roughly 21.3%. Although technically present, close-ups dominated enough that the user perceived the mainframe as missing. The lesson is to measure screen time and evaluate hold length, not merely confirm that wide-shot clips exist.

## Tightened edit

The second sequence preserved the full edit and made only Hendrik-side repairs.

1. A local Whisper model transcribed the Hendrik ISO with word timestamps.
2. Transcript words were filtered through the independent host-speaker energy map to reject room bleed.
3. Eighteen conservative candidates were produced: explicit `um`/`uh` fillers plus awkward mid-thought pauses.
4. Waveform boundaries were refined to low-energy/near-zero samples.
5. Candidates less than two seconds apart were consolidated to avoid rapid repair cuts, leaving 16 accepted removals.
6. The accepted removals ripple-tightened 14.91 seconds.
7. Each join received a camera change on the first retained post-join frame, usually to the mainframe and periodically to a Kent reaction.
8. Each cover held for about 2.85 seconds; sub-second pre-join flashes were smoothed.
9. Existing wide holds were extended and additional paced wide resets were added.

Final tightened result:

- Runtime: `01:26:22:40` at 59.94 fps.
- Video cuts: 562.
- Removal markers: 16.
- Kent close-up: 63.44%.
- Hendrik close-up: 7.81%.
- Mainframe/wide: 28.75%, approximately 24 minutes 50 seconds.
- Shortest visual shot: approximately 1.26 seconds.
- Program mix enabled; both isolated microphones preserved but disabled.

The generator emitted an editable Premiere XML, removal list, cut list, summary JSON, candidate analysis, LUT copy, and import README. A validator confirmed one continuous video track, three continuous audio tracks, resolvable original media, matched source/timeline durations, and one marker per removal.
