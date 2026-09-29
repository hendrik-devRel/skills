# Episode 16 — Francesco Bonacci / Cua

This case extends the Kent workflow to a different source setup. Episode-specific measurements belong in the delivered configuration and analysis, not universal defaults.

## Verified source differences

- Guest: `GUEST-CAM/C0048.MP4`, Sony FX3A, 3840×2160 HEVC, 60000/1001 fps.
- Host: `HOST-CAM/C0027.MP4`, Sony FX3A, 1920×1080 AVC, 60000/1001 fps.
- Main/wide: `MAIN-CAM/C0015.MP4`, Sony FX3A, 3840×2160 HEVC, 60000/1001 fps.
- All three Sony sidecars specify S-Log3 / S-Gamut3.Cine. Unlike Kent, the main angle also requires the matching technical normalization. The host is native 1080p, not native 4K.
- New recorder files: `RODECASTER-AUDIO/79 - 25 Sep 2026/`, 48 kHz / 24 bit, 2734.001667 seconds, stereo mix and isolated inputs.
- Earlier transcript: `RODECASTER-VIDEO/slessandro-cua/Audio/Live-Mix.wav`, 2727.756 seconds. Transcript times need a measured mapping to the new audio master.

## Transferable lessons

Camera role is not camera model or color profile. Check sidecars every episode. A recorder-folder date can disagree with camera metadata; synchronize by the recorded signal. Previously silent tracks from another recorder do not establish the quality of newly provided ISOs. A cloud storage quota does not equal free local disk space.

The requested edit preserves a full episode and a separately tightened pass. Candidate trailer passages are collected during the episode work, with a roughly one-minute trailer kept in its own Premiere project and not automatically prepended.

The isolated inputs on the new recorder were usable. Relative loudness analysis led to an ISO-based program: separately editable guest and host microphones, with the original recorder mix disabled as reference. The guest's proposed +5.5 dB relative balance is an episode measurement, not a reusable gain preset. XML encodes gain/pan intent; native import, listening and final delivery loudness remain separate verification steps. This differs from Kent's recorder-mix delivery and is why the generic workflow records an explicit audio mode.

## Working-edit outcome (September 9, 2026)

- FULL: 148,536 frames / 41:18.076 elapsed, 205 camera shots. TIGHTENED: 148,493 frames, 209 shots and two removal markers. Only 43 frames of silence were removed; no voiced filler passed the conservative checks. A fresh local transcription of the host ISO helped reject false gaps containing actual speech.
- Separate trailer: 3,506 frames / 58.492 seconds, five picture shots from three source-grounded excerpts. It was not prepended to the episode and remained a rough assembly without final titles or music.
- Native project read-back confirmed real assembled sequences, matching clip counts, muted stereo reference and active ISOs. Premiere's Effect Controls displayed guest +5.5 dB, host 0 dB and centered pan. The native 1080p host filled the 4K frame correctly.
- The original Sony LC-709 Type A technical LUT was applied at camera-source level and checked in Premiere on host, guest and wide pictures. This was technical normalization, not a claim of finished exposure/skin-tone matching.
- Final dynamics/loudness and a complete listening/lip-sync pass remained pending. Numerical synchronization, a successful native reopen and representative picture/playback checks are not publication approval.

Detailed measurements, native filenames and current verification status live with the episode deliverables. Do not reuse these gains, timings, cut counts or conclusions as defaults for another recording.
