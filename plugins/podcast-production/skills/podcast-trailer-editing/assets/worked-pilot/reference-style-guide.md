# CodeRabbit kinetic typography — reference inspection

Inspected the user's supplied video files with FFmpeg and viewed extracted frames. This is a visual analysis, not a claim of access to the original title layers or an identification of the exact embedded font files.

## Sources and coverage

- **NVIDIA-Podcast-Trailer.mp4**: UHD 3840×2160, 30000/1001 fps, 65.966 s. Contact sheets cover 0–60 s. Dense samples cover 0–3 s and 5–8 s at 10 fps, plus every source frame around 0.25–0.85 s. This is the strongest motion/type reference.
- **Merge - Episode 3 trailer v02.mp4**: 960×540, 30000/1001 fps, 72.673 s. Contact sheets cover the whole clip. There is **no visible kinetic dialogue text** in the examined footage; only the end logo/title animation. Use it for conversational pace, shot variety, and the CodeRabbit end-card language, rather than as evidence of word animations.
- User's second screenshot: a strong lower-left editorial stack — small sentence, much larger **3.5 MILLION**, smaller italic **daily actives** — supports more pronounced hierarchy and placement in available space than the usual centered captions.

## What the NVIDIA footage actually does

1. **Words reveal into a prepared phrase layout.** They do not recenter or reflow the words that already appeared. Whole words appear at their spoken moment; existing words remain static. The inspected every-frame entrance shows an effectively instantaneous reveal, not a noticeable slide or bounce.
2. **The phrase builds and then holds.** The first stack appears approximately: FASTER at the opening; MODELS at 0.4 s; ARE at 0.7 s; SMARTER at 0.9 s; MODELS at 1.2 s. The complete stack remains for about two seconds. These timings are visual estimates from extracted frames, not forced-aligned audio measurements.
3. **Hierarchy creates the motion impression.** Supporting connectors are roughly half the cap height of the principal words. Weight, case, and italic styling vary. A phrase usually occupies two to four rows, not a long single subtitle line.
4. **Emphasis is selective.** White dominates. Significant nouns such as THE MODEL, CODEX, and CLAUDE CODE get a solid orange rectangular background. Rectangles have square corners and close but comfortable padding. They grow when additional words in the same highlighted phrase arrive.
5. **There are intentional quiet gaps.** The first complete phrase clears around 3 s, leaving the speaker visible until the next build near 5 s. Do not fill every silence with text.
6. **Placement can adapt to the shot.** Most stacks sit lower-middle over the torso, roughly x=0.25–0.75 and y=0.55–0.94 of the frame, keeping the face clear. The comparative FASTER/BETTER stack around 9–11 s moves to the left available space. A wide-shot caption can retain its layout across a camera cut.
7. **Legibility comes from a dark shadow/edge.** White small letters have a fairly visible dark outline or shadow, without a large full-caption black panel. Orange emphasis plates are opaque.
8. **The examined NVIDIA frames do not show underlines.** Underlining is a user-requested variation, so use it deliberately in the pilot rather than describe it as copied from these frames.

## Measured visual anchor

At the extracted 1920×1080 frame from 5.6 s:

- THE MODEL orange rectangle: approximately x=578–1342, y=660–807; 764×147 pixels.
- Main letter cap height: about 85 px; connector EVEN IF cap height: about 44 px.
- Orange interior's most common decoded RGB: **253,86,8 (#FD5608)**. This is a decoded video measurement; use the established CodeRabbit brand orange when available, with **#FF570A** as a close design default.
- Main plate width is roughly 40% of screen width; this is substantial title typography, not small subtitles.

## Proposed first-10-second pilot formula

These are implementation recommendations based on the reference and the user's requested fonts, not measurements of the original Premiere/AE layers.

- **Primary font:** Plus Jakarta Sans SemiBold. Use semantic emphasis and size to create weight hierarchy. Reserve IBM Plex Mono for smaller connecting phrases or technical wording such as CAD BENCH. Do not assume the supplied videos themselves used those exact fonts.
- **At 3840×2160:** primary keyword size approximately 180–240 px, secondary words 110–150 px, short connectors 76–100 px. Adjust to actual text width and the shot, keeping clear differences rather than every word the same size.
- **Lay out complete phrases first.** Give every word its final anchor position. Animate visibility at each measured audio onset. Previous words must not shift when the next word arrives.
- **Entrance:** direct reveal or a maximum 2–3-frame opacity/scale settle. If adding scale, keep it subtle (about 96% → 100%, no overshoot) and only on chosen emphases. Phrase exit can be a 2–4-frame opacity dissolve.
- **Screen position for the current host/rabbit shot:** prefer a lower-left anchored stack, starting roughly 7–9% of frame width from the left, with the right-hand rabbit image left unobstructed. Stay below the face. Keep the stack within about 55–60% of frame width while the picture-in-picture is present.
- **One strong emphasis per thought:** e.g. CAD BENCH in a large orange block; the key model name in large white type; one short underline to make the requested variation visible. Do not put orange behind every spoken word.
- **Underline:** a thin orange horizontal shape attached to its word; reveal left-to-right over 4–6 frames at 59.94 fps. This is a proposed variation, not an observed NVIDIA motion.
- **Keep literal word timings on the sequence frame grid.** Build words at their actual starts in the current edited audio. Do not reuse prior trailer clocks or evenly space words.
- **Preserve the footage, cut timing, audio, and rabbit insert.** Build this as a separate top graphic track/pilot version with editable text and shapes. Disable only the old captions/labels that duplicate the pilot words in those first ten seconds.
- **Review target:** one 10-second playback and a few still frames showing early, middle, and final builds; approve scale, placement, timing, and frequency of emphasis before extending the style.

## Contact sheets

Each sheet reads left-to-right, top-to-bottom. Files ending `-labelled.jpg` add approximate timestamps. FFmpeg fps sampling is periodic, so these are navigation labels, not exact title-in point measurements.

- `nvidia-first30-labelled.jpg`
- `nvidia-30-60s-labelled.jpg`
- `nvidia-0-3s-10fps-labelled.jpg`
- `nvidia-5-8s-10fps-labelled.jpg`
- `nvidia-models-entry-everyframe-labelled.jpg`
- `nvidia-orange-wordblock.png`
- `merge-first30-labelled.jpg`
- `merge-rest-2s-labelled.jpg`
