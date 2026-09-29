# Portable nested-angle XML builder

`../scripts/build_podcast_xml.py` generates **ungraded FCP7 XML plus a validation manifest**. It reads source metadata with `ffprobe`, creates one full-length video-only ANGLE sequence per camera, and references those sequences from edited timelines. Grade each original once inside its ANGLE sequence after importing into Premiere.

It does not synchronize, analyze speakers, process audio, apply LUTs, import into Premiere, or save a native project. Supply measured synchronization and an approved editorial plan first. The native `.prproj`, after visual and audio verification, is the canonical edited deliverable.

## Run

Requires Python 3.10+ and `ffprobe` on `PATH`. No Python packages are needed.

```sh
python3 /path/to/premiere-podcast-editing/scripts/build_podcast_xml.py \
  /path/to/episode/edit-config.json \
  --output /path/to/episode/Timelines/first-edit.xml
```

Use `--ffprobe /absolute/path/to/ffprobe` if needed. Existing XML or manifest files cause refusal; `--overwrite` explicitly replaces those two generated files. Relative **input** paths resolve beside the config JSON. Relative `--output` resolves from the current working directory. Paths with spaces are supported. Keep config, sources, outputs, and editorial JSON files separate.

Outputs:

- `first-edit.xml`: portable construction interchange with unique IDs and local media URLs.
- `first-edit.manifest.json`: source dimensions and frame counts, measured affine coefficients, camera cuts/source ins, retained intervals, audio routing, markers, source quantization/drift estimates, XML SHA-256, and structural validation. `premiere_import_verified` remains `false`: only a native import and review can establish that.

## Complete example

These filenames, times, and synchronization coefficients are **illustrative**. Replace them with this recording's inspected files, measured sync coefficients, actual speaker identities, and approved ranges. Never reuse these sample coefficients as defaults. All times below are seconds on the original recorder clock.

```json
{
  "schema_version": 1,
  "project_name": "Podcast Episode",
  "fps": "60000/1001",
  "output_resolution": [3840, 2160],
  "cameras": {
    "guest": {
      "path": "Media/Guest.MP4",
      "sync": {"time_scale": 1.000012, "offset_seconds": 12.34}
    },
    "host": {
      "path": "Media/Host.MP4",
      "sync": {"time_scale": 1.000018, "offset_seconds": 7.21}
    },
    "wide": {
      "path": "Media/Wide.MP4",
      "sync": {"time_scale": 1.000014, "offset_seconds": 10.82}
    }
  },
  "audio": {
    "recorder_aligned": true,
    "master_stereo": "Audio/Master_Stereo_Full_48k24.wav",
    "processed_mono_stems": [
      {"name": "Guest microphone", "path": "Audio/Guest_Processed_Full_48k24.wav"},
      {"name": "Host microphone", "path": "Audio/Host_Processed_Full_48k24.wav"}
    ],
    "raw_mono_mics": [
      {"name": "Guest original", "path": "Audio/Guest_Original_48k24.wav"},
      {"name": "Host original", "path": "Audio/Host_Original_48k24.wav"}
    ]
  },
  "speaker_camera_map": {"speaker_a": "guest", "speaker_b": "host"},
  "wide_camera": "wide",
  "speaker_segments": [
    {"start": 20, "end": 100, "speaker": "speaker_a"},
    {"start": 100, "end": 210, "speaker": "speaker_b"},
    {"start": 210, "end": 350, "speaker": "speaker_a"},
    {"start": 350, "end": 700, "speaker": "speaker_b"}
  ],
  "edit_policy": {
    "minimum_shot_seconds": 5,
    "opening_wide_seconds": 8,
    "closing_wide_seconds": 5,
    "relief_after_seconds": 65,
    "wide_hold_seconds": 5
  },
  "sequences": [
    {
      "name": "MAIN FIRST EDIT",
      "keep_ranges": [[120, 300], [320, 600]],
      "markers": [
        {"recorder_seconds": 120, "title": "Opening", "comment": "Verify the introduction cut."},
        {"recorder_seconds": 220, "end_recorder_seconds": 245, "title": "Screen reference needed", "comment": "Insert the approved screen capture after editorial review."}
      ]
    },
    {"name": "BONUS", "keep_ranges": [[20, 100]]},
    {"name": "REVIEW OPENING", "preview_of": "MAIN FIRST EDIT", "duration_seconds": 120, "include_stems": false},
    {
      "name": "THREE ANGLE IMPORT TEST",
      "keep_ranges": [[150, 165]],
      "shots": [
        {"start": 150, "end": 155, "camera": "guest"},
        {"start": 155, "end": 160, "camera": "host"},
        {"start": 160, "end": 165, "camera": "wide"}
      ],
      "include_stems": false
    }
  ],
  "sync_assembly": {"name": "SYNC ORIGINALS", "chunk_seconds": 60}
}
```

