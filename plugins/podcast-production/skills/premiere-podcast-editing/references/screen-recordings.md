# Screen recordings and demonstrations

Use this mode to add screen captures or gameplay to an existing podcast while retaining its camera edit, microphone isolation, manual mute automation, content removals, and mix. It also covers native Screen Studio styling/export when requested. An already suitable silent video can be used directly; routing every source through Screen Studio is unnecessary.

When the user wants a talking-head camera over these cutaways, read [presenter inset](presenter-inset.md) for visual-example matching, synchronized nest bounds, the protected-audio pilot, and chart/HUD occlusion checks.

## Establish the source and its purpose

- Inspect the current sequence and current recorder-to-program keeps. Old markers become stale after head trims or content removals. Preserve camera and audio state, and sequences outside the requested scope.
- Inventory raw screen video, its separate raw microphone, saved project metadata, and existing exports. Probe timestamps, duration, rational frame rate, dimensions, sample/display aspect, and audio streams. Low average frame rate can reflect a sparse screen recording; use actual timestamps.
- For article/chart stills, verify content, qualifiers, aspect, and readable native framing. Stills need no audio-clock fit or video remux. Use their actual source context and deliberate timeline holds.
- Sample actual content around the relevant dialogue. A matching brand or broad topic does not prove that a board, chart, model, game version, or viewpoint is the demonstration being discussed. Do not substitute unrelated footage for missing material. Keep cameras when correspondence is absent.
- Separate demonstrated synchronization from an explicitly supported illustration. Audio-bearing footage can be unrelated to the podcast; silence or muting the source does not resolve an editorial mismatch. A silent edited video may need independent visual anchors for each section.
- Before changing a Screen Studio treatment, duplicate the source package into a working area and verify the opened path. Preserve intentional source trims, slice speed, zooms, and cursor behavior. Compare those saved values before/after; an empty original slice list may become an equivalent explicit full-range slice.

## Keep the demonstration visible throughout its discussion

The user's explicit editing rule is to keep the synchronized screen or gameplay continuously visible while the speakers discuss its onscreen actions, results, charts or table rows. Return to full-screen faces when the conversation moves to an unrelated topic. A sentence boundary, short pause, reaction or explanation of the same result does not end the screen passage. Keep presenter reactions in the requested inset while the demonstration stays visible.

Read the surrounding dialogue to establish the whole demonstration span, including setup, pointing, numerical explanation and follow-up. Short isolated cutaways can be individually correct yet leave viewers unable to follow the discussion. For static article evidence, hold the verified same chart/table through its explanation and switch assets at the actual reference change; retain qualifications. A still cannot demonstrate an interactive action. If the corresponding footage is missing or ends, document that gap and use the authorized fallback rather than inventing continuity or repeating gameplay as if it were live.

Inspect the current native program frame and every contributing visible layer before diagnosing what viewers see. Track labels, old manifests, source thumbnails and a correct clip on one layer do not establish the final composition: an enabled foreground above it can obscure or replace it. Check actual start/middle/end frames and meaningful screen-state changes across each extended span.

## Keep the clocks distinct

For raw screen time `s`, recorder time `r`, and native-export source time `e`:

```text
r = a*s + b
s = (r-b)/a
e = p*s + q
e = p*(r-b)/a + q
continuous playback speed percent = 100*p/a
```

Use piecewise mappings when the screen project has trims, gaps, or speed changes. A saved `timeScale=1/24`, for example, makes exported time advance at one twenty-fourth of raw source time; the export cannot be treated as realtime raw footage.

For waveform matching, use raw capture microphone audio and aligned recorder ISO references. Use [sync and audio](sync-and-audio.md) for coarse envelope search, signed waveform correlation, dispersed fit anchors, holdouts, drift, and coverage. Retain polarity: a strong negative match can be correct. Compare both people’s own microphones and competing room-bleed peaks; several milliseconds of propagation difference must not be mistaken for clock drift. Keep practical audio uncertainty separate from unmeasured visual capture latency.

