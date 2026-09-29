# Founder-to-Founder: measured full UHD export recovery

Validated locally on 2026-09-17 in Premiere 26.5. This records a specific native boundary failure and its verified recovery; it is not a universal export-range or H.264 timestamp recipe. Follow the [streaming export workflow](streaming-export-audio.md) for the general verification contract.

## Source and output provenance

All media remained on the user's drive. These case paths identify the evidence without adding footage to Git:

```text
P = /Volumes/OWC Envoy Ultra/Founder-to-Founder/Episode-1-Rahul
Q = P/Analysis/Assembly/Final-Combined-v03/Export-QA
Project = /Users/hendrikkrack/Library/CloudStorage/GoogleDrive-hendrik@coderabbit.ai/My Drive/Recordings/Podcast/Product-Podcasts/TRM-Labs/TRM-Labs-Final-v05-Source-Links-Fixed.prproj
Sequence = F2F_E01_TRAILER_V10_PLUS_FULL_V4_INTRO_CLEAN_4K_EXPORT
Sequence ID = 6a74e07e-840a-49fd-b3c0-ac9ce533335e
Preset = P/Analysis/Assembly/Final-Combined-v03/Presets/F2F-UHD-2997-H264-40Mbps-MRQ-v01.epr
Native picture = P/Exports/F2F-E01-Full-Episode-v05-UHD-Native.mp4
Native PCM = Q/F2F-E01-Full-Episode-v05-Native-Mix.aif
Verified delivery = P/Exports/F2F-E01-Full-Episode-v05-4K-YouTube.mp4
```

`P` and `Q` above are descriptive aliases, not shell assignments. The sequence has 1,737 trailer frames followed by 178,207 episode frames: 179,944 total at 30000/1001 fps. The episode already includes the authorized 21-frame intro hesitation removal and moderate hiss reduction. Its native stereo PCM is the authoritative final mix, including accepted trailer reaction muting and the music transition. Earlier standalone trailer mixes are not interchangeable references.

## Pilot result versus full endpoint failure

| Export | Intended range/count | Requested out point | Measured result |
| --- | --- | --- | --- |
| Initial pilot | `[1920,2160)`, 240 frames | Exact frame 2160 boundary | 241 picture frames; 384,385 PCM samples |
| Corrected pilot | Same range | Boundary minus `1/48000` second | 240 frames; 384,384 PCM samples; 8.008 seconds |
| Full native export | `[0,179944)`, 179,944 frames | Boundary minus `1/48000` second | **179,943 picture frames**; 288,198,309 PCM samples |

The corrected pilot PCM matched the edited dialogue across the intro join. Its native AAC separately measured +1,024 samples on both channels in six windows. Fresh AAC passed zero lag and tail/picture checks in `Intro-UHD-Pilot-v02-Verified.mp4`.

For the full export, the intended end was `179944 * 1001 / 30000 = 6004.1314666667` seconds. `full-export-receipt.json` records out-point readback `6004.1314375000002`, both export results `No Error`, and completion at 00:36:04 −0700. The success receipt did not establish the frame count. The native picture ended at 6004.0981 seconds, one frame short. Its AAC measured +1,024 samples in all 24 channel comparisons across 12 windows and lacked reference-tail coverage.

The full native PCM was usable: PCM16, stereo 48 kHz, 288,198,309 samples (6004.1314375 seconds). The intended picture duration equals 288,198,310.4 sample periods, so the difference is **1.4 samples**, inside the original two-sample tolerance. Unlike the pilot endpoint, this frame boundary is fractional on the audio sample grid. No universal offset was inferred and no tolerance was relaxed.

## Recover the actual missing native frame

The missing zero-based frame index was 179943. Native reference images distinguish it from frame 179942:

- `Native-Expected-F179943.png`: requested time 6004.10644166667 seconds, one-quarter frame inside F179943.
- `Native-Prior-F179942.png`: requested time 6004.073075 seconds, one-quarter frame inside F179942.

The first native tail, `Full-UHD-Tail-F179943-v01.mp4`, requested the exact F179943 boundary but read back 6004.0980833333333, 0.8 audio sample early. Its first IDR showed F179942. The desired image was its next dependent B-frame; neither the first frame nor an isolated B-frame was appended.

The second tail, `Full-UHD-Tail-F179943-v02.mp4`, began at F179943 + 0.25 frame (readback 6004.1064375) and requested an out point at F179947. Its first independent IDR matched the intended native image, with center MAE 2.506 against the expected image versus 4.338 against the prior frame. UHD decoded stills were downscaled only for this comparison to the 1920×1080 native PNG references. These image measurements and inspection support this particular frame identification; they are not general MAE acceptance thresholds.