Omit bonus/test/review entries when unwanted. Omit `sync_assembly` and raw microphone paths when a sync reference is unnecessary. Do a small import test first; the example includes one for convenience, but production XML can contain only delivery sequences.

## Config contract

### Sources, frame rate, and synchronization

- `schema_version: 1`, nonempty `project_name`, rational-string `fps`, two positive integers in `output_resolution`, nonempty `cameras`, `audio`, and nonempty `sequences` are required. Unknown configuration keys are rejected.
- Supported sequence rates are `24/1`, `25/1`, `30/1`, `50/1`, `60/1`, `24000/1001`, `30000/1001`, and `60000/1001`. Supply the exact rational, not rounded `59.94`. The tested native workflow used `60000/1001`; other rates require their own small native import test.
- Each camera ID is arbitrary and must have `path` plus explicit `sync.time_scale` and `sync.offset_seconds`. There is no inferred or default sync. The measured model is **recorder_time = time_scale × camera_source_time + offset_seconds**. Therefore a clip's source-in is `(recorder_time - offset_seconds) / time_scale`. A verified zero-offset, zero-drift source is explicitly `{ "time_scale": 1, "offset_seconds": 0 }`.
- `ffprobe` must report exactly one progressive, unrotated, square-pixel video stream, a positive exact `nb_frames`, and matching nominal and average rational frame rates. Mixed rates, obvious variable frame rate, rotation, and interlace are rejected. Matching rate metadata is a preflight check, not a full per-frame timestamp audit; use known constant-frame-rate camera originals.
- The builder reads full camera duration and native resolution itself. Each ANGLE uses those dimensions. Nested shots scale uniformly to **fit** the output using `min(output_width/source_width, output_height/source_height) × 100`. A 1920×1080 source in 3840×2160 output receives 200%; a different aspect ratio can show bars. There is no automatic crop, reframe, stabilization, deinterlace, or resolution enhancement.
- Audio requires standalone 48 kHz PCM WAV files. `master_stereo` must have exactly two channels; each optional `processed_mono_stems` / `raw_mono_mics` entry needs `name` and a one-channel `path`. Duration is read from integer `duration_ts` and rational `time_base`, not rounded filename or cached inventory metadata. Audio bits-per-sample are preserved in file metadata; sequence format is 24-bit/48 kHz.
- `audio.recorder_aligned: true` is required: explicitly confirm **every provided audio file starts at recorder t=0**, with processing latency compensated and no editorial time removal. The script can verify format and duration, but it cannot prove acoustic synchronization from metadata. Short files that do not cover requested ranges are rejected. Processing, loudness, and sample alignment must be established separately.

### Editorial plan

