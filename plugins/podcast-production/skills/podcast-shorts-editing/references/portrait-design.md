# Portrait design and native architecture

Use this when building the picture, typography and editable composition of a standalone podcast Short. The accompanying [portrait-layout.json](../assets/portrait-layout.json) records the approved eight-clip design as an adaptable starting configuration. It is a layout specification, not an executable AE importer or a platform-wide safe-area standard.

## The design the user approved

Give a complete spoken idea a stable visual structure: a concise editorial hook above a substantial speaker panel, a small speaker identity below the panel, and speech-timed phrase captions below that. Replace the hook with a few meaning-driven chapter headings as the argument develops. A thin orange line and quiet progress indicator provide rhythm; the speaker remains the main event.

This treatment used warm charcoal, cream and orange, Plus Jakarta Sans SemiBold, IBM Plex Mono and a small official CodeRabbit logo. Use the current project’s approved brand fonts and accent when adapting this architecture; orange and the named fonts describe this CodeRabbit example. All authored type sits outside the picture, respecting the user's preference that typography never cover the speaker's face or body. Speech alone carried these eight clips; music was not added automatically. The user specifically approved these Shorts and requested the architecture be reusable. That is evidence of creative preference, not measured audience retention or a guarantee of platform performance.

Keep two text roles distinct:

- **Editorial heading:** an accurate summary or question that explains the point of the passage. It is not presented as a verbatim quote. Change it when the spoken idea changes, not at a fixed visual timer.
- **Spoken caption:** a supported transcription whose words arrive with speech. Emphasize important words in orange only when they are spoken. Do not reveal a claim prematurely simply because the static heading makes it attractive.

## Verified portrait geometry

The final build used 1080×1920 pixels, square pixels and the source rate of exactly 30000/1001. The chosen picture panel is **1080×1000 at x=0, y=330**, with its nested layer centered at `[540,830]`. Early framing studies proposed square and 1080×1150 panels; those proposals are not the delivered layout.

Text coordinates below are AE **point-text anchor/baseline positions**, with anchor `[0,0]`; they are not glyph bounding-box top-left coordinates. Measure actual native bounds after applying the real font.

| Element | Position / size | Type and behavior |
|---|---|---|
| Full canvas background | `[0,0,1080,1920]` | Opaque warm charcoal |
| Series label | `[72,115]`, 24 px | IBM Plex Mono; persistent |
| Brand logo | center `[827,103]` | Delivered asset 2152×313 at 10%, producing about 215.2×31.3; fit a replacement by desired display dimensions rather than blindly copying 10% |
| Opening heading | `[72,204]`, start at 68 px | Plus Jakarta SemiBold; two deliberate lines; max measured line width 880 |
| Later heading | `[72,204]`, start at 53 px | Width-fit downward; one delivered long heading used 49 px |
| Heading context line | `[72,266]`, 26 px | Muted Plus Jakarta; optional, start with later beats; max width 880 |
| Heading accent | `[72,300]`, height 5 | Orange solid; width 120 initially, then `120 + beat_index × 76` in this example |
| Camera panel | `[0,330,1080,1000]` | Clipped by a nested portrait precomp |
| Active speaker label | `[76,1385]`, 25 px | Muted IBM Plex Mono; name / organization or moderator role |
| Phrase captions | `[76,1476]`, 60 px | Plus Jakarta SemiBold; at most two rows; max line width 874 |
| Progress line | `[76,1630,858,3]` | Orange; anchor `[0,1.5]`, position `[76,1631.5]`, X scale 0→100 over the clip |
| Footer | `[76,1700]`, 21 px | Muted IBM Plex Mono; episode / full-conversation cue |

Base text is left aligned, tracking 0, no stroke, manual leading `font_size × 1.24`. The main font was selected as `PlusJakartaSans-SemiBold` with variable weight axis `wght=600`; mono was `IBMPlexMono`. Verify installed font identities instead of substituting a similarly named family silently. The RGB floats in the configuration are the authoritative colors; hex values are rounded reference values.