Test the native export against its own raw capture audio as a separate operation. Distributed early/middle/late windows can establish its rate and offset. A sped-up or trimmed export needs its expected source mapping, not a near-zero-offset test. For silent or heavily retimed footage, combine saved slice/frame timing with corresponding visible events. Static picture matches support content correspondence, not subframe event timing.

Never invent a coefficient for an unsupported match. Record tested ranges, competing candidates, confidence, and limits. A wall-clock date is supporting metadata, not a replacement for source evidence.

Map each planned insert through the current program keeps. Snap program boundaries to the sequence’s rational frame grid, then derive export source bounds from those snapped times using full-precision coefficients. Preserve the live capture clock throughout continuous demonstrations. If an unrelated-topic camera return is appropriate, recalculate source time on returning to the screen rather than resuming the previous source out-point. Preserve elapsed time when using a 60 fps source in a 59.94 fps sequence; frame-rate reinterpretation changes playback speed.

For silent footage with supported visual anchors, an editorial retime can keep a demonstration visible while aligning viewpoint changes. Label this as visual correspondence, not waveform synchronization. Preserve the original source and the camera/audio clocks. In the September 2026 native NIGHTSHIFT repair, the speed setter reported success but produced the wrong timeline duration. Read actual `getSpeed()` and all four bounds; do not repeat the speed command on an already retimed clip. In that runtime, native in/out used the retimed clock: `original source seconds = native in/out seconds * actual speed`. Explicitly setting that clock's in/out and the exact program start/end corrected the two ranges, then native frames and a bounded Premiere review verified the result. Treat these semantics as a measured case to pilot on another version, not a universal API guarantee.

## Style and export only as required

Use the requested app/preset and delivery settings. A preset’s Auto canvas can differ from an explicitly requested wide canvas. Verify background, padding, canvas aspect, readable framing, and cursor/zoom behavior on the working project. Episode-specific choices such as a named orange preset or Studio quality are not defaults for another podcast.

Export natively when the result needs Screen Studio’s cursor animation, zooms, and styling. Record the project/output pair before starting. Different projects can queue behind an active render; opening another project does not prove completion. Track jobs separately rather than resubmitting them.

Wait for the final file to have a complete MP4 structure and a closed writer/stable size before moving, probing in depth, or decoding it. A growing file or absent `moov` can be normal finalization. If the UI is busy, permitted read-only process/file diagnostics can establish progress: fragmented MP4 headers can reveal completed media time without decoding picture. Render progress is not a completed export. Poll sparsely, respect the requested time bound, and do not change app internals to bypass a modal.

Probe the completed file’s actual dimensions, frame count, duration, timestamps, aspect and color metadata. A nominal 4K export can be a few pixels narrower than 3840; do not reuse another file’s scale correction. Moving a completed export to the agreed output area should preserve its content and avoid overwriting an existing file.

## Protect podcast audio at import

For an audio-bearing screen export, make a video-only derivative before insertion. In the inspected Premiere MCP implementation, `linkAudio:false` removes linked audio **after** insertion; embedded audio can overwrite a microphone track before cleanup. The flag is not preventive video-only editing.

A suitable MP4 can be remuxed without re-encoding:

```sh
ffmpeg -hide_banner -loglevel error -n -i 'native-export.mp4' \
  -map 0:v:0 -c:v copy -an -sn -dn -movflags +faststart \
  'native-export_VideoOnly.partial.mp4'
```

Probe the candidate for one video stream and zero audio streams. Compare every video packet’s payload hash, PTS, DTS, duration, size, flags, and count with the native export before publishing the derivative. A changed container hash is expected; changed picture payload/timing needs investigation. Retain the original export for audio QA.

An already suitable source with zero audio streams needs neither this remux nor a new encode. Use it directly or make a verified copy to the agreed media location. Preserve its declared aspect and timing. A file copy can be checked with a full-file hash; a remux requires packet/timestamp comparison because its container changes.

