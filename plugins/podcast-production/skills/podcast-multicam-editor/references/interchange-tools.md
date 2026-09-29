# Config-driven episode interchange tools

These tools produce editable source-linked Premiere/FCP `xmeml` interchange, not a native `.prproj` and not a listening-approved final edit. Original media and existing projects remain untouched.

From the installed skill folder (or use absolute script paths):

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/build_episode_edit.py /absolute/episode-config.json
python3 scripts/validate_episode_xml.py /absolute/output/FULL.xml --min-shot-seconds 3.5 --expected-markers 0
python3 scripts/validate_episode_xml.py /absolute/output/TIGHTENED.xml /absolute/trailer/TRAILER-DRAFT.xml
```

## Config contract

- `episode_name`, `fps` (rational string such as `60000/1001`), sequence `width` / `height`.
- `master_start_seconds`, `master_end_seconds`: intended conversation boundaries in the chosen recorder master clock.
- `sources.guest`, `.host`, `.wide`: `path`, native `width` / `height`, explicitly probed rational `fps`, `duration_seconds`, signed `offset_seconds`, `drift_ratio`, optional `color_note`. Every source must match sequence cadence; unequal rates are rejected, not mislabeled or silently conformed.
- Probed VFR sources must set `variable_frame_rate: true` and are rejected by this helper. Absence of that field is only a legacy-config assumption, not proof of CFR; inspect source cadence before generation. Rational rates must round-trip exactly through xmeml timebase/NTSC fields. Audio layouts other than stereo program plus two mono ISOs (2/1/1) fail before output files are written.
- Mapping direction is always **source seconds = offset seconds + drift ratio × master seconds**. An offset is not “camera start time”; a later camera start normally means a negative intercept.
- `audio.program`, `.guest_iso`, `.host_iso`: `path`, `duration_seconds`, `channels` (2/1/1), optional `offset_seconds` (default zero), `sample_rate` (48000), `bit_depth` (24). Audio `drift_ratio` must be 1; these tools never stretch the master or ISO audio.
- `audio_delivery_mode`: `recorder_mix` (default for older configs) enables stereo program and disables ISOs; `iso_mix` enables the two independently editable mono ISOs and disables the original stereo reference. This choice does not change the synchronization master. Never enable both complete mix and ISOs together.
- Each audio source may specify `gain_db` (-96 to +12 dB) and mono ISO `pan` (-1 left, 0 center, +1 right). These encode editable Audio Levels/Audio Pan effects, not normalization, dynamics or baked media. Conflicting per-source `enabled` flags fail rather than overriding delivery mode. Verify imported effect values and channel routing in Premiere.
- `speaker_segments_csv`: CSV containing `start_master_seconds,end_master_seconds,state`; allowed states are guest/host/overlap/silence/wide/unknown. Uncovered spans become unknown/wide and are reported, not fabricated speaker labels. Overlapping, reversed or sub-frame segments are errors.
- `output_dir`: episode output folder. `trailer_output_dir` optionally places trailer XML/CSV in a separate folder.
- `approved_removals`: optional list of `{start_master_seconds,end_master_seconds,reason?,context?}`. Presence of an empty array produces an identical separately named TIGHTENED sequence; that is not evidence that tightening occurred.
- `trailer_ranges`: optional ordered list of `{start_master_seconds,end_master_seconds,camera?}`; default camera is guest. Only the selected dialogue appears. No identity card, music, graphics, or invented duration is added.
- `pacing` optionally supplies `minimum_hold_seconds` (3.5), `speaker_confirm_seconds` (0.5), `wide_reset_after_seconds` (45), and `wide_hold_seconds` (6). These are starting values; episode-specific pacing may override them. Wide share is measured, not forced to a quota.
- `max_within_shot_sync_error_seconds`: default 0.05. The report bounds uncorrected intra-shot clock drift plus half-frame rounding. This does **not** include uncertainty/residual error in the measured source sync itself.

Relative paths resolve against the config's directory. Outputs are `FULL.xml`, optional `TIGHTENED.xml`, optional `TRAILER-DRAFT.xml`, cut CSVs and `edit-summary.json`. `PODCAST.xml` combines only FULL/TIGHTENED for one native import, with unique sequence/clip IDs and shared source definitions deduplicated across them. The trailer remains separate. Re-running updates those generated outputs; use a new output directory to retain a prior version.

## Edit guarantees and limits

- Frame quantization is shared across master boundaries, sequence boundaries, source in/out and audio ripple regions. Source out equals source in plus timeline frame duration. Out-of-range media is an error, never a clamp or shortened track.
- Tiny video drift is compensated by per-cut source slip, not a speed effect. The reported error bound must remain acceptable; substantial clock mismatch needs another method.
- Full camera holds are at least the configured minimum. Approved removals are rejected when safe source-region cover cannot fit. Kept picture/audio regions ripple together; joins change camera exactly on the first retained frame and hold that cover for at least 2.85 seconds. Short visual fragments are smoothed only within a continuous retained source region.
- The audio delivery mode determines the enabled tracks. File identifiers are reused per role so picture cuts reference one source definition for each camera. `validate_episode_xml.py --config /path/to/config.json` checks audio mode and every gain/pan value against the intended configuration.
- Native source raster is retained. A 1920×1080 source in a 3840×2160 sequence gets an explicit 200% Basic Motion scale; it is not relabeled native 4K. Mixed aspect ratios fail until framing is explicitly decided.
- Color notes are only notes. No input transform or Lumetri effect is applied. Verify source color interpretation and any technical LUT in Premiere.
- The independent validator checks XML continuity, source bounds against declared/probed durations, file existence, audio states, mixed-raster scaling, join cover, camera totals, and optional marker counts. It cannot prove cloud hydration, decodability, correct speaker detection, good framing, audible edit points, or correct media-probe metadata. Those require actual media/Premiere checks.
- Trailer XML is separate; save it in a separate native Premiere project. Do not prepend it to the episode without approval.

## Audio encoding provenance

[Apple's XMEML Topics](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/FinalCutPro_XML/Topics/Topics.html) specifies linear Audio Levels gain: `10 ** (gain_db / 20)`. [Blender Studio's first-hand Premiere round-trip report](https://studio.blender.org/blog/opentimelineio-in-blender/) supplies the `audiolevels`, `level`, `authoringApp="PremierePro"`, and mono/stereo track metadata. A [published source XML example from NYU](https://www.itp.nyu.edu/~dbo3/comperas/wp-content/uploads/2012/04/ARtoXMLtoPDF1.pdf) contains the legacy `audiopan` / `pan` encoding. XML validation confirms serialized intent; only a native import/playback check establishes current Premiere behavior. Do not describe unverified imported gain or pan as applied successfully.
