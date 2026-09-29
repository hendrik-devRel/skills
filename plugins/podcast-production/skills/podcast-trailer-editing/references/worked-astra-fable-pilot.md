# Worked case: Astra/Fable 10-second kinetic trailer pilot

This is the chronological record of the pilot completed on 14 September 2026 in Premiere Pro 26.5.0 build 99 and After Effects 26.5 Apple Arm 64. It records both the successful construction and the failed attempts that affected the workflow. Names, IDs, font locations, timings and dimensions below belong to this episode; rediscover them for another project.

The deliverable was a **600-frame, 10.010-second pilot**, not a typography pass on the entire trailer. The user subsequently asked to make this process repeatable. Do not interpret the successful pilot as permission to apply its exact wording, coordinates or accent frequency to every episode.

## Evidence and starting state

A portable subset of the editable project, reference media, final preview, measurements and review notes is bundled with this skill under `assets/worked-pilot/`; see [example assets](example-assets.md). The absolute links below retain provenance to the original episode workspace. Its full tool log and external camera media are not required to understand the procedure and are not included in the skill archive.

The canonical edit was [astra-vs-fable5P1-Codex-First-Edit-v01.prproj](</Volumes/OWC Envoy Ultra/9-Eps-Astra-vs-Fable/astra-vs-fable5P1-Codex-First-Edit-v01.prproj>). Its active trailer was `AF_TRAILER_V1_OPENING`, ID `3d9e3559-07e3-4add-9d3f-6146e8d0d543`. The source was UHD 3840×2160 at 60000/1001 fps. Premiere used 254016000000 ticks/second and 4237833600 ticks/frame. The pilot range was ticks 0–2542700160000.

A fresh [source-before.xml](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/source-before.xml) captured the current native edit. The user had already changed camera cuts, inserted the rabbit photograph and added captions. Earlier trailer manifests were therefore not a safe timing source.

The final [handoff](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/HANDOFF.md), [layout specification](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/layout-spec.json), [word timing manifest](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-word-timings.json) and [independent QA report](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/qa-summary.md) hold the persistent evidence. Exact operation and result details that were not serialized into those files were recovered from this task's [local tool history](/Users/hendrikkrack/.codex/sessions/2026/09/14/rollout-2026-09-14T01-37-52-01a09f10-c72d-7e30-af7e-93ee8540c499.jsonl), principally 19:11–19:25 UTC. That log is an audit source, not a required dependency for a new trailer.

## 1. Translate the request into a bounded style test

The user requested words appearing as spoken, pronounced size changes, occasional underlines and orange backgrounds. They specified Plus Jakarta Sans SemiBold and IBM Plex Mono. The scope was the first ten seconds, retaining the edited conversation, separate cameras, isolated microphones and rabbit inset.

The first screenshot was evidence of the current trailer, not the typography target. The second screenshot supplied the desired hierarchy: a small introductory line, a much larger numeric phrase, then smaller supporting text. Two downloaded trailers supplied moving references.

The Premiere podcast-editing skill and installed Higgsfield use After Effects integration were read. The AE `ae-clean-rig` typography and reference-motion guidance informed the implementation: native text and shapes, measured reference behavior, sparse keys, actual font resolution, and rendered proof. The working integration was reused. Disabled `eval.run` was not bypassed; construction used catalog operations and `batch.run`.

## 2. Analyze the original references before animating

A separate read-only analysis inspected the MP4s with FFmpeg/ffprobe, contact sheets and dense samples.

| Reference | Measured media | Coverage and role |
|---|---|---|
| [NVIDIA-Podcast-Trailer.mp4](/Users/hendrikkrack/Downloads/NVIDIA-Podcast-Trailer.mp4) | 3840×2160, 30000/1001 fps, 65.966 s | Contact sheets across 0–60 s; 10 fps samples at 0–3 s and 5–8 s; original-frame inspection around 0.25–0.85 s. Main typography/motion reference. |
| [Merge - Episode 3 trailer v02.mp4](</Users/hendrikkrack/Downloads/Merge - Episode 3 trailer v02.mp4>) | 960×540, 30000/1001 fps, 72.673 s | Contact sheets across the clip. Pacing, shot variety and end-card reference. No dialogue kinetic text was observed in the inspected footage. |

