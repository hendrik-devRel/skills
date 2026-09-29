# Worked episode: Astra versus Fable first edit

Historical example and resume index, not a configuration for future episodes. Verified in Premiere 26.5.0 build 99 on macOS, using `adobe-premiere-pro-mcp` 1.2.8 and its CEP bridge. Inspect current project state before resuming.

## Deliverables on the original computer

Episode root: `/Volumes/OWC Envoy Ultra/9-Eps-Astra-vs-Fable/`.

- Original project unchanged: `astra-vs-fable5P1.prproj`.
- Canonical graded project: `astra-vs-fable5P1-Codex-First-Edit-v01.prproj`.
- Supporting files: `Codex-First-Edit/Audio`, `LUTs`, `Timelines`, `Review`, and `Notes`.
- Preview: `Codex-First-Edit/Review/Astra-Fable_First-Edit_Opening_120s.mp4`.
- Analysis scripts, local transcripts, and reports: `/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/`.

The analysis directory is optional historical evidence; the reusable skill and generator do not import from it. External-drive media must remain available or be relinked.

## Verified acquisition and mapping

All three Sony sidecars identified ILME-FX3A, S-Log3 / S-Gamut3.Cine. The guide's main-camera FX6 description was outdated. The user's “Slog4” wording did not match acquisition metadata.

| Role | Original | Picture | Microphone |
|---|---|---|---|
| Eric, guest | `GUEST-CAM/C0048.MP4` | UHD, HEVC, 10-bit | `Track1-Combo 1.wav` |
| Hendrik, host | `HOST-CAM/C0020.MP4` | 1920×1080, AVC, 8-bit | `Track2-Combo 2.wav` |
| Wide | `MAIN-CAM/C0015.MP4` | UHD, HEVC, 10-bit | Recorder reference |

Camera frame rate was 60000/1001. Both mono recorder WAVs were 24-bit/48kHz, exactly 257,353,152 samples (5361.524 seconds), under `RODECASTER-AUDIO/81 - 10 Oct 2026/`.

RODECaster program/ISOs were processed 1080p29.97 Rec.709 backups. ISO1/2/3 corresponded to guest/wide/host; the others sampled black. Backup color guided the grade; originals supplied edited picture.

## Alignment and editorial choices

Independent camera timecodes were unsuitable. Scratch-audio alignment produced these mappings, where `T_recorder = a * t_source + b`:

| Camera | a | b, seconds |
|---|---:|---:|
| Guest | 1.0000184562297811 | 60.35730168498182 |
| Host | 1.0000218451878555 | 23.379741773100545 |
| Wide | 1.000020619789782 | 41.262991450802275 |

Do not use these coefficients on other recordings. Source in-points were recalculated per shot; short shots limited residual intra-shot drift. Acoustic propagation and camera hardware audiovisual latency were not independently calibrated.

Main keep ranges in recorder seconds: `[[641.64,4662.50],[4727.20,5340.10]]`. This starts at the formal introduction, removes 64.7 seconds of explicitly discussed waiting/setup, and ends after the closing exchange. Pre-show `[[115.7,635.7]]` was retained as a bonus. Other demonstration pauses were not removed automatically.

- Main: `AF_FIRST_EDIT_V1_FORMAL_MAIN`, 4633.7624667 seconds (77:13.762), 163 camera clips, 20 markers, UHD59.94.
- Bonus: `AF_FIRST_EDIT_V1_BONUS_PREINTRO`, 520.0028167 seconds.
- Review: `AF_REVIEW_OPENING_120S`, 120.0032167 seconds.
- Source assembly: `AF_FIRST_EDIT_V1_SYNC_ORIGINALS`.
- Shared grade sequences: `AF_FIRST_EDIT_V1_ANGLE_GUEST`, `_HOST`, `_MAIN`.

A roughly five-second guest reply needed a native correction at edited 4270.7665–4275.7548167 seconds, guest source 4916.66175–4921.6500667. A nominal five seconds can quantize to 299 frames at 59.94; enforcing 300 without context can suppress a real turn. Reconstruction XML was updated afterward without reimporting.

## Grade and audio