- Every regular sequence has a unique `name` and ordered, non-overlapping `keep_ranges: [[recorder_start, recorder_end], ...]`. Ranges are concatenated without gaps. Boundaries round to the nearest frame (`floor(seconds × fps + 0.5)`). Audio and video share exactly those quantized intervals. Deleted intervals get a review marker, not an automatic crossfade.
- Choose automatic speaker planning **or** explicit `shots` per sequence. Explicit shots override all automatic opening/closing/wide/minimum policies. These must be ordered, non-overlapping `{start, end, camera, reason?}` recorder intervals that cover every retained frame. They may cross removed intervals; the builder splits them at keep boundaries. Gaps in retained coverage are errors. This option is appropriate for a reviewed camera plan or controlled import test.
- Automatic planning requires `speaker_segments`, `speaker_camera_map`, and `wide_camera`. Segments are ordered non-overlapping `{start, end, speaker}` intervals. Map identities to camera IDs explicitly; microphone track numbers do not identify cameras. Unmapped speaker labels and gaps in segment coverage use the wide camera; map all known identities explicitly so a misspelling does not silently choose wide. Use conservative speech evidence and inspect interjections, overlap, and reactions; the generator does no diarization.
- `speaker_segments` can be an inline array or a path to JSON containing an array or `{ "segments": [...] }`. Each sequence's `shots` and `markers` similarly accept arrays or paths to arrays / `{ "shots": [...] }` / `{ "markers": [...] }`. Relative JSON-file paths resolve from the config directory. Speaker segment entries may carry additional analysis metadata; planning uses only `start`, `end`, and `speaker`.
- `edit_policy` keys default to the values in the example. Set opening, closing, or relief-after seconds to `0` to disable that behavior. Minimum shot and wide hold must remain at least one frame. Automatic keeps must be at least the minimum shot length. Short speaker turns may be extended by borrowing from neighbors or merged into a neighbor; review the manifest's resulting plan.
- At 60000/1001 fps, a real 5.000-second turn can round to **299 frames**. The automatic planner first attempts the tested one-frame borrowing policy; if neighboring five-second turns cannot donate a frame, it preserves a 299-frame turn instead of deleting the response. Intentional five-second wide holds use 300 frames. This is a quantization tolerance, not permission to shorten all holds.
- The first retained interval receives the opening wide; the last receives the closing wide. Wide relief is inserted after the configured long-closeup duration when sufficient trailing footage remains. Speech-boundary borrowing can shift cuts slightly. No new opening is automatically added after a removed interval.

### Audio routing, previews, markers, and sync reference

- Delivery audio is the unchanged-gain premixed stereo master, represented by linked left/right source-channel clips on two tracks, hard-panned −1/+1. This matches the tested FCP7 import route. Processed mono stems are centered and disabled at **both track and clip level** to prevent doubling. To adjust a stem natively, enable both levels and manage the master so the same voice is not doubled. A numeric gain or LUT is not embedded by this helper.
- `include_stems` defaults to `true` for each sequence; `false` leaves only the stereo pair. `raw_mono_mics` appear only in the optional sync reference and are audible centered raw tracks there.
- A preview entry uses `preview_of` naming an **earlier** sequence and positive `duration_seconds`. It takes exactly that sequence's first N rounded frames, preserving cuts, source ins, audio offsets, and keep-gap mapping. It cannot also provide `keep_ranges` or `shots`. It does not invent a closing wide; its final shot can be shorter than the minimum. Markers and `include_stems` are supplied separately per preview.
- `markers` require `title` and `recorder_seconds`; `comment` and `end_recorder_seconds` are optional. Point markers outside retained footage are omitted. Range markers are clipped or split at deleted intervals. Markers annotate editorial work; they do not insert screen captures, B-roll, graphics, or titles.
- Optional `sync_assembly` needs a unique `name`; `chunk_seconds` defaults to 60. Duration defaults to the shortest supplied raw microphone duration, rounded **down** to whole frames, or use explicit positive `duration_seconds` within that coverage. Stacked camera tracks begin/end at their measured recorder-clock coverage; natural gaps are intentional. Camera order follows the `cameras` object order, last on top. Disable upper tracks to inspect other angles. Raw microphones are continuous from recorder t=0. This sequence is a reference and has no delivery loudness guarantee.

## Verification and limits

The generated manifest checks source existence, unique ID definitions, resolved file/sequence/link references, continuous delivery tracks, equal source/timeline clip lengths, and source bounds. The script rereads its XML after writing. It does not modify the inputs or call Premiere.

Camera affine timing is reset at every cut (and each sync chunk), **without a speed effect**. This is appropriate for measured small camera-clock drift, not gross speed mismatches. The manifest reports quantization and estimated maximum drift within each shot; estimates above 40 ms produce a warning. Shorten those shots/chunks or use a separately verified retiming workflow. Audio remains on its original recorder clock and is never stretched.

Before trusting the native edit, import a short representative test into Premiere, inspect every angle's size, source-in and lip sync, confirm stereo source channels/hard pans and disabled stems, then check the end of the recording and both sides of removed ranges. Apply the correct input transform manually/through a verified API and inspect the actual image; the XML embeds no LUT or Lumetri grade. Save a new native project. Each generation uses fresh IDs; reimporting can create duplicate angles and does not update an existing graded project.

The XML structure follows Apple's archived [FCP7 elements](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/FinalCutPro_XML/Elements/Elements.html) and [XML basics](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/FinalCutPro_XML/Basics/Basics.html). Premiere import behavior varies by version; successful structural validation is not a native render or listening test.