The NVIDIA words appeared directly into prepared phrase positions. Existing words stayed still; they did not recenter as the sentence grew. Phrase groups built, held and cleared, with deliberate empty intervals. Large bold/italic principal words contrasted with connectors roughly half their cap height. White dominated; square orange plates emphasized selected terms and expanded when more highlighted words arrived. The inspected entrances did not justify bounce or slide animation.

At a decoded 1920×1080 sample at approximately 5.6 s, the orange THE MODEL plate occupied about x=578–1342, y=660–807. Its dominant decoded interior color was #FD5608. The implementation chose the close design value #FF570A; this was not a claim to have recovered a formal brand token. Underlines were a user-requested addition, not an observed feature of the sampled NVIDIA frames.

The full [reference-style-guide.md](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/reference-style-guide.md) distinguishes observations from proposed choices. [Every-frame entrance samples](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/nvidia-models-entry-everyframe-labelled.jpg) and [the orange-word sample](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/nvidia-orange-wordblock.png) preserve the visual anchors.

Internet research consulted [Adobe's native text animation documentation](https://helpx.adobe.com/after-effects/desktop/animating-text/text-animation/animating-text.html), its [letter-by-letter tutorial](https://www.adobe.com/learn/after-effects/web/animate-letter-by-letter), and [IBM's official font repository](https://github.com/ibm/plex). The actual pilot used word-layer in-points for direct reveals rather than assuming that a text animator was necessary.

## 3. Protect the current edit and export fresh reference media

The trailer was duplicated with its existing content. The full-length duplicate initially carried the name `AF_TRAILER_V2_KINETIC_PILOT_10S`; it was later renamed `AF_TRAILER_KINETIC_WORK_COPY`, ID `0f1c7459-cd63-4445-94fb-0d53729dfa8f`. Creating this duplicate preserved native camera nests, grades, source bounds, microphone edits, music and the photo.

A native export of the first 600 frames supplied [dialogue-first10.wav](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/dialogue-first10.wav). Its SHA-256 was `a7604034eb8c7b436560c8b111b16b2b21ed10047d12ab2bfd2481093bd6985e`. The filename denotes the native program-audio reference; it was not a newly flattened replacement for the two microphones in Premiere.

The first attempted source export used a save/restore-marks script with a `finally` block, but that operation failed before a successful export was established. The successful native WAV export instead set in/out marks to 0 and 2542700160000 ticks on the working duplicate, exported the marked range, and kept those pilot marks for later subsequence creation. A future operation on an existing source sequence should save and restore its marks; that preferred pattern is not a claim that the failed first attempt completed.

These local scripting details required correction:

- `__findSequence` was unavailable inside bare `execute_extendscript`. The working script iterated `app.project.sequences` and matched `sequenceID`.
- A bare final JSON expression returned `undefined`; returning an object yielded `[object Object]`. Useful structured readback required `return JSON.stringify(...)`.
- An export attempt using the HEVC `01 - Match Source - High Bitrate.epr` returned `Error: -1`. The cause was not established. It was not treated as a completed export.

Before exporting clean picture, the duplicate's original caption display was toggled off through Premiere's UI. The old `02_prompting.png` label was disabled in the duplicate because the kinetic question replaced it. The rabbit photograph remained.

| Export | Local preset / result |
|---|---|
| Native WAV | `/Applications/Adobe Premiere Pro 2026/Adobe Premiere Pro 2026.app/Contents/MediaIO/systempresets/3F3F3F3F_57415645/Waveform Audio 48kHz 16-bit.epr`; successful 48 kHz 16-bit stereo reference. |
| Attempted HEVC picture | `/Applications/Adobe Premiere Pro 2026/Adobe Premiere Pro 2026.app/Contents/MediaIO/systempresets/4A454646_48455643/01 - Match Source - High Bitrate.epr`; failed with `Error: -1`. |
| Working H.264 picture | `/Applications/Adobe Premiere Pro 2026/Adobe Premiere Pro 2026.app/Contents/MediaIO/systempresets/4E49434B_48323634/High Quality 1080 HD.epr`; successful [pilot-background.mp4](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/pilot-background.mp4). |

The background was probed and a [2.8-second frame](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/background-2.8.png) was extracted and viewed. This checked the actual current picture, scale and inset before design work.

## 4. Resolve the installed fonts in After Effects

An ordinary Fonts-directory search found Jakarta but not IBM Plex. AE's font inventory and `text.measure` established that IBM Plex was already Adobe-synced under an opaque name. No new font installation was necessary.

| Intended use | Actual AE resolution in this case |
|---|---|
| Principal text | PostScript name `PlusJakartaSans-SemiBold`, family Plus Jakarta Sans, style SemiBold; measured layers resolved to [/Users/hendrikkrack/Library/Fonts/PlusJakartaSans-VariableFont_wght.ttf](/Users/hendrikkrack/Library/Fonts/PlusJakartaSans-VariableFont_wght.ttf). Version 2.071, variable `wght` range 200–800, default 400, design vector **600**. |
| Duplicate Jakarta registration | The same PostScript name also existed as a static instance at [Plus Jakarta Sans SemiBold-bbaa.otf](</Users/hendrikkrack/Library/Application Support/Adobe/.User Owned Fonts/Plus Jakarta Sans SemiBold-bbaa.otf>). It was not the file reported by the pilot text measurements. |
| Supporting mono text | PostScript name `IBMPlexMono`, family IBM Plex Mono, style Regular; actual file [.39868.otf](</Users/hendrikkrack/Library/Application Support/Adobe/CoreSync/plugins/livetype/.w/.39868.otf>). |

The variable font reported a confusing “Regular” full name while its style and design vector identified SemiBold. The implementation explicitly called `text.set_variable_font` with `axes:{wght:600}` on every Jakarta word layer. `font.list_missing` reported no missing fonts. These paths explain this machine's resolution only; another computer must resolve its own installed or synced font.

## 5. Transcribe the exported edit and preserve timing uncertainty

The [local transcription script](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/transcribe_pilot_words.py) loaded cached Whisper large-v3-turbo on CPU, used four Torch threads, English, `fp16:false`, `condition_on_previous_text:false`, and `word_timestamps:true`. Its initial prompt supplied the domain terms “CAD bench,” “Astra,” and “prompt engineering” while asking it to preserve spoken words.

A separate base.en pass and cropped boundary checks tested the transcription. The models agreed on the substantive wording; base.en rendered “you say” as “to say.” The chosen text followed the large-v3 pass:

> No one model had ever really passed the CAD bench until Astra just blew it away. So prompt engineering still plays a role, you say? Definitely.

Each chosen ASR onset was quantized with `frame = round(seconds * 60000 / 1001)`, then `time = frame * 1001 / 60000`. This made the animation deterministic on the sequence grid. It did **not** turn estimated word boundaries into phoneme-accurate measurements.

The raw [primary ASR](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-current-word-asr.json), [independent check](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-current-word-asr-base-check.json), [crop checks](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-word-asr-boundary-check.json), [waveform](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-asr-waveform.png), and [onset recommendations](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-word-onset-recommendations.md) were retained.

“The,” “until,” and “Astra” spans could absorb pauses. Engineering/still differed by up to 0.18 s between models. These boundaries remained candidates for subjective playback review. The pilot endpoint cuts an ongoing exchange; the last word's ASR end did not prove a natural edit point.

| Word | ASR onset (s) | Reveal frame | Frame-grid onset (s) |
|---|---:|---:|---:|
| No | 0.00 | 0 | 0.000000 |
| one | 0.20 | 12 | 0.200200 |
| model | 0.46 | 28 | 0.467133 |
| had | 0.76 | 46 | 0.767433 |
| ever | 0.92 | 55 | 0.917583 |
| really | 1.12 | 67 | 1.117783 |
| passed | 1.42 | 85 | 1.418083 |
| the | 1.92 | 115 | 1.918583 |
| CAD | 2.54 | 152 | 2.535867 |
| bench | 2.74 | 164 | 2.736067 |
| until | 3.10 | 186 | 3.103100 |
| Astra | 4.04 | 242 | 4.037367 |
| just | 5.12 | 307 | 5.121783 |
| blew | 5.70 | 342 | 5.705700 |
| it | 6.10 | 366 | 6.106100 |
| away. | 6.26 | 375 | 6.256250 |
| So | 7.00 | 420 | 7.007000 |
| prompt | 7.10 | 426 | 7.107100 |
| engineering | 7.34 | 440 | 7.340667 |
| still | 7.74 | 464 | 7.741067 |
| plays | 8.06 | 483 | 8.058050 |
| a | 8.38 | 502 | 8.375033 |
| role, | 8.50 | 509 | 8.491817 |
| you | 8.94 | 536 | 8.942267 |
| say? | 9.04 | 542 | 9.042367 |
| Definitely. | 9.38 | 562 | 9.376033 |

## 6. Build the native AE pilot and establish the layout

AE initially had the unrelated, saved `CodeRabbit-Skills-in-Motion.aep` open with `dirty:false`. `project.new` with `save:true` preserved that project, and the new pilot was saved as [AF-Kinetic-Pilot-v01.aep](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/AF-Kinetic-Pilot-v01.aep).

The new composition `AF • Kinetic typography • 10s pilot` was created at 3840×2160, 60000/1001 fps and 10.01 s. The native WAV and current picture export were imported. The 1080p picture was placed at 200% scale as a locked guide layer named `REFERENCE PICTURE • guide • not exported`.

A temporary whole-phrase CAD BENCH text layer tested font size and measurement. It was removed before the full build. The final build used **26 native text layers, four native shape layers and one locked guide layer: 31 layers**. Word layers were named by phrase and global word number, for example `02 • 12 • ASTRA`; phrase labels distinguished groups.

Each word was created with `layer.create_text`, styled through `text.set_style`, assigned a quantized in-point and its phrase's out-point with `layer.set_props`, then measured with `text.measure`. The main creation batch contained 105 operations and returned zero failures. The measured baseline width of each actual font instance drove horizontal placement.

All text used white fill, left justification, tracking 0, anchor [0,0]. Words without orange plates had a 3 px dark stroke, color [0.03,0.03,0.03], behind the fill. Words on orange plates had no stroke. Starting x was 280 px. The next word's x was the previous x plus its measured width and a gap of 0.28×font size for Jakarta or 0.60×font size for Mono. Words therefore remained fixed as the phrase built.

| Group | Fixed line | Font | Size (px) | Baseline y (px) | Measured line width (px) | Requested phrase out (s) |
|---|---|---|---:|---:|---:|---:|
| 01 | No one model | Jakarta SemiBold | 116 | 1480 | 800.864 | 3.1 |
| 01 | had ever really | IBM Plex Mono | 88 | 1608 | 792.000 | 3.1 |
| 01 | passed the | Jakarta SemiBold | 164 | 1775 | 891.996 | 3.1 |
| 01 | CAD BENCH | Jakarta SemiBold | 210 | 1990 | 1265.880 | 3.1 |
| 02 | until | IBM Plex Mono | 96 | 1510 | 288.000 | 6.85685 |
| 02 | ASTRA | Jakarta SemiBold | 258 | 1790 | 827.406 | 6.85685 |
| 02 | just blew it away. | Jakarta SemiBold | 124 | 1990 | 1052.512 | 6.85685 |
| 03 | So prompt | Jakarta SemiBold | 112 | 1460 | 587.888 | 9.3760333333 |
| 03 | ENGINEERING | Jakarta SemiBold | 198 | 1670 | 1354.122 | 9.3760333333 |
| 03 | still plays a role, | IBM Plex Mono | 98 | 1840 | 1117.200 | 9.3760333333 |
| 03 | you say? | Jakarta SemiBold | 120 | 2000 | 515.040 | 9.3760333333 |
| 04 | Definitely. | Jakarta SemiBold | 202 | 1950 | 999.900 | 10.01 |

These are text baseline coordinates, not glyph bounding boxes. The first column of every line starts at x=280. [layout-spec.json](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/layout-spec.json) preserves every measured word width and exact x value. It is the full numerical layout record; the onset manifest also contains earlier *proposed* phrase groups that were not identical to the finished design.

The fixed lower-left placement kept text below the faces and clear of the right-hand rabbit photo. The four thoughts used different emphasis: CAD BENCH on orange; large white ASTRA with orange underline; large ENGINEERING with smaller Mono support; then Definitely. on orange.

## 7. Add the orange plates and underline

Each accent used a native shape layer, `shape.add_group`, `shape.add_rect` and `shape.add_fill`. Shapes used square corners and fill [1,0.341176,0.039216,1], approximately #FF570A. Their anchors were [0,0]; the rectangle's internal position was half its size so the layer's position represented its top-left corner.

| Native shape | Position x,y (px) | Width × height (px) | Visible interval / behavior |
|---|---:|---:|---|
| `01 • CAD • orange plate` | 256,1810 | 511.680 × 224 | Frame 152 to first phrase out-point 3.1 s. Width is CAD's measured width +48. |
| `01 • CAD BENCH • plate expansion` | 256,1810 | 1313.880 × 224 | Starts at frame 164, same out-point. The second larger plate overlays the small plate, expanding the highlight without moving text. |
| `02 • ASTRA • underline` | 280,1830 | 827.406 × 10 | Starts at frame 242, ends at 6.85685 s. Two Scale keys: [0,100] at frame 242 and [100,100] at frame 247. Left-anchored five-frame draw. |
| `04 • Definitely • orange plate` | 256,1776 | 1055.900 × 228 | Frame 562 to 10.01 s. Width is text width +56. |

These plates and underline were editable shapes, but not an automatic text-fitting rig. Changing the word length requires manually resizing the corresponding plate/underline and possibly the following word positions.

No generic bounce, overshoot, continuous camera movement, or per-frame opacity keys were added. Direct layer in-points supplied the reveals. The second phrase ended at frame 411; frames 411–419 were intentionally transparent before “So” appeared at frame 420.

## 8. Correct the preview construction and verify editable text

An attempt to temporarily set the locked reference layer's `guideLayer:false` for a composite still failed. AE reported warnings that the guide property could not change while the layer was locked, even though the batch's overall result said `ok:true` and `failed:0`. That first “composite” operation was not proof that the background had rendered.

The resolved construction created a separate 1920×1080 composition, `AF • Review with picture and sound`, at the same frame rate/duration. It contained the native picture-and-sound export and the UHD typography composition scaled to 50%. The overlay's guide remained excluded from actual exports. This separated review picture from transparent delivery without repeatedly toggling guide state.

Native AE stills were rendered and viewed at the CAD, ASTRA and prompting layouts: [review-cad.png](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/review-cad.png), [review-astra.png](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/review-astra.png), and [review-prompting.png](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/review-prompting.png).

To prove editability, the typography composition was duplicated as `QA • Editable text verification`. Its ASTRA Source Text was changed to TEST, measured in the resolved Jakarta SemiBold font, and rendered at 4.4 s. [qa-editable-text.png](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/qa-editable-text.png) records that proof. The QA duplicate was deleted and the actual AEP saved; TEST was not left in the deliverable.

## 9. Render the transparent overlay and review MP4

Two native AE render-queue items were configured:

| Queue item | Composition / settings | Saved output |
|---|---|---|
| 1 | UHD typography; `High Quality with Alpha`; output audio explicitly Off | [AF-Kinetic-Pilot-v01-ALPHA.mov](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/AF-Kinetic-Pilot-v01-ALPHA.mov) |
| 2 | 1080p review; `H.264 - Match Render Settings - 15 Mbps` | Initially `AF-Kinetic-Pilot-v01-PREVIEW.mp4`; the original AE export was later preserved as [AF-Kinetic-Pilot-v01-AE-RAW.mp4](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/AF-Kinetic-Pilot-v01-AE-RAW.mp4). |

The native render log records 12:18:54–12:19:10 PDT for the overlay, then 12:19:10–12:19:28 PDT for the review, 34 seconds total. [AE render log](</Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/AF-Kinetic-Pilot-v01.aep Logs/AE 9-14-26 12-18-54 PM PDT.txt>).

The alpha actually probed as ProRes 4444, 3840×2160, 60000/1001 fps, 600 frames, 10.010 s, `yuva444p12le`, with no audio stream. The preview probed as H.264 1920×1080 at the same frame count/rate, with AAC audio. These file checks were needed in addition to render-queue success.

## 10. Integrate into Premiere while retaining editable camera and mic lines

The rendered alpha was imported as project item `000f47eb`. All four audio tracks in the working duplicate were confirmed unlocked, then temporarily locked for the video insertion. The alpha was overwritten onto zero-based video track 4 (V5) at time 0 with `linkAudio:false`. Its end and source out-point were normalized to ticks 2542700160000 and read back. The audio tracks were restored to their prior unlocked state. Two wrapper calls around the lock/name/end-point changes reported host-side scripting errors despite partial mutations. Readback established the renamed project item, exact overlay end/out-point and restored unlocked audio tracks; the errors were not treated as transactional rollbacks. The V5 name was set through the supported `rename_track` tool.

The full work copy still contained the original long music clip, so its end was approximately 147.981 s. It was not falsely treated as a ten-second sequence simply because an in/out range existed. `create_subsequence` with `ignoreTrackTargeting:true` produced a genuinely bounded sequence from the marked pilot range.

| Role | Final sequence name | ID |
|---|---|---|
| Original, preserved | `AF_TRAILER_V1_OPENING` | `3d9e3559-07e3-4add-9d3f-6146e8d0d543` |
| Full-length working duplicate | `AF_TRAILER_KINETIC_WORK_COPY` | `0f1c7459-cd63-4445-94fb-0d53729dfa8f` |
| Bounded pilot | `AF_TRAILER_V2_KINETIC_PILOT_10S` | `6d8b0139-8358-4ea9-ae91-dfed760935d3` |

The new subsequence initially had suffix `_Sub_01`. Both sequence names and project-item names were then changed to the final names above.

| Pilot track | Native clips and retained interval |
|---|---|
| V1 MAIN – Wide camera | `000f47ed` 0–6.9069 s; `000f47ee` 6.9069–10.01 s |
| V2 HENDRIK – Host camera | `000f47ef` 0–6.9069 s; `000f47f0` 6.9069–10.01 s |
| V3 ERIC – Guest camera | `000f47f1` 6.9069–9.376033 s |
| V4 TITLES – Trailer graphics | Rabbit `IMG_8727.jpg`, `000f47f2`, 2.385717–5.6056 s; `02_prompting.png`, `000f47f3`, 6.9069–10.01 s, **disabled** |
| V5 KINETIC TEXT – first 10s | Alpha `000f47f4`, 0–10.01 s |
| A1 ERIC – Guest mic | `000f47f5` 0–6.740067 s; `000f47f6` 6.9069–9.376033 s; `000f47f7` 9.376033–10.01 s |
| A2 HENDRIK – Host mic | `000f47f8` 0–6.740067 s; `000f47f9` 6.9069–10.01 s |
| A3 existing music | `000f47fa`, 0–10.01 s, retained source `podcast-interview-background-music-318260.mp3` |
| A4 | Empty |
| C1 existing subtitles | Copied by subsequence; display required a second UI toggle, described below. |

The program still used the native graded camera sources. Existing folder/angle names had historically been opposite the people: GUEST angle contained Hendrik in the cap, HOST angle Eric with blond hair. The person-labeled timeline tracks prevented this naming trap from changing the picture.

## 11. Discover the subsequence caption issue and record the incomplete native check

A successful native Premiere frame export at 2.9 s verified that the overlay composited over the actual cameras and rabbit inset. [premiere-native-cad.png](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/premiere-native-cad.png) also exposed duplicated original captions. Creating the subsequence had re-enabled captions that were hidden in the working duplicate.

The final pilot's “Toggle active caption tracks” control was operated through the UI to hide the original captions again. Caption display could not be reliably read or changed through the tested Premiere scripting DOM. Consequently, creating a subsequence required its own visible inspection.

The subsequent native frame export failed with `bridge_unavailable`. A sequential orchestration batch improperly continued into one further native WAV/video export attempt after that result; it also failed. Those attempted files were `pilot-audio-verified.wav` and `AF-Kinetic-Pilot-v01-Premiere.mp4`; they were **not completed deliverables**. The repeatable workflow should stop dependent native calls immediately on the first such failure rather than continue a preassembled batch.

AE independently deleted the TEST proof comp and saved successfully. Premiere's save call returned success at **19:22:38.828 UTC**. The following connection verification still failed. No further Premiere editing calls were made after that failed verification.

Thus the record supports: saved pilot construction, successful earlier native overlay frame, and an executed UI caption-toggle action. It does **not** support a fresh successful native frame or full native MP4 export after the final caption toggle. A filename containing “verified” is not proof when its associated operation failed. The handoff explicitly asked to reopen **Window → Extensions → MCP Bridge** before further native work.

## 12. Independently check rendering and repair the review audio

Independent QA fully decoded both original assets with FFmpeg `-xerror`. The alpha was inspected across all 600 frames at 960×540 sampling resolution. Every nonblank artwork frame retained transparency and every canvas edge was transparent. Aggregate nonzero-alpha bounds were [63,343,407,509] at that sampling size; maximum artwork coverage was 5.074%. The intentional transparent gap was frames 411–419.

Frame quadruplets checked the frame before, at, one after and three after key entrances. No at frame 0; CAD at 152; BENCH and its expanded plate at 164; until at 186; ASTRA at 242; ENGINEERING at 440; still at 464; Definitely. at 562 all matched the input onset table. These checks proved rendered timing against the chosen manifest, not independent phoneme accuracy. [Entrance evidence](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-onset-quadruplets.jpg), [alpha QA data](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-alpha-qa.json), [4 fps preview sheet](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-preview-4fps.jpg).

The rendered preview's audio needed a separate correction. An initial downsampled check detected about 21.3 ms of lag. Six independent 48 kHz waveform windows spanning 0.25–9.5 s each measured **1024 samples late**, 21.333 ms, with correlations 0.99931–0.99980 after shifting. This would make the text appear about 1.28 video frames early in the preview. The problem was consistent with AAC encoder priming in the AE export; it did not affect the silent alpha overlay.

The repair did not move Premiere clips or apply a blind 1024-sample offset. FFmpeg stream-copied the already rendered video and replaced only its audio with the native WAV:

```sh
ffmpeg -i AF-Kinetic-Pilot-v01-PREVIEW.mp4 \
  -i dialogue-first10.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy \
  -c:a aac -b:a 256k -ar 48000 \
  -movflags +faststart -shortest \
  AF-Kinetic-Pilot-v01-PREVIEW-SYNCED.mp4
```

The same six-window test then measured **zero-sample lag** in every window, correlations 0.99895–0.99995, and the corrected file passed a full decode. The raw AE preview was preserved under `references/AF-Kinetic-Pilot-v01-AE-RAW.mp4`; the validated synced file was promoted to [AF-Kinetic-Pilot-v01-PREVIEW.mp4](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/AF-Kinetic-Pilot-v01-PREVIEW.mp4).

[Original lag confirmation](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-preview-audio-lag-confirmation.json) and [corrected audio QA](/Users/hendrikkrack/Documents/recording-studio/outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/references/pilot-preview-audio-synced-qa.json) record the measurement. The latter retains the temporary “PREVIEW-SYNCED” source filename because it was written before promotion. These are numerical comparisons; no full subjective listening review was claimed.

## 13. Deliver the pilot and preserve what still needs review

The user received the corrected 1080p preview, editable AEP and Premiere sequence name. The handoff explained that camera and microphone tracks remained separate, and that text content, positions and onset times were individually editable. It disclosed the unresolved final native verification.

The side question about exporting the main episode was answered with [Adobe's Media Encoder background-export documentation](https://helpx.adobe.com/sg/premiere/desktop/render-and-export/export-files/export-directly-to-adobe-media-encoder.html). Media Encoder 2026 was installed, but **this task did not queue or complete a main-episode export**.

The resulting reusable pattern was: inspect original moving references; export the current native edit; choose and retain word timing evidence; establish fixed whole-phrase layouts with actual font metrics; use direct word reveals, selective plates and sparse underline keys; supply native editable text plus a silent alpha overlay; retain native camera/mic lines; test the actual final files and preview audio; document any verification boundary.

For the next iteration, reopen and verify the Premiere bridge, confirm the pilot's caption display in a fresh native frame, and review the uncertain until/Astra and engineering/still arrivals with the user. Extend the pattern beyond ten seconds only under the next requested scope.
