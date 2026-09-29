# Native kinetic text workflow

## 1. Analyze references before designing motion

Probe each supplied reference with FFprobe. Extract contact sheets over its duration and dense samples around a representative word entrance. Inspect original-size frames for type hierarchy, placement, emphasis treatment, phrase holds, exits and motion. Keep direct observations separate from the proposed variation.

The CodeRabbit NVIDIA example used prepared phrase layouts, direct word reveals, stationary existing text, selective orange rectangles and intentional clear gaps. The user's Jesse Vincent screenshot supplied a small/large/small lower-left hierarchy. The Merge example supplied pacing and camera references; the inspected video did not establish kinetic dialogue text. Underlining was a user-requested extension, not an observed NVIDIA behavior.

Store a brief style guide and timestamped evidence. Do not copy branding details onto unrelated clients by default. User-specified fonts, colors and references take precedence over this example.

## 2. Snapshot and export the current pilot

Discover callable Premiere tools, verify the connection, read the current project/sequence, save, then duplicate the source. Use verified sequence IDs rather than relying on `activeSequence`, which can change as the user navigates. Record clips, source bounds, grades/nest identities, track mute/lock states and overlays.

Capture the desired range as picture and native PCM. In the worked Premiere 26.5 build, `Sequence.exportAsMediaDirect(outputPath,presetPath,1)` exported sequence in/out; range argument 0 exported the whole sequence. Set marks on the work copy or save/restore existing marks with a guarded operation. Confirm the actual exported duration and content.

Successful local preset suffixes under the actual Premiere application's `Contents/MediaIO/systempresets` were:

- `3F3F3F3F_57415645/Waveform Audio 48kHz 16-bit.epr`
- `4E49434B_48323634/High Quality 1080 HD.epr`

The second preserved the pilot's 60000/1001 frame rate at 1920×1080. Verify current installed files and output rather than assuming presets exist on another version. The HEVC Match Source preset returned `Error: -1` in this run; no cause was established. Do not confuse H264 Blu-ray's `48323642` directory with the working H264 exporter `48323634`.

If a required operation is not exposed, use permitted Premiere ExtendScript with current schemas. In this bridge, return data using `return JSON.stringify(result);`; a bare expression returned `undefined`, and returning an object became `[object Object]`. Helpers such as `__findSequence` were not available inside arbitrary execution. A bounded explicit lookup worked:

```javascript
var seq = null;
for (var k = 0; k < app.project.sequences.numSequences; k++) {
  var candidate = app.project.sequences[k];
  if (candidate.sequenceID === requestedId) { seq = candidate; break; }
}
if (!seq) throw Error('Requested sequence missing');
return JSON.stringify({id: seq.sequenceID, name: seq.name});
```

This is a pattern; derive `requestedId` from current reads. Do not execute placeholder IDs or broad unguarded mutations.

## 3. Derive and review word timing

Run a word-timestamp transcription against the current native pilot WAV. The example used local Whisper large-v3-turbo with English, FP32 CPU, `condition_on_previous_text:false`, and `word_timestamps:true`; base.en provided an independent text/boundary comparison. Another reliable timestamp source is acceptable.

Preserve actual wording. Record each word's source seconds, chosen frame, uncertainty and final phrase membership. Quantize once with the rational frame rate. Two models agreeing on the words does not prove their onsets are exact; pauses can be absorbed into “until” or a model name. Review uncertain words in context and keep their timing editable.

When a reveal appears early, inspect the current PCM around the preceding word and pause rather than trusting the automatic word boundary. A word beginning with an unvoiced consonant can start with high-frequency frication before strong vowel energy appears: inspect the spectrogram as well as the waveform, and audition the phrase when possible. Record the supported onset interval, chosen frame and rounding rule; spectral evidence alone does not remove uncertainty. Check neighboring cues for the same pause-allocation error, without applying one blanket offset to the phrase.

Move the corrected word, its associated plate/underline and their entrance animation keys together. Place the first reveal/key at the revised frame and preserve relative animation spacing, shortening it if necessary to fit the remaining hold. Keep the established card clear time unless the requested correction requires changing it; preserve unrelated words, picture cuts and audio. Verify the frame before the new reveal, its first visible frame and the settled phrase. Retain the original automatic timestamps separately from the reviewed correction.

Set and read back **both** layer endpoints during a timing revision; do not assume that setting only `inPoint` trims the layer. In the observed AE MCP `layer.set_props` implementation, changing `inPoint` alone also advanced `outPoint` to preserve duration while leaving `startTime` and animation keys unchanged. Supply the revised `inPoint` and explicit intended `outPoint` together, shift position/scale entrance keys deliberately, then verify the settled cue and original card end. Check associated accents and unchanged media bounds in the same native readback.

## 4. Verify fonts and build the full phrase layout

Use AE `font.list`, `font.info` and actual `text.measure` results. The pilot resolved `PlusJakartaSans-SemiBold` to the variable font with weight 600, explicitly confirmed through `text.set_variable_font`. IBM Plex Mono was available via Adobe Fonts even though a filename search missed it. Duplicate PostScript names can point to variable and static instances; inspect actual resolution.

Lay out complete phrases, then reveal individual word layers at their onsets. Each word retains its final position as later words appear. Measure advances in the same AE font and size that will render. Avoid guessing widths from a browser or different font library. The helper compiler supports generating operation plans from a manifest and measured widths; read its contract before use.