All angles use one Sony `SL3SG3Ctos709.cube` input transform from Sony's s709 archive. Host nests are scaled 200% in the UHD program. Closeups needed no additional global correction. Wide: Exposure +0.15, Shadows +12, Highlights −10 to lift backlit subjects. These values were chosen from this footage, not prescribed for another studio.

Dialogue used a 75Hz high-pass, gentle 2.5:1 compression (10ms attack / 180ms release), and gradual inactive-mic attenuation up to 12dB with protected speech boundaries; no hard gate. A 192kHz oversampled limiter fed a 48kHz PCM24 stereo master, measured −16.1 LUFS / −1.5 dBTP for the full program. Exact sample count and matched-filter correlation verified zero timing shift. The master is audible on A1/A2; processed mono stems are disabled and muted on A3/A4. Raw microphones remain in the source assembly.

Premiere's native AAC preview had a measured 1024-sample delay and an audio edit-list media time of zero. A copy's edit list was corrected after diagnosis; all compressed packets and video timestamps were verified unchanged. The native file is preserved under `Review/QA/Astra-Fable_Opening_Native_AAC_Priming.mp4`. The canonical preview decodes at zero sample lag against the master. This export-specific correction is not a reason to shift timeline audio.

## Verification limits and remaining work

Native validation found no gaps or offline media; all three Lumetri LUTs and the wide adjustments were read back. Eight actual preview frames matched the cut plan, scaling, and grade. Later native frames were checked near the setup cut, corrected reply, and closing. The preview passed full decode; audio matched the reference at 0.999988 correlation and about −0.0066dB gain difference.

No complete watch/listen of the full episode was claimed. Article chart and game-demo screen inserts, final editorial polish, and a full-length delivery export remain finishing work. XML is an ungraded reconstruction; resume the native project for current edited and graded state. Discover fresh sequence/clip IDs instead of reusing transient IDs from old logs.

## Bonus pre-intro V2: filler cleanup

The later request created `AF_FIRST_EDIT_V2_BONUS_PREINTRO` in the same canonical native project. The V1 bonus track snapshot remained exactly unchanged. `AF_BONUS_V2_SOURCE` is a full internal clone of V1 used by the new edit; keep it because V2 references its existing camera cuts and graded angle nests.

The native V1 bonus audio began at recorder frame 6935 and ended at frame 38104. Its exact 31,169-frame duration was 520.0028167 seconds. V2 retains 29,712 frames, or 495.6952 seconds, after 33 reviewed filler removals totaling 1,457 frames / 24.3076167 seconds. These historical frame values are not defaults for future edits.

V2 uses 34 retained video nests, 32 centered four-frame same-camera Cross Dissolves, and one genuine camera change left as a hard cut. All four clip bounds were checked after batch placement; eight decimal-placement discrepancies required exact native `Time.ticks` corrections. The ordinary transition wrapper produced misplaced or one-sided fades during its pilot. The guarded incoming-QE-clip operation documented in [filler cleanup](filler-cleanup.md) produced the correct centered transitions, verified against the final native XML.

The final audio is `Codex-First-Edit/Audio/AF_Bonus_V2_Filler_Cleanup_Master_48k24_r2.wav`: stereo PCM24/48 kHz, 23,793,370 samples, −16.0 LUFS and −1.5 dBTP. All 33 joins use fixed-duration 20 ms raised-cosine blends with measured quiet handles. Samples outside blend windows retain the calibrated source gain and timing. The earlier WAV without `_r2` is a superseded analysis draft and is not the V2 timeline source.

Paired local ASR context checks and waveform review led to retaining ambiguous or connected fillers. One draft removal, F36, was restored because the comparison changed neighboring “good/at it/but” wording. The restored region matches the original PCM exactly. No subjective listening is claimed; this is a conservative review edit, not a guarantee that every hesitation is removed.

The full native 1080p59.94 review export was checked for all 29,712 video frames, channel parity, reference gain/correlation, loudness, and complete audio/video decode. Twenty-four exported still frames covered six blend joins, the hard camera change, and opening/middle/last-frame coverage; no full motion playback was claimed. Resume evidence is in `outputs/astra-fable-first-edit/bonus-v2-analysis/`, including `v2-edit-manifest.json`, `v2-native-final.xml`, transition and saved-project audits, filler context comparisons, and native picture/audio QA.

