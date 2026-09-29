# Local helper contracts

Use these helpers to turn a reviewed word/layout plan into AE operations and to verify preview audio. They do not choose trailer excerpts, discover speech boundaries, replace visual review, or operate Premiere. They never execute native applications themselves.

## Kinetic plan compiler

`scripts/kinetic_plan.py` uses Python 3 standard library only. It emits JSON containing `batches`, each a complete `ae_do` argument object for `batch.run`. The operation parameters were checked against the installed Higgsfield AE catalog on 2026-09-14. Rediscover the relevant catalog before applying in a different environment/version.

The process has two phases because font widths must come from the installed font in AE:

1. Author a plan with the actual sequence's rational frame rate, duration in frames, canvas, phrase lines, word onsets and style. Give the composition and every layer unique names. Use the supplied example as a schema example, not as a transcript for another episode.
2. Run `prepare`. Inspect its JSON. With AE already saved and a verified unused composition name, execute its batches serially and save each structured response. This creates a new typography composition, creates/styles point-text layers, and calls `text.measure`. It does not close, create, save, or delete an AE project. Do not insert footage, a guide, or other layers into this new composition between phases: the shape stacking indices assume only the generated text layers exist.
3. Read actual resolved font family/style and missing-font state. `font` is a PostScript name, not a display-name guess. The compiler does not install or substitute fonts. Optional `font_axes` are applied by `text.set_variable_font` before measurement. The current example uses `PlusJakartaSans-SemiBold` with `wght: 600` and `IBMPlexMono`. The chosen font must support the requested axes; the compiler does not assume a static face is variable.
4. Run `normalize` on the prepare document and its response array. The response file must be a JSON array with one response per batch in the same order. It accepts native batch payloads with `ok`, `failed`, and `results`, or the actual `ae_do.structuredContent` envelope `{ok, result: {ok, results, count, failed}, context, ...}`. Failed, skipped, warned, mismatched or incomplete operations stop normalization, including a warning from a font/style setter. The prepare document contains a plan signature; changing the plan between prepare and normalization is rejected.
5. Run `compile` with those measurements. It lays out each line from actual baseline advance widths plus an explicit gap, assigns word in/out points, and creates native rectangle layers underneath the text. Inspect emitted positions, frames and operations before applying its batches serially. This is a layout pass for the matching prepare pass, not an idempotent update script. Do not replay after an uncertain or partial mutation: inspect native state first.
6. Render representative complete phrases and at least the frame before/on each important word entrance. Check the faces, inset photographs, safe margins, actual font appearance and shapes. Add guide footage and review/export compositions only after layout completes. For a new transcript or changed wording, recompute measurements and deliberately adjust line breaks, sizes, positions and shape geometry.

Example commands (choose an existing Python 3):

```sh
TRAILER_SKILL=/Users/hendrikkrack/.codex/skills/podcast-trailer-editing
TRAILER_WORK=/absolute/path/to/a/new/pilot-work-directory
python3 "$TRAILER_SKILL/scripts/kinetic_plan.py" prepare "$TRAILER_WORK/plan.json" --out "$TRAILER_WORK/prepare.json"
# After executing and saving the actual AE responses:
python3 "$TRAILER_SKILL/scripts/kinetic_plan.py" normalize "$TRAILER_WORK/plan.json" --prepared "$TRAILER_WORK/prepare.json" --responses "$TRAILER_WORK/prepare-responses.json" --out "$TRAILER_WORK/measurements.json"
python3 "$TRAILER_SKILL/scripts/kinetic_plan.py" compile "$TRAILER_WORK/plan.json" --measurements "$TRAILER_WORK/measurements.json" --out "$TRAILER_WORK/layout.json"
```

All output paths must be new. `open(..., 'x')` refuses existing files and symlinks. Output directories must already exist. `--chunk-size` defaults to 64 operations; each emitted batch uses `stopOnError: true`. A batch is not transactional even with that setting.

### Manifest fields

See [pilot-plan.json](../assets/examples/pilot-plan.json) for a complete 26-word example with real geometry.

