# Editable camera tracks from builder XML

`scripts/restructure_podcast_xml.py` restructures the untouched output of `build_podcast_xml.py` into **three explicit camera tracks**, preserving full-source video-only ANGLE nests and the existing visible camera/source edit. It does not control Premiere or modify media. Use before native import; never regenerate over a later native edit.

## Selected tracks versus synchronized alternatives

Choose the structure for the receiving editor's workflow. This helper distributes selected shots and preserves source handles; it does not build a native multicam source. When the editor needs live angle switching or immediate alternate coverage, also retain a clearly labeled native multicam source or synchronized stacked-camera assembly. Cover the retained conversation wherever each source exists, and record genuine camera gaps. Follow the verified recorder/camera mapping and drift correction; equal clip starts alone do not establish sync.

Keep that assembly separate from the approved selected-shot timeline unless the chosen native multicam structure preserves its visible edit. Continuous enabled upper tracks would obscure lower selected shots. A native multicam source supports the editor's angle-switching controls; a stacked assembly should make corresponding moments easy to find and insert without re-syncing. Test a representative angle change and verify picture timing and independent dialogue before calling the handoff ready.

## XML helper

Runtime: Python 3.10+ standard library. Inputs: generated XML, its matching SHA-256-bound builder manifest, and an explicit adaptation JSON. Outputs: a new `.xml` and adjacent `.separate-tracks.json` audit. The output directory must exist; existing outputs/reports are refused. Input XML must match `manifest.xml_sha256`.

```sh
"$EDIT_PYTHON" "$EDIT_SKILL/scripts/restructure_podcast_xml.py" "$BUILD_DIR/edit.xml" \
  --manifest "$BUILD_DIR/edit.validation.json" \
  --config "$BUILD_DIR/separate-tracks-config.json" \
  --output "$BUILD_DIR/edit-separate-cameras.xml"
```

Set these variables to the chosen Python, installed skill folder and episode build directory. Use the builder's actual manifest filename. The helper writes only the two explicit construction artifacts.

## Configuration contract

All camera IDs and sequence names must match the builder manifest. Camera count is exactly three; speaker/stem count is independent. This is a schema example, not a mapping inferred from filenames:

```json
{
  "schema_version": 1,
  "sequence_names": ["Main edit"],
  "video_tracks": [
    {"camera": "wide", "label": "Wide"},
    {"camera": "angle_a", "label": "Angle A"},
    {"camera": "angle_b", "label": "Angle B"}
  ],
  "background": null,
  "disabled_gap_handles": false,
  "audio": {"mode": "preserve"}
}
```

Track order is bottom V1 to top V3. Desired labels are recorded in the audit; check/rename the actual native track labels after import. `background` must explicitly be null unless the bottom camera is visually confirmed as wide. To fill its available gaps, set:

```json
"background": {"camera": "wide", "confirmed_wide": true, "coverage": "required"},
"max_coverage_clip_frames": 300
```

Choose the coverage chunk length at the actual sequence frame rate and measured clock drift. `required` fails if the wide source cannot cover an interval; `available` records any uncovered ranges. Added coverage follows retained recorder spans and recomputes the explicit affine camera mapping per chunk, without introducing a speed effect. Inspect the reported maximum within-chunk drift estimate.

Keep `disabled_gap_handles: false` for a clean selected-shot edit when the companion synchronized assembly supplies the alternatives: the original ANGLE nests retain full source handles for extending a cut. `true` adds disabled reference clips in gaps and also requires a positive chunk length. Such clips can obstruct native edge extensions until trimmed/removed and are not equivalent to native multicam switching. Never enable continuous upper camera tracks that hide the selected edit. Extending an active upper clip can still require trimming another track to preserve the intended view.

## Audio modes

`audio: {"mode": "preserve"}` keeps the builder's audio untouched. This is a valid final arrangement when the available source is a shared stereo mix. Camera track separation does not create microphone isolation.

Only when verified independent processed mono stems exist, choose:

```json
"audio": {
  "mode": "promote_processed_stems",
  "stems": [
    {"path": "../Audio/verified-person-a.wav", "label": "Person A"},
    {"path": "../Audio/verified-person-b.wav", "label": "Person B"}
  ],
  "keep_unselected_stems_disabled": true
}
```

Relative stem paths resolve against the adaptation config directory. The builder must already have included them with `include_stems=true`; selected paths must match that program's `muted_processed_stems`. Any positive number of explicitly verified stems is supported, including three. The helper checks mono 48 kHz source declarations and exact recorder-span timing, removes the old audible master L/R pair, enables/centers/unlocks selected stems, and retains others disabled only if requested. It never manufactures stems or guesses COMBO/USB identities. Native pan-law gain, stereo mix routing, loudness and output limiting still require a native pilot.

## Evidence and native checks

Structural checks require unique/resolved XML IDs, existing source files, valid source bounds, ordered nonoverlapping clips, duration-preserving recorder spans, unchanged original ANGLE sequences and active clip properties, and an identical topmost camera/source map. Shared file definitions needed by untouched sequences are preserved. These checks do not decode media or prove Premiere import behavior.

The 11 included synthetic tests exercise three-camera coverage, three centered mono stems, shared-mix preservation, removed recorder intervals, missing/unconfirmed wide coverage, unverified/duplicate stems and file references used by unmodified sequences. CLI fixtures also check output outside the installed skill, preservation of inputs/existing outputs and rejection of a changed source XML. These CLI fixtures use empty source placeholders and do not validate codecs. The command reports `native_import_verified: false`; perform actual native import, camera/track naming, trim-handle, scaling, routing, source-in and render checks for the current project. Preserve that distinction when reporting success.
