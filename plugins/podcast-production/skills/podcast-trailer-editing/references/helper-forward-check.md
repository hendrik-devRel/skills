# Independent behavioral forward check

The requested 1280 × 720, 30000/1001, four-word scenario can be represented and planned locally with the skill. The nearest eight-second grid duration is 240 frames / 8.008 seconds. Word onsets are frames 3, 13, 27, and 186; the left-edge underline uses frames 186→191. The preparation phase creates four native text layers, and the layout phase adds two editable shapes. Font widths and actual appearance still require AE; MOCK-prefixed files intentionally use synthetic measurements and are not final execution plans.

## Reproduced defects and verified corrections

1. Stale font measurements: an old 60 px prepare/response pair could be normalized under an 80 px manifest and stamped with a new signature. Corrected helper rejects the changed plan at normalization. It now also rejects a mocked text-style warning instead of quietly accepting the batch.
2. Truncated audio: an 8-second prefix of a 10-second reference incorrectly returned PASS_ZERO_LAG. Corrected helper returns DURATION_MISMATCH, exit 2. Evidence: RETEST-truncation-qa.json.
3. Repeated audio windows: six copies of one matching early interval incorrectly passed a candidate with eight unrelated seconds after that interval. Corrected helper rejects the overlapping windows, exit 1, before writing a report.
4. Ignored audio track timestamps: a 10-second video at origin zero with matching 10-second PCM audio beginning at 0.500 seconds incorrectly passed zero lag. Corrected helper returns TIMELINE_ORIGIN_MISMATCH, exit 2. Evidence: RETEST-audio-pts-delay-qa.json.

The original BUG-prefixed files preserve the failing pre-correction results. planning-results.json records the corrected stale-plan and warning behavior.

## What was actually exercised

- Read skill root, native workflow, verification, asset instructions, helper contract, and both helper sources.
- Ran the compiler prepare/normalize/compile workflow with clearly marked synthetic native-shaped measurement responses, then reran prepare through its CLI after the corrections.
- Verified rational timing, four native text layers, orange plate, left-anchored five-frame underline, and generated batch counts.
- Loaded the installed bridge operation registry from local JavaScript modules and ran validateOpArgs against all 17 preparation and 26 layout child operations plus batch wrappers; none were invalid. This only validates declared operation parameters. No Adobe operation was called.
- Confirmed the compiler refuses an existing output path; ran all six bundled regression tests successfully after corrections.
- Ran read-only audio verification against the real bundled pilot and native WAV; all six windows retained zero lag after corrections.
- Ran audio replacement into a new /tmp MP4 after corrections; it passed zero-lag QA and the compressed video payload hash check before publication.
- Checked an intentionally repetitive waveform; it returned INCONSISTENT_LAG, not a false pass.

## Remaining limits and documentation handoff

No remaining reproduced blocker was found after the helper corrections. The new compiler batches were not run in AE, native font resolution was not measured for the new words, no visual render or listening review was performed, and no Premiere sequence was read or altered. The editable AEP and silent-alpha integration workflow is described in scenario-handoff.md. This keeps all isolated microphones on their existing separate tracks and imports only a verified silent graphic above the picture edit.

The final helper contract was rechecked after its update and now documents font_axes, full prepare-plan binding and warning rejection, six-window midpoint coverage, duration checks, and track-origin checks.

Validated on 2026-09-14. Detailed local fixtures remain in `/tmp/trailer-skill-forward-check/`; that temporary directory is not part of the transferable skill. The durable summary is included here and in [helper-test-summary.json](../assets/examples/helper-test-summary.json).