- Root: `schema_version: 1`, unique `comp` name, `fps: {num: 60000, den: 1001}`, integer `duration_frames`, `canvas: {width, height}`, nonempty `lines`, optional `shapes`.
- Line: `left`, `baseline`, `font` PostScript name, `font_size`, `gap_px`, `end`, and `words`. Coordinates and font sizes are in composition pixels. A point-text layer's anchor is `[0,0]`; `baseline` is its baseline y coordinate.
- Word: unique `name`, `text`, `onset`; optional `end`, `font`, `font_size`, `font_axes`, `fill`, `stroke_width`, `stroke`, `x`, `vertical_envelope`. These override the line's values. `font_axes` maps four-character axis tags to numeric values, for example `{"wght": 600}`; it may also be set on a line. `x` is an optional explicit baseline origin; otherwise the compiler places the word after the preceding measured advance plus `gap_px`. These are single-line point-text word layers, not paragraph text or automated line wrapping.
- Line/word defaults: white fill; no stroke unless specified; dark `[0.03,0.03,0.03]` stroke color; stroke behind fill; zero tracking; left justification. `vertical_envelope` is `[top,bottom]` relative to baseline, default `[-font_size,0.3*font_size]`.
- Time: a decimal seconds value/string or `{"frame": integer}`. Fraction strings such as `"1001/120000"` also work. Times are converted using exact rational arithmetic and nearest-frame rounding, with halfway values rounding upward. JSON floating numbers are interpreted through their decimal string representation. Use explicit frames when an editorial cut is already known precisely. Negative, collapsed, unordered or out-of-duration intervals are refused.
- Shape: unique `name`, `kind: "plate"` or `"underline"`, top-left `position: [x,y]`, `size: [width,height]`, `onset`, `end`, optional RGB `fill`. The default is orange `#FF570A`. Each is an editable rectangle with path position `[width/2,height/2]`, zero roundness and layer anchor `[0,0]`.
- Optional shape `width_keys`: array of `{time, width, easing}`. Width is implemented as horizontal layer scale around its left edge. The first key must equal the shape's in point; keys must be distinct frames and inside its visible interval. `width` must be between zero and declared full width. Easing supports `linear`, `hold`, `ease`, `easeIn`, `easeOut`. The pilot underline uses frames 242→247 at widths 0→827.406 px.

The compiler rejects out-of-canvas declared rectangles and text advance/envelope bounds. `text.measure.baselineLocs` gives advance width, **not pixel ink bounds**; the vertical envelope is explicitly a conservative design envelope, not a measured glyph box. Glyph overhang, stroke extents, collision with a face and optical alignment still require a native rendered frame. There is no dynamic text reflow or automatic shape resizing. The original example's separate CAD and CAD BENCH plates intentionally overlap with the same fill.

### Measurement contract

`normalize` first verifies the prepare document's complete plan signature, then obtains advance as `baselineLocs[2] - baselineLocs[0]` for one composed point-text line. It records a SHA-256 signature of text and relevant style, including variable-font axes, for each layer. `compile` rejects missing, stale, nonfinite, nonpositive or off-canvas width measurements. A stored width for one word/font/size cannot be silently reused after changing them.

The bundled [pilot-measurements.json](../assets/examples/pilot-measurements.json) contains actual advances captured in the successful original pilot's `layout-spec.json`. It supports reproducing this exact example only. It is not a lookup table for arbitrary words.

## Audio offset verification and replacement

For long native episode exports, the companion Premiere skill provides [streaming export-audio verification](../../premiere-podcast-editing/references/streaming-export-audio.md) and `scripts/streaming_preview_audio.py`. Use it when the whole-file decoder below would consume excessive memory or both-channel/tail verification is required. It takes the exact matching native stereo PCM and checks the original export clock, sequential sample coverage and unchanged compressed picture. Install/copy that companion skill when using this route; the helper is not duplicated here.

That streaming helper also supports short stereo H.264 trailers with `--window-count 6` and an exact MP4 movie clock. Prefer it when a fractional-millisecond endpoint fails duration QA despite passing sample-count, waveform and tail checks. The reference explains the tested `-movie_timescale` fix; do not loosen timing tolerance or trim the native PCM to fit a rounded container duration.

`scripts/preview_audio.py` requires FFmpeg, ffprobe and NumPy. NumPy is the explicitly required measurement dependency for efficient normalized FFT correlation; it is not needed by the kinetic compiler. Use an existing suitable Python, or an isolated environment. The machine used for this pilot had NumPy in:

`/Users/hendrikkrack/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`

The reference must be an authoritative **same-origin, same-content** native audio export of the range shown in the preview. The test compares waveforms, so changed music, cuts, noise processing or speaker mixing can make the result inconclusive. It does not prove lip-sync or validate the original source alignment.

`verify` decodes the reference and preview audio stream to mono 48 kHz floats and searches a default ±150 ms lag in six windows. It requires exactly one preview audio stream and at most one picture stream. It first checks stream start timestamps: audio must start with picture (or at zero for an audio-only file) within one sample. Raw PCM decoding would otherwise hide a shifted audio track. It also rejects a truncated or overlong decode: PCM may differ by at most two samples; AAC allows up to one final 1024-sample packet of decoder padding. When picture exists, its duration must agree with the reference within two samples. These preconditions are reported as `TIMELINE_ORIGIN_MISMATCH` or `DURATION_MISMATCH` rather than a waveform pass.

