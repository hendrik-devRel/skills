# Worked-pilot assets

The skill includes a compact copy of the actual CodeRabbit pilot under `assets/worked-pilot/`. This is a finished example and editable starting reference. It is not a universal trailer template with automatic text reflow or an installed Premiere project.

| File | Purpose |
|---|---|
| `AF-Kinetic-Pilot-v01-PREVIEW.mp4` | Completed 10.010-second style reference with corrected audio timing |
| `AF-Kinetic-Pilot-v01.aep` | Actual native text, shapes, underline keys, reference guide and review composition |
| `pilot-background.mp4` | Current Premiere picture/audio export used by that AEP |
| `dialogue-first10.wav` | Native audio used for word timing and final preview audio |
| `review-cad.png`, `review-astra.png`, `review-prompting.png` | Native rendered layout references |
| `layout-spec.json` | Saved original word/line layout, measured advances and nominal onset seconds |
| `pilot-word-timings.json` | Fresh ASR words, chosen frame-grid onsets and uncertainty notes |
| `reference-style-guide.json` | Machine-readable reference findings |
| `reference-style-guide.md`, `qa-summary.md`, `pilot-word-onset-recommendations.md` | Portable reference analysis, validation record and timing uncertainty notes |
| `pilot-alpha-qa.json` | Numerical transparency/decode evidence for the rendered overlay |
| `pilot-preview-audio-synced-qa.json` | Passing multi-window preview audio comparison |
| `manifest.json` | Byte sizes, SHA256 hashes and original provenance for copied files |

Use the helper-specific example and contract for regeneration. The original `layout-spec.json` is retained as evidence of the executed pilot; it is not itself a promise that every later compiler accepts that legacy schema directly.

The AEP has 26 individually editable words plus four shapes and a guide. Words hold fixed positions; plates and the underline have manually adjustable widths. It contains the original episode's references. Open a copy and replace the reference media for a new episode rather than editing the preserved example.

Both referenced media inputs accompany the AEP. If AE reports offline files on another computer, relink to the matching filenames in this folder; the original AEP's path references were not rewritten or tested on a second machine. Plus Jakarta Sans SemiBold and IBM Plex Mono must resolve in AE there. Font binaries, Adobe apps and MCP servers are not bundled.

The large 151 MB ProRes alpha overlay is left in the episode output folder rather than duplicated into the skill package. It can be rerendered from the AEP. Its actual verified delivery remains at the absolute path listed in [the worked case](worked-astra-fable-pilot.md). A fresh render should be checked, particularly if fonts or AE versions change.

The AEP's H264 review export exhibited a 1024-sample audio delay in this run. The included final preview was corrected externally using the native WAV and verified again. If you rerender the review, remeasure its audio; do not assume the correction is embedded in the AEP or always required.