This leaves generous bottom space and more right margin around important text than a full-width caption. Check current destination UI overlays and a realistic phone-size view; the geometry was not certified against every social platform's controls. Do not shrink long captions until they become unreadable just to preserve this template. Regroup or rephrase an editorial heading first, and preserve verbatim meaning in captions.

## Camera panels and framing

Use accepted, graded angle precomps as source dependencies. In the validated case those sources were already display-referred 1920×1080 Rec.709 media with native angle corrections. No second log conversion was needed. Camera geometry and grade are separate decisions: reproduce the panel architecture, but inspect each new recording's framing and actual color pipeline.

Each camera gets its own **1080×1000 portrait precomp**. For these source precomps, the anchor was `[960,540]`:

| Panel role | Source | Position inside portrait panel | Uniform scale |
|---|---|---|---:|
| First single | First founder camera | `[540,500]` | `1000/1080 × 100 = 92.5925926%` |
| Second single | Second founder camera | `[632.5925926,500]` | 92.5925926% |
| Moderator portrait | Wide camera, separately reframed | `[555.5,345]` | 155% |
| Shared wide | Wide camera | `[540,500]` | 56.25% |

The singles use the original full source height and retain about 1166.4 source pixels horizontally. The second single is shifted to fit the actual seated person. These shifts are **episode-specific examples**; identify speakers and sample their gestures before reusing them. The stronger moderator crop uses already-HD footage and needs its own sharpness/framing proof. A centered crop of a three-person wide can otherwise select the wrong person.

At 56.25%, a 1920×1080 wide becomes 1080×607.5, centered vertically in the panel. Its unused top and bottom areas **must be opaque**, with a full 1080×1000 background below the wide footage inside that precomp. Transparent letterbox bars allowed the underlying close-up to show through in the first pass. The final project repaired this, and targeted before/during/after join frames confirmed the corrected composite.

Use a bounded precomp or mask to enforce the panel; a transform alone does not clip a source to the intended rectangle. Avoid automatic punch-ins for every sentence. Sample the opening, middle, ending and important gestures for each selected passage. A framing contact sheet is a sample, not proof that all continuous gestures remain visible.

## Editable project structure

Keep one final portrait composition per Short and reusable graded angle / portrait-panel precomps. Resolve current source items by verified names or inspected IDs when building; native IDs from an old project or session are not portable.

Use names that expose the topic, speaker and visible phrase without requiring the editor to interpret a cue log. Keep stable IDs for automation in the manifest or a short prefix; descriptive names are the human navigation layer. For example:

```text
SHORT 03 • <topic> • portrait • v02
  AUDIO • <speaker> speaking turns • SHARED MIX
  FOOTER / PROGRESS
  CAPTION 001 • <speaker> • <opening words of phrase>
  SPEAKER 01 • <name / role>
  EDITORIAL 01 • <heading> / CONTEXT 01 • <phrase> / ACCENT 01
  BRAND / SERIES
  HANDOFF 02 • synchronized wide
  JOIN COVER 01 • synchronized wide
  CUT 01.01 • <speaker> CAMERA
  SOURCE 01 • <camera> • alternate angle   [disabled]
  BACKGROUND • warm charcoal
```

Use consistent native label colors for each speaker across related compositions, captions and speaking-turn audio, with a short legend in the handoff index. Retain text labels so color is not the only identifier; a speaker color does not imply an isolated microphone. Keep the final review composition easy to find and distinguish it from source, design and superseded compositions. When changing an existing naming scheme, update any name-based automation rather than silently breaking it.

This is a logical organization, not a requirement that incidental list ordering equal exact AE stacking. Keep graphics above picture, cut and cover layers above disabled alternatives, and backgrounds below their pictures. The built rectangles and lines were native **solid layers**, while captions and headings were native **text layers and animators**. Do not describe them as baked PNG text or claim unbuilt vector diagrams.

For every retained source span, preserve independent disabled wide and single-camera alternatives. Add enabled speaker-camera layers for the actual turns, and keep source camera audio disabled. Store the clip's source/program map once and use it for all angle layers. Apply `startTime = program_in − camera_in` **before** final `inPoint` / `outPoint` trims; changing start time later can move the trims.

