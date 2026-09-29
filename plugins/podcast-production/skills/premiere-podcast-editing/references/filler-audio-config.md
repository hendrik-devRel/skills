# Filler-removal audio assembly

Use `scripts/assemble_filler_audio.py` after choosing exact kept recorder-frame intervals. It assembles aligned PCM audio and replaces samples around the resulting joins with short blends. It does not identify fillers, choose editorial boundaries, import into Premiere, or prove that an edit sounds natural. See [filler cleanup](filler-cleanup.md) for the editorial workflow.

## Runtime and input contract

Requires Python 3.10 or newer and NumPy. Resolve the script relative to this skill's installed location; it has no fixed user directories or external service dependencies.

- This implementation supports **only explicitly declared `60000/1001` fps and already aligned 48,000 Hz audio**. These are helper limitations, not default settings for other projects. A missing `fps`, the approximate value `59.94`, or any other rate is rejected.
- WAV sample zero must represent recorder time zero. Establish offsets and drift before using the helper; it does not align or retime input audio.
- Source: little-endian RIFF or RF64 WAV containing integer PCM16, PCM24, or PCM32, with one or two channels. PCM WAVEFORMATEXTENSIBLE is supported when valid bits equal container bits (or are unspecified). Float, compressed, other-rate, and other-channel inputs are rejected.
- Keeps are sorted, positive-length, nonnegative **half-open** recorder frame intervals `[in, out)`, expressed as JSON integers. They must be separated by deleted material. Merge touching keeps; overlapping or out-of-order keeps are rejected.

## Manifest schema

The manifest is a JSON object. The complete interpreted top-level fields are:

| Field | Required | Type and meaning |
| --- | --- | --- |
| `fps` | Yes | Exact string `"60000/1001"`. |
| `keep_recorder_frames` | Yes | Nonempty array of `[in_frame, out_frame]` integer pairs; all boundaries use the source recorder clock. |
| `joins` | No | Array of objects, exactly one between each pair of keeps. If omitted, each join requests a 20 ms crossfade with zero approved handles. A single keep needs no joins. |
| `room_tone_recorder_frames` | No | `[in_frame, out_frame]` integer pair identifying verified clean source ambience available as the default room-tone span. |

Each `joins` object accepts:

| Field | Default | Type and meaning |
| --- | --- | --- |
| `mode` | `"crossfade"` | Exactly `"crossfade"` or `"room_tone"`. |
| `fade_ms` | `20` | Requested total blend duration, normally 10–30 ms. Converted to the nearest 48 kHz sample and validated as 480–1,440 samples; the symmetric implementation uses an even sample count. |
| `safe_outgoing_handle_ms` | `0` | Nonnegative duration of verified clean samples immediately **after** the outgoing kept section, within the removed interval. |
| `safe_incoming_handle_ms` | `0` | Nonnegative duration of verified clean samples immediately **before** the incoming kept section, within the removed interval. |
| `room_tone_recorder_frames` | Top-level value | Optional per-join override identifying verified clean ambience for this join. |

Durations can be JSON numbers or decimal strings; safe margins round **down** to whole samples. Frame numbers must be integers, not numeric strings, floats, or booleans. Unrecognized fields are ignored and can hold caller metadata; misspelled operational fields do not configure the helper.

This synthetic example illustrates the format; it is not an approved recording edit:

```json
{
  "fps": "60000/1001",
  "keep_recorder_frames": [[0, 60], [72, 132]],
  "room_tone_recorder_frames": [150, 153],
  "joins": [
    {
      "mode": "crossfade",
      "fade_ms": 20,
      "safe_outgoing_handle_ms": 10,
      "safe_incoming_handle_ms": 10
    }
  ]
}
```

## Choose and constrain blends