## Calibrate native interpretation and framing

Check the imported item’s actual path, frame rate, and pixel aspect. Do not change interpretation when it is already correct. Any necessary interpretation correction affects every use of that item; keep it limited to the intended new source and verify the native result.

Preserve displayed geometry, not merely coded width/height. For example, a tested 1920×1080 video declared SAR `972:1117`, making displayed content approximately 1.547:1. Its correct image belongs inside a wider canvas with margins; treating its pixels as square would widen it by about 14.9%. A square-pixel export is valid if that aspect has been baked into the content geometry.

Native imports may already be conformed to the sequence. Inspect an actual native frame before deriving Motion Scale from source/sequence resolution. In one tested UHD sequence, the 1080 source already fit the full height at numeric Scale 100%; 200% doubled the zoom. The chosen 91.3% produced a modest inset. These are observed case values, not settings to apply to another source. A background image’s fill scale is a separate calibration.

Resolve the exact `Motion` component and numeric `Scale` property. A tested generic getter conflated `Uniform Scale`, `Scale Width`, and `Scale`, returning Boolean `true` for scale. Require a finite numeric read and preserve the distinct Uniform Scale Boolean. Compare a float32 Scale readback with a small percentage-unit tolerance, such as `1e-4`, rather than strict decimal equality. Tick strings, counts, Booleans, and zero-amplitude mute values remain exact; do not apply this Scale tolerance to unrelated properties.

## Place overlays and verify the existing edit

Use fresh sequence, project-item, and clip IDs. Take a current protected-state snapshot and save a checkpoint before insertion. Keep camera clips underneath overlays; add or reuse only the video layers needed for this treatment, independently checking video/audio track counts.

Pilot an overwrite into an intended empty overlay interval. Avoid a ripple insert that moves the edit. Read all four native bounds after placement:

```text
clip.start.ticks      program start
clip.end.ticks        program end
clip.inPoint.ticks    source in
clip.outPoint.ticks   source out
```

Use exact `Time.ticks` for frame-bound corrections. Some source-mark APIs use decimal seconds, silently retain old marks after failure, or return timeline bounds under misleading source-field names. A success flag does not establish correct bounds. Inspect the new clip, guard against stale state, and correct only that clip instead of blindly repeating insertion. A failed guard may be a float serialization difference; distinguish that from a real source/timeline mismatch.

Apply only required new-overlay effects/transforms. Verify native picture and fit, not just setter/readback success. Then compare protected camera clips, microphone bounds, Level/Mute keys, and mixer settings. Public snapshots may omit master inserts, transitions, or nested sequences; inspect relevant saved/native state separately. A checkpoint comparison is not a final rendered-program QA result.

After any ripple cut, head trim or content removal, derive the recorder-to-program mapping again from the surviving native microphone clips. Audit **all overlay tracks**, including backgrounds, screen foregrounds, stills and presenter insets, against those current keeps. A shifted background does not prove its foreground moved; stale foregrounds can remain at old program times or become stranded beyond the audible edit. Check source correspondence, paired-layer boundaries, unintended gaps/overlaps and every clip beyond the current audio-program endpoint. The sequence's reported end may itself be extended by a stranded overlay, so it is not sufficient evidence of the intended program end. Repair only identified stale clips, then recheck the actual visible composition and protected audio.

Batch only after a successful pilot. The tested batch API can continue after individual failures and has no rollback, so inspect every result and every clip’s four bounds. Do not automatically repeat a partial batch. Await each command/tool session and inspect its final exit status; an empty yielded `exec_command` response is not completed script output.

For handoff, record the current insert manifest, verified source/export clock maps, actual media probes, video-only/copy evidence, native bounds, protected-state comparison, and representative rendered edges/returns to faces. Report listening, visible review, and full-episode rendering only when each actually happened. Keep incomplete assembly or final QA explicitly pending.