Final review: `Codex-First-Edit/Review/AF_FIRST_EDIT_V2_BONUS_PREINTRO.mp4`. This export independently reproduced the 1,024-sample AAC delay. Only its copy's audio edit-list media time was corrected; every compressed packet and video timestamp remained unchanged. Nine early/middle/late/junction comparisons then measured zero lag, both channels correlated about 0.999988 with the PCM master, and the complete reference ending was covered. The unchanged native export is archived as `Review/QA/AF_Bonus_V2_Native_AAC_Priming.mp4`. The Premiere timeline was not shifted. A compact handoff and copied QA are in `Notes/Bonus-V2/`.

On 2026-09-14, Hendrik explicitly praised the dissolve result and asked that the workflow be saved for later requests to “cut out the ems.” This is user feedback supporting the short-dissolve starting point documented in [filler cleanup](filler-cleanup.md); it does not change the recorded scope of the agent's own verification.


## Separate microphone revision

Hendrik's later preference is independent audible microphones: Eric on A1 and Hendrik on A2, with the listener's microphone fading to silence. The mixed-master versions remain historical revisions. Use this routing preference when continuing the episode unless the current user asks otherwise.

New copies preserve the live picture edits: `AF_FIRST_EDIT_V2_FORMAL_MAIN_SEPARATE_MICS` and `AF_FIRST_EDIT_V3_BONUS_PREINTRO_SEPARATE_MICS`. The main was cloned after a user trim to recorder 643.509533333333 s, so its duration is 4631.89393333333 s; do not reconstruct it from the older main start. The bonus retains 495.6952 s and its 33 filler removals and 32 picture dissolves.

Main A1/A2 use the existing full processed mono stems; bonus A1/A2 use `AF_Bonus_V3_Eric_Separate_48k24.wav` and `AF_Bonus_V3_Hendrik_Separate_48k24.wav`, each assembled from the approved filler keep map and original 20 ms blends. No combined master plays in these sequences.

The initial 8,810-key independent detection pass was too permissive: the user still heard listener sounds because bleed reopened the mic. The correction uses sustained speaking turns, roughly 80 ms handoff fades, and 21 narrow corroborated spoken-reply exceptions. Those exceptions open the reply mic without ducking an ongoing word on the owner mic. Unverified listener noises do not reopen a track. This is an automated full-program pass with focused waveform/transcript and native export checks, not word-by-word listening to the whole episode.

The user split Eric's opening clip at program 33.38335 s and added intrinsic Volume Mute automation. Preserve both. The current Level envelopes contain 2,470 native-verified keys across seven clips; the opening Eric clip is exact zero throughout, followed by a 10 ms anti-click fade inside the reply clip. All other effect parameters, manual Mute keys, clip enable states, source bounds, track states, and picture layout were verified unchanged. Five reviewed host-turn interiors contain no Eric reopenings. The source-level report also checks all 21 brief replies and 121 owned plateaus.

The reusable method is in [separate microphones](separate-microphones.md). Analysis, final control maps, exact clip guards, native readback, and audio QA live under `outputs/astra-fable-first-edit/mic-isolation-analysis` in the local recording-studio workspace. These episode-specific controls are evidence for this edit and are not reusable detection thresholds or edit boundaries for a different podcast.

The native Mix limiter has linked channels, True Peak mode, 7 ms look-ahead and 100 ms release. Common input boost remains +7.4 dB, compensating the measured center-pan attenuation; ceilings remain −3.2 dB for the main and −1.8 dB for the bonus. Earlier main R2 produced intersample overshoots despite its True Peak setting; the lower main ceiling corrected those measured events. Current `native-main-strict-mics-r1.wav` measures −16.5 LUFS / −2.2 dBTP, and `native-bonus-strict-mics-r1.wav` measures −16.2 LUFS / −1.7 dBTP. Exact sample counts are preserved; sampled source comparisons agree within one audio sample. Strict-pass evidence and native listening excerpts are under `Codex-First-Edit/Notes/Separate-Microphones/Strict-Turn-Muting` and `Review`. The R numbers identify QA audio exports, not new sequence versions.