The first packet had PTS 0, DTS −1001 and duration 1001 in time base `1/30000`. Its H.264 Main, UHD, progressive Rec.709 metadata and codec extradata matched the full export. The existing full stream used a two-frame decode reorder offset, so the independent appended packet's local DTS was set to −2002 while retaining its PTS, duration and compressed payload. No original prefix timestamps changed.

The tested extraction command, with paths assigned explicitly, was:

```sh
ffmpeg -nostdin -v error -n -i "$TAIL_V02" \
  -map 0:v:0 -frames:v 1 -an -c:v copy \
  -bsf:v 'setts=pts=0:dts=-2002:duration=1001:time_base=1/30000' \
  -video_track_timescale 30000 -movie_timescale 240000 "$ONE_IDR"
```

`ONE_IDR` was `Q/Full-UHD-Missing-F179943-IDR.mp4`. These timestamp constants belong to the measured streams above. Derive and validate them afresh for another file.

`Q/full-tail-repair.ffconcat` listed the original native MP4 with duration `6004.0981`, followed by the one-IDR MP4 with duration `0.0333666666666667`. Concat used matching AVCC extradata and disabled automatic bitstream conversion:

```sh
ffmpeg -nostdin -v warning -n -f concat -safe 0 -auto_convert 0 -i "$CONCAT_LIST" \
  -map 0:v:0 -map 0:a:0 -c copy -video_track_timescale 30000 \
  -movie_timescale 240000 -movflags +faststart "$PICTURE_COMPLETE"
```

`PICTURE_COMPLETE` was `Q/F2F-E01-Full-v05-UHD-Picture-Complete.mp4`. It retained the old AAC only as an intermediate input for subsequent full replacement; it was **not publishable** at this stage.

`verify_picture_tail_repair.py` compared every one of the original 179,943 video packets against the repaired prefix: payload hashes, PTS, DTS, duration, size and flags were identical. Exactly one native IDR was appended at PTS 180122943, DTS 180120941, duration 1001. The result had 179,944 frames and the intended rational duration. Strict tail decoding returned three frames without errors; the last decoded image was pixel-identical to the second native tail's first frame. No picture was reencoded.

## Complete PCM replacement and final checks

The existing `scripts/streaming_preview_audio.py replace` used `PICTURE_COMPLETE`, the full matching native AIFF, 12 windows and a new final output/report path. It stream-copied repaired picture and encoded AAC-LC at 320 kb/s, stereo 48 kHz, with movie timescale 240000 and faststart. There was no audio trim, gain change, offset, resampling, manufactured silence or `-shortest`. The source PCM was preserved. The helper published the separate output only after strict verification passed.

| Verified final property | Result |
| --- | --- |
| Local file | `P/Exports/F2F-E01-Full-Episode-v05-4K-YouTube.mp4` |
| File size | 30,208,527,894 bytes |
| Picture | H.264 Main; 3840×2160; progressive Rec.709; 30000/1001 fps |
| Frame count / duration | 179,944 / 6004.1314666667 seconds (1:40:04.131 elapsed) |
| Audio report | `PASS_ZERO_LAG`, no failures, output published locally |
| Sync | All 24 channel comparisons at zero integer-sample lag; minimum correlation 0.9999206 |
| PCM / sequential AAC extent | 288,198,309 / 288,198,656 samples; all reference samples covered, 347 legal AAC padding samples |
| End checks | Both active-tail signal comparisons pass; picture/reference difference 1.4 samples |
| Sample peak | −1.4241 dBFS, **not a true-peak measurement** |

Final compressed video payload SHA-256 (not a whole-file hash):
`ff3eec95cb32862eb78116f7fc68e231bb409322d870d555ba57290663d0ccc2`

Original/repaired-prefix packet manifest SHA-256:
`9db4c10d451554373f56bda3174838e57076d149cb544a687e09a3d38fa831d2`

Appended native IDR payload SHA-256:
`4b3aaa74c93d7f41311cf64b15987b76a137d01421d603b1546d81e30775889f`

Matched codec extradata SHA-256:
`e0a538e338815df93e63088c9fe9163188f1ec40c40f9344ddb956dc4987cb37`

The evidence files under `Q` are `full-export-receipt.json`, `full-native-aac-QA.json` (original failure), `tail-v02-frame-proof.json`, `full-picture-tail-repair-QA.json`, `full-repaired-last-frame-decode-QA.json`, `full-4K-YouTube-QA.json`, `full-4K-YouTube-ffprobe.json` and `FULL-4K-HANDOFF.md`. Preserve the failed native export and intermediary files with a do-not-publish note; never move or replace a file while an upload is reading it.

This establishes full sequential **audio** decoding, distributed audio sync, reference-tail coverage, unchanged compressed picture prefix and a focused final-frame decode/image check. It does not claim a full sequential video decode, a complete watch/listen pass, true-peak compliance or online upload completion. Upload receipts are separate evidence.