Review the words, breaths, and room sound around each proposed removal. Set boundaries in safe margins without removing meaningful pauses or word tails. Mark handle lengths only when the corresponding source samples are suitable for reintroduction. Silence detection, low RMS, and ASR labels cannot certify that those handles exclude a quiet filler, consonant, breath, or second speaker.

A crossfade is centered on the program join. Its outgoing and incoming windows extend into the removed interval. Each half is capped to both approved margins, half the actual excluded sample interval, and half each neighboring kept segment. This prevents overlapping fades and bounds any reintroduced material. Fades can shorten, but the helper refuses fades shorter than 10 ms.

When approved handles cannot support 10 ms, an available room-tone span enables automatic `room_tone` fallback. That mode fades retained audio through a continuous center slice of the specified ambience and reads **no handles from the deleted filler**. The ambience must fit entirely inside the source and contain at least the full fade duration. It is not looped or generated. If safe handles and room tone are both unavailable, the helper stops; revise the boundary or obtain suitable ambience. It applies no blanket gate.

## Usage and outputs

From the skill directory, with the source, manifest, and destination set for the current project:

```sh
python3 scripts/assemble_filler_audio.py /path/to/keeps.json \
  --source /path/to/aligned-master.wav \
  --output /path/to/edited-master.wav
```

Optional `--report /path/to/report.json` overrides the default output basename with `.report.json`. Output directories must already exist. Source files are read-only; existing output or report files are rejected. Output is a new 48 kHz PCM24 RIFF WAV retaining the source channel count. Outputs exceeding RIFF's approximately 4 GB limit are rejected. The CLI prints a compact JSON result and exits nonzero on validation failure.

The Python interface is `assemble(manifest, source_path, output_path, report_path=None)`, returning the report dictionary. Apply the same manifest to separately aligned mono raw or processed stems when editable alternatives are wanted, choosing clean ambience appropriate to each input. Avoid playing a master and its duplicated stems simultaneously.

## Timing and verification report

All arithmetic uses the exact rate. The output sample count is:

```text
round_half_up(sum(out_frame - in_frame) × 48000 × 1001 / 60000)
```

Program segment boundaries derive from cumulative kept frames; they are not independently rounded segment lengths. Each source in snaps to its nearest native sample. Outside fades, samples copy at 1:1 speed. A segment's sample end can differ by one sample from independently snapping its recorder out; the report records both. This bounded quantization does not accumulate. A blend replaces samples around its existing program join and adds or removes zero output samples.

The report includes input/output paths and formats, total kept picture frames, exact output samples, duration error, each segment's recorder/source/program mapping, each join's requested and actual length/mode/handle ranges/fallback reason, and unchanged source-to-output ranges. Verification reads back the WAV and checks exact format and sample count, mapping error and per-channel correlation outside fades, every rendered blend, and sample-peak bounds. Constant/silent comparison ranges can have undefined correlation, reported as `null`.

Raised-cosine weights sum to one. This bounds sample peaks by contributing input peaks, allowing PCM24 quantization tolerance. No limiter, normalization, resampling, or dither is applied. A sample-peak check does not prove true-peak compliance after reconstruction or lossy encoding.

## Review claims and tests

Listen to the rendered joins in context, including quiet replies, overlap, breaths, and neighboring words. Then verify the actual native Premiere preview for picture timing, routing, sync, loudness, and true peak. The helper's checks establish signal and timing properties only. ASR, waveforms, correlation, synthetic tests, and successful exports are **not listening**. If listening has not occurred, say so; do not describe candidate boundaries, handles, room tone, or an actual case as listening-approved.

Run the bundled synthetic tests from the skill directory:

```sh
python3 scripts/test_assemble_filler_audio.py
```

The tests create temporary synthetic sources and verify duration rounding, source preservation, mapping outside fades, discontinuity smoothing, sample-peak bounds, safe-handle limits, exclusion of synthetic deleted filler, room-tone fallback, mono stems, PCM24 extensible/RF64 input, and explicit-frame-rate rejection. They do not access or validate a real recording.