Each window uses normalized cross-correlation, which tolerates overall gain differences. Positive lag means the preview is late. A default minimum correlation of 0.97 must be met in all six windows; a hit at the search boundary is inconclusive. The default required lag is zero samples. Noisy, silent or inconsistent windows are reported rather than called a pass.

Use explicit speech-rich windows when available; [pilot-audio-windows.json](../assets/examples/pilot-audio-windows.json) records the six intervals used for the 10-second example. Windows must be ordered and non-overlapping, with each midpoint in its corresponding sixth of the reference duration. Repeating one known-good window cannot stand in for six distributed checks. With no `--windows`, the helper selects six evenly spaced interior windows; verify they contain usable signal. The helper decodes the full audio into memory, so use it for bounded trailer/pilot ranges, not an entire multi-hour episode.

```sh
TRAILER_PYTHON=/path/to/python-with-numpy
"$TRAILER_PYTHON" "$TRAILER_SKILL/scripts/preview_audio.py" verify \
  --preview "$TRAILER_WORK/preview.mp4" --reference "$TRAILER_WORK/native-dialogue.wav" \
  --windows "$TRAILER_WORK/audio-windows.json" --report "$TRAILER_WORK/audio-qa.json"
```

Exit 0 means pass, 2 means a completed test found a lag/inconclusive result, 1 means invalid input or an execution error. JSON contains the per-window lag and correlation. A constant lag result does not authorize changing the original project or original audio.

`replace` creates a **new** MP4 with stream-copied picture and AAC audio encoded directly from the authoritative PCM WAV. It does not shift the existing encoded audio by an assumed number. Both inputs remain unchanged. Preconditions: exactly one picture stream, one uncompressed PCM reference audio stream, and their durations agree within two 48 kHz samples.

```sh
"$TRAILER_PYTHON" "$TRAILER_SKILL/scripts/preview_audio.py" replace \
  --preview "$TRAILER_WORK/ae-raw.mp4" --reference "$TRAILER_WORK/native-dialogue.wav" \
  --windows "$TRAILER_WORK/audio-windows.json" \
  --out "$TRAILER_WORK/preview-audio-corrected.mp4" --report "$TRAILER_WORK/replacement-qa.json"
```

Replacement is staged in a new temporary file. Before publishing it, the helper reruns all six correlation windows and compares the compressed video payload SHA-256 against the input. It publishes only on a pass, using a hard link that refuses overwriting an existing output. Failed replacement QA removes the temporary media and writes the failure report. There is no in-place edit. File-format duration/sample padding from AAC may exceed the authoritative duration slightly; actual decoded waveform lag is the measured criterion.

## Validation performed on 2026-09-14

- The compiler was run on the captured pilot plan and widths: 26 words, 4 shapes, two prepare batches and two layout batches. Its output positions match the original saved layout. All six local regression tests passed, including exact frame math, five-frame underline duration, stale/missing widths, geometry/timing rejection and no-overwrite behavior.
- Run the regression checks with `python3 scripts/test_kinetic_plan.py` from any directory. The tests do not touch AE or Premiere. The response-normalization check uses a synthetic structural fixture populated with the captured actual advance values; it is not a new native response capture.
- Audio verification on `AF-Kinetic-Pilot-v01-AE-RAW.mp4` independently found **+1024 samples** in every window. Verification on the delivered preview found **zero samples** in every window.
- A fresh non-destructive replacement from the raw AE MP4 and authoritative WAV passed all six zero-lag windows and matched the original compressed video payload hash.
- Evidence is in the episode work folder `outputs/astra-fable-first-edit/trailer-analysis/kinetic-pilot/helper-validation/` (latest compiler files `prepare-v2.json`, `layout-v2.json`; audio reports `raw-audio-qa*.json`, `final-audio-qa*.json`, `rebuilt-audio-qa*.json`; `rebuilt-preview-v3.mp4`).
- Independent forward checks reproduced and fixed stale-style normalization, ignored setter warnings, duplicate windows, truncated media and a shifted audio stream timestamp. They do not replace future native font/render verification.
- **The newly generated compiler batches were not executed in AE during skill documentation.** The original pilot already had native render and editability verification; do not confuse that with an end-to-end native replay test of these new helper scripts. Re-render after applying them in a future episode.

See the [independent forward-check record](helper-forward-check.md) for the alternate canvas/frame-rate scenario, reproduced edge cases, corrected results, and precise native-validation limits.
