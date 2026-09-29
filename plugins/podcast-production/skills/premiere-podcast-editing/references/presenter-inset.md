# Presenter inset over screen demonstrations

Use this mode when the user requests a talking-head or picture-in-picture camera over existing screen cutaways. Preserve the requested corner, aspect and visible style, the camera's synchronization, and the established microphone edit. Do not add an inset to unrelated camera-only passages unless requested.

Follow the user's continuous-demonstration rule: keep the synchronized screen/gameplay visible throughout discussion of its onscreen actions or results, with presenter reactions in the inset. Full-screen faces return for an unrelated topic. Extend inset coverage when extending the related screen passage; a previous set of sparse cutaways is not the limit of the requested coverage. See [screen recordings](screen-recordings.md) for the dialogue and source checks.

## Preserve and interpret the visual example

The user's inspected example is stored at [assets/presenter-inset-user-example.png](../assets/presenter-inset-user-example.png). It is the unchanged original screenshot, including Premiere UI; use its program image as a visual reference, not as output footage. SHA256: `562b5c572e0f732ad307db50433877bcc0b8aefe727ea068889c5a0f2027c663`.

A [native program-frame example](../assets/presenter-inset-native-example.png) is also stored unchanged, without Premiere UI. This is a sampled native frame, not evidence of a full watch. The user screenshot shows a rectangular, uncropped host angle at the top right over a Fable comparison table. The UI rounds its Scale to 46% and Position to 3350.8,289.8. More precise native property reads for this same example are:

| Property | Verified example value |
| --- | --- |
| Program dimensions | 3840×2160 |
| Host angle nest dimensions | 1920×1080 |
| Position, normalized native property | `[0.87260282039642, 0.13414631783962]` |
| Position converted to program pixels | Approximately `3350.7948, 289.7560` |
| Host numeric Motion Scale | `45.8126487731934%` |
| Guest and main/wide numeric Motion Scale | `22.9063243865967%`, verified in native frames to produce the same physical inset size |
| Derived visible rectangle | Approximately `879.6029×494.7766` pixels, 16:9 |
| Derived top/right margins | Approximately `42.3677` / `49.4037` pixels |

These are case measurements, not universal defaults. Match the visible proportions and margins when the user requests this saved style. For another reference, preserve a durable copy and record output dimensions, source/nest dimensions, anchor, crop, position units and native scale before reproducing it. Do not depend on a temporary clipboard path.

A property exposed as normalized coordinates must not receive pixel coordinates, or vice versa. Inspect the actual property representation and verify the native frame. Resolve exact Motion/Position/Scale properties; the generic Scale getter can conflate numeric Scale with Uniform Scale. Do not substitute the rounded UI 46% for the verified native value above.

The native pilot verified that host Scale `45.8126487731934%` and guest Scale `22.9063243865967%` produce the same physical inset at the example Position. Uniform Scale remained true; the separate Scale Width property read 100 after setting Scale, while rendered pixels were correct. Do not force that width property to equal uniform Scale or treat its 100 value as failed sizing. The final native I02 frame and native property readback also verified main/wide Scale `22.9063243865967%` at that same physical size. Other nests may have different dimensions or an existing conform/transform: compare each distinct nest type in a native frame before transferring settings. Rendered physical size is stronger evidence than assumed source-pixel arithmetic.

## Map synchronized camera picture

Use the camera choice requested by the user. When following the existing camera edit, intersect each screen interval with its actual camera clips and preserve their source clocks. For an unretimed camera clip:

```text
inset source in = camera source in + (overlap program start - camera program start)
inset source out = inset source in + overlap duration
```

Use exact native ticks and the current sequence frame grid. Include the actual source-rate mapping for retimed clips. Do not start every inset at camera source zero, pause its clock over camera returns, or use a frozen image where live speaking video is intended. Keep the graded source nest so the inset receives the established grade once.

Place inset picture above all screen foreground/background layers, leaving the existing camera edit below them. A single screen interval may need several inset clips when the requested camera selection changes; distinguish screen-cutaway count from inset-clip count. Preserve intentional small holds and speaker logic rather than reacting to every breath or backchannel.

## Require a protected-audio pilot

Before the first nested-camera insertion, save a checkpoint and capture the protected camera, microphone, manual Mute/Level and mixer state. **Lock every protected podcast audio track and verify those locks before the pilot.** In the tested native API, use `track.setLocked(1)` / `setLocked(0)`: Boolean `true` was rejected as an illegal parameter type. Confirm the actual interface on another version. Keep them locked while performing the new inset insertions; record prior lock states and restore them after verification.

An angle nest that appears to have no audio can still insert an empty linked audio clip. Do not infer safe insertion from an empty nested audio track or `linkAudio:false`: in the inspected bridge, linked-audio cleanup happens after insertion, so it is not protection against overwriting a microphone clip.