The validated build covered a new source-span join with 0.8 seconds of synchronized wide, and speaker handoffs with a 0.7-second wide centered on the turn boundary. These are starting values, not mandatory cuts. Use a real simultaneous wide from the correct source interval; inspect whether the insert helps the exchange. Bound a cover to its owning source span so it cannot reach into a removed segment. Do not use a wide to disguise a misleading change in argument or fabricate a reaction from another moment.

Speaker labels change on the verified turn map. Turn-separated audio layers remain explicitly labeled **SHARED MIX** when that is their origin; the visual presence of separate tracks does not make them isolated microphone recordings. Keep their summed dialogue reference available without playing a duplicate combined mix alongside them.

## Native speech-timed captions

The implemented phrase builder starts a new group at an explicit boundary, after seven word entries, or after a gap greater than 0.6 seconds. It closes a group on explicit instruction or sentence-ending punctuation after at least three entries. It wraps by actual font measurement at 874 pixels; a 60 px start size is reduced by 2 only if more than two rows result. All 374 delivered caption layers stayed at 60 px. Use manual group boundaries to avoid bad syntax breaks; “seven entries” is a heuristic, not an editorial goal.

For each phrase:

1. Map word source timestamps to the current program timeline after all cuts. Keep the full phrase text in a fixed layout, so revealing words does not reflow earlier words.
2. Start the layer at `ceil(first_word_onset × fps − ε) / fps`. End no later than the next phrase or clip end, with a 0.3-second hold after the last word and a 0.2-second minimum phrase duration where available. Quantize the final boundary consistently to the frame grid.
3. Add native text animator **Spoken word reveal**, opacity 0, range selector based on **words**, selector smoothness 0. Animate range start from the cumulative revealed-word percentage toward 100%; leave range end at 100%.
4. Put a **hold** key at each word's upward-quantized onset, using cumulative token counts. Whole words appear at speech onset; do not interpolate partial character fades between onsets. Multiple words landing on the same frame share the final cumulative reveal for that frame.
5. Apply the approved accent color (orange in the worked example) to selected character ranges inside that same text layer. The reveal still governs their visibility, so an emphasized term does not arrive early. Choose a per-clip vocabulary, not a universal brand/keyword regex. Preserve qualifiers around emphasized numbers.

The verified AE property mapping was `ADBE Text Opacity = 0` on the text animator, `ADBE Text Range Type2 = 3` for word-based selection, `ADBE Text Selector Smoothness = 0`, and hold-eased keys on `ADBE Text Percent Start`. These are observed property names/values, not permission to bypass the current bridge schema. Inspect the current catalog and native readback before reusing them.

ASR supplies estimated onsets, not phoneme proof. Check audible entrances, fast phrases and new joins. If a phrase is uncertain, preserve the sound and show only supported selective keywords when appropriate; do not fabricate a fluent subtitle. Label any such accessibility limitation in the caption/source notes. The delivered design used this deliberately for a brief uncertain exchange about codifying taste.

Heading and context changes used a restrained 12 px upward move over five frames, with ease-out at the arrival key. The opening heading was static. The progress line ran linearly from X scale 0 at frame zero to 100 on the final frame. These cues organize the argument; they should not compete with faces or force cuts to a beat unrelated to the speech.

## Prove one example before multiplying it

Build a representative 5–10-second native proof that includes a caption reveal, headline/context change, a speaker camera and an actual wide insert if the set uses them. Inspect at intended phone scale, then measure native text bounds. Test a long heading and a two-row caption before duplicating the structure. In the approved batch, native readback checked 462 text layers with no recorded layout violations, alongside sampled rendered frames; this did not replace continuous motion review.

After scaling, inspect every clip's opening, meaning beats, labels and ending. Add before/during/after frames for **each source join and speaker handoff**: opening and midpoint proofs alone missed the transparent-wide error. Preserve the previous good native project and render when repairing a limited range. Detailed delivery and resource checks belong to the workflow's rendering references.

Evidence for this specification: final `native_shorts.py` and `build_shorts.py`, `shorts-manifest.json`, native layout/readback records, framing study and production audit, opening/beat contact sheets, and final boundary/visual-review records. The portable configuration intentionally omits recording paths, participant identities, native IDs, private transcript text and episode-specific color corrections.