Derive each text-safe rectangle from the current picture across the shot, including leaning and gestures. Sample word entrances and completed phrases, then inspect denser source frames around the smallest apparent head/body margins. A fixed rectangle can pass every alpha frame while later poses move into it. Narrow or reposition the layout when the picture requires it; preserve word timing and uniform glyph proportions. See [body-clear layout](continuation-body-clear.md#design-for-bodies-and-camera-cuts) for shot boundaries and [verification](verification-delivery.md#picture-and-word-checks) for separate containment and picture verdicts.

Use native `layer.bounds` after text styling to measure visible glyph extents, including descenders. Combine those bounds with the actual anchor, position and scale; advances alone are insufficient for accent geometry. Fit orange plates to the targeted glyph union with explicit horizontal/vertical padding and stroke allowance, keeping the whole plate in the picture-derived clear area. Derive underline spans and offsets from the same ink bounds. Recompute accents after a text-size, scale or position change.

The UHD pilot used a left anchor280px, lower-half baselines 1460–2000px, white type, a 3 px dark stroke behind nonplate text, and #FF570A rectangular plates. Jakarta sizes 116–258px and mono 88–98px created deliberate hierarchy. These dimensions were chosen to keep both faces and the right-hand rabbit photograph clear. Adapt them to the actual shot, aspect ratio and insert layout.

## 5. Construct editable AE text and shapes

Inspect and preserve the existing AE project. Save unrelated work before creating or switching to a new project; never overwrite it with a demo. Create a uniquely named composition at the actual target canvas, rational rate and pilot duration.

Use native operations discovered from the current AE catalog:

1. `comp.create` for the typography composition.
2. `layer.create_text` for each named word.
3. `text.set_style` for PostScript font, size, color, justification and stroke; set variable axes when applicable.
4. `text.measure` for actual composed advances; assign final positions through `transform.set`.
5. `layer.set_props` with `inPoint` and `outPoint` for direct reveals and phrase clears. Differentiate word onsets from phrase out-points.
6. Native shape groups, rectangle paths and fills for orange plates. Create a small CAD plate and a second wider CAD BENCH plate at BENCH's onset so existing text stays still.
7. Use an underline rectangle anchored at its left edge, with Scale keys `[0,100]` to `[100,100]` across five frames for the sample style. No overshoot was added.
8. Keep shapes below text and above a locked reference picture guide layer. A guide layer is visual context and should be excluded from final alpha rendering.

Make the main review composition obvious, and name phrase groups with the speaker and recognizable spoken text. Name word layers by their visible text and function; keep machine IDs as suffixes or in the timing map rather than making them the only navigation aid. Use consistent speaker label colors with a short legend, and expose cue context through phrase markers, layer comments or the linked timing map. A 31-layer composition was reasonable for 26 words, four shapes and one guide. For a longer trailer, group phrases into named precomps or another clear hierarchy. Manual word edits in this pilot require manual plate/underline width adjustments; do not advertise automatic resizing unless implemented and tested.

When motion is requested, establish a small reusable treatment before spreading it across the trailer. Native text animators with opacity/position and range selectors, or equivalent editable keys, can provide a consistent entrance. Review easing, line spacing and visual weight across title cards and dialogue layouts; test italic emphasis in the actual phrase rather than applying it indiscriminately. Preserve measured speech onsets and approved holds while refining motion. Direct reveals remain valid when they match the chosen reference; different card types need not have identical animation durations.

Use `batch.run` for bounded related operations, with `stopOnError:true` where later edits depend on success. Examine per-operation warnings: trying to change `guideLayer` on a locked layer emitted a warning while the batch still reported success. Unlock deliberately first, or use a separate review composition. Never assume a returned PNG has finished writing when immediately reused; verify dimensions and use unique proof filenames if a stale file is possible.

## 6. Render overlay and review compositions

Create a second review composition with the current native picture/audio export underneath the typography precomp. A 1080p review can use the UHD text comp at 50%; the original UHD overlay remains suitable for the native sequence.

Discover render templates with a queue item and `render.list_templates`. The worked outputs used `High Quality with Alpha` for MOV and `H.264 - Match Render Settings - 15 Mbps` for the review. Explicitly set overlay `Output Audio` to `Off`; confirm the resulting media has no audio stream and genuine transparency. Native guide layers should be All Off in render settings. Validate actual codec, size, frames, alpha and timestamps.

Render representative completed and intermediate phrase frames before the full pilot. Test editability in a temporary duplicate: change one word, render it, verify the change, then remove only the test duplicate. Save the AEP. Follow [verification and delivery](verification-delivery.md) for audio timing and full decode checks.

## 7. Integrate into Premiere without flattening the edit

Import the silent overlay into a named graphics bin and overwrite it at the intended output time on a spare video line. Snapshot and protect audio first, restore previous locks after insertion, and compare retained audio clip bounds and routing. Verify no unintended linked audio or empty tracks appeared.

Keep camera lines, isolated mic lines, music and the rabbit/photo/screen insert. Disable only old titles that duplicate the new pilot text. The MOV is one graphics overlay; its words are editable in the AEP.

For a bounded pilot, create a subsequence from the exact in/out marks with all required tracks included (`ignoreTrackTargeting:true` in the tested API). Verify native duration and clips; rename both sequence and project item where necessary. The work copy can remain clearly labelled as construction history.

In Premiere 26.5 the new subsequence re-enabled original captions even though the source copy's caption display was off. The scripting API could not read or hide caption tracks. Use fresh native UI state, select the correct pilot, toggle its caption display, and inspect a new native frame. Do not infer that no captions exist from an empty scripting response.

Save and verify the final native state. If the bridge drops, obey its reconnection/stop response and report the remaining native check precisely; a good external preview is not proof that an unseen final UI change persisted.