Pilot one bounded overwrite on the intended new video layer, then inspect exact program/source bounds, source identity, enabled/online state, all resulting audio clips and track-count changes. The tested nested insertion created another empty audio track each time, even when an existing empty Audio4 was present. `linkAudio:false` removed the new linked clip after insertion, but the extra track remained. Read back each track and delete only newly created, verified empty tracks, in descending index order, with `delete_track`; retain every original track, including original empty ones. Identify any unwanted linked clip exactly before cleanup. Never remove or replace an existing microphone clip. The two-insert native pilot restored the original three audio tracks and matched all 2,471 audio keys and the entire bonus state. This verifies that pilot, not later batches. If a guard or comparison fails, resolve it before proceeding; uncertain insertion is not a reason to repeat it blindly.

## Keep screen information readable

Inspect the composition against actual first/middle/last frames and relevant cursor zooms, window changes and HUD states. Check chart model labels, axes and qualifications, table headings/footnotes, cursor targets, minimaps and controls involved in the spoken demonstration. A clear face does not make an obscured table acceptable.

The earlier inset pass inspected native midpoint frames for its 18 screen intervals. This establishes sampled layout quality, not continuous coverage of the full discussion or completion of a later continuity repair. The original comparison-table placement remains readable. The following asset-specific adjustments were applied and verified in those native frames, preserving the camera's top-right rectangle:

| Screen foreground | Native foreground adjustment in the 3840×2160 case | Visible result |
| --- | --- | --- |
| Cost table | Scale 90%; center `[0.5, 1200/2160]` | Complete upper qualification and all table rows remain clear |
| Sunhaven gameplay | Scale 86%; center `[0.5, 1210/2160]`; move video from V3 to V4, with a full-frame orange background on V3 (Scale 200%, centered) | Money, wanted stars, health, minimap and speed clear; start/middle/end frames additionally reviewed |
| NIGHTSHIFT gameplay, all three cutaways | Scale 76.5%; center `[1600/3840, 0.5]`; retain source pixel aspect | Full minimap, bottom abilities and notifications clear |
| Standalone decision-map still, later native check | Scale 75%; center `[1600/3840, 0.5]`; orange background centered and unchanged | Full Directional Data box, earlier-model legend, axes and bottom qualification clear; foreground sits wholly left of PiP |

Unchanged native-frame references are saved for the [gameplay layout](../assets/presenter-inset-gameplay-example.png) and [standalone decision map](../assets/presenter-inset-decision-map-example.png). The latter initially lost its top-right qualification and part of its legend behind PiP; the verified 75% left-shifted composition fixes that specific still while retaining the user's camera geometry. These images establish sampled content/framing only.

These scale numbers depend on the specific source/nest and conform state; reuse the method, then validate another asset's pixels. The article chart cutaways still cover ends of surrounding prose above the chart, while the graph, values and below-chart qualification remain visible. In the earlier live decision-map capture, the inset touches a decorative box edge while wording, legend and caveat remain clear. Its screenshot layout differs from the standalone still and does not establish that still's fitting scale. WESTLINE's sampled game state keeps its time, money, wanted stars, minimap, speed and police notification visible. Do not claim every dynamic HUD state was watched from a midpoint inspection, or automatically shrink every screen source.

Retain the user's inset corner and aspect where possible. For a demonstrated conflict, make the smallest asset-specific foreground adjustment over its background, preserving pixel aspect and all relevant content, then inspect a native frame. A geometry estimate is a candidate until the native picture is checked. Use direct suitable silent video and original stills without unnecessary ScreenStudio re-encoding; see [screen recordings](screen-recordings.md).

## Verify and hand off

Read back each new inset's four bounds, source identity, numeric transform, enabled state and online state. Check dense intended inset coverage only inside the requested screen intervals, with no extra camera sound. Recompare protected camera/audio/mixer/grade and bonus state; existing V1/V2 and screen layers remain protected except for explicitly authorized framing changes.

After ripple edits, inspect all visible layers against the current audio-source map and program endpoint. Recalculate presenter intersections from the surviving camera clips; never copy old program positions merely because the nested source still exists. Check that screen foreground, background and inset move together, and that no stale upper-layer clip hides the corrected screen or remains beyond the audible edit. Confirm the actual native program frame, not only a lower-layer clip's properties.

The earlier inset pass contained 39 inset clips (38 new plus the preserved user example) across 18 screen intervals; camera changes explain the differing counts. Treat this as historical scope evidence, not a template count or proof of later repair completion.

Save a representative native example for each validated nest geometry and any distinct screen/HUD remedy. Store its real settings and distinguish that evidence from the original user example. Export a bounded review when needed to exercise actual nest playback, synchronization and camera changes. Report sampled native review, rendered review, listening and full-episode review separately; do not claim a full watch or render from a few screenshots.
