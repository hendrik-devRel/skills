# Premiere operations: verified workflow and recovery

These observations were tested on macOS with Adobe Premiere Pro 26.5.0 build 99 and `hetpatel-11/Adobe_Premiere_Pro_MCP` 1.2.8 in September 2026. Treat them as version-bounded evidence. Inspect the current tool schema and application state before relying on an old workaround.

The CEP bridge's script validator rejects module-loading and dynamic-evaluation tokens before execution. A harmless locally defined assertion helper named `require(...)` triggered `Script validation failed`; naming that helper `assertState(...)` resolved the false positive without changing the guard or bridge. Inspect the actual validation rule and whether any mutation ran before correcting a rejected script. Do not disable the validator or retry an uncertain mutation blindly.

## Connect and discover

- Reuse a working installation. Start with `verify_premiere_connection` using `launchIfNeeded:false`; confirm `status:connected`, a responsive bridge, Premiere version, and the intended project path.
- A running MCP process or “bridge initialized” log is not proof that Premiere receives commands. Follow connection verification with a read such as `list_sequences` or `get_project_info`.
- The default catalog is deliberately small: `search_tools`, `get_tool_schema`, `invoke_tool`, `verify_premiere_connection`, and `list_sequences`. Missing top-level editing tools do not imply a broken installation.
- Use a focused natural-language query or regex with `search_tools`, request the relevant schema, then call `invoke_tool` with the exact returned name and arguments. Example: search `^(list_project_items|import_fcp_xml)$` with `detail:"schema"`; invoke the chosen result. Avoid repeatedly dumping the full catalog.
- Discover project items, sequence IDs, clip IDs, and tracks from current reads. Never reuse episode-specific IDs from this reference or another project.
- If setup or repair is actually necessary, use the installed `premiere-pro-mcp` skill and its installation/doctor references. Its current location can be found through the skills catalog; do not assume a particular user's home directory.
- For the tested file bridge, the server's `PREMIERE_TEMP_DIR` and the CEP MCP Bridge panel's Temp Directory must agree, commonly `/tmp/premiere-mcp-bridge`. Open the panel under Window > Extensions, save its configuration, and start the bridge when needed.
- Keep configuration repairs limited to the diagnosed connection problem. Do not reinstall a connected bridge or edit unrelated MCP, account, shell, or app settings.

### Explicit stdio fallback

Prefer callable host MCP tools. If the server is already installed but unavailable through the host catalog, use this skill's `scripts/mcp_call.py`. Substitute the actual skill directory and installed server entrypoint; these example paths are placeholders.

```sh
python3 /path/to/skill/scripts/mcp_call.py --server /path/to/dist/index.js --bridge-dir /tmp/premiere-mcp-bridge tools/list
python3 /path/to/skill/scripts/mcp_call.py --server /path/to/dist/index.js --bridge-dir /tmp/premiere-mcp-bridge search_tools '{"pattern":"^(list_project_items|import_fcp_xml)$","detail":"schema"}'
python3 /path/to/skill/scripts/mcp_call.py --server /path/to/dist/index.js --bridge-dir /tmp/premiere-mcp-bridge --args-file /absolute/path/request.json invoke_tool
```

The last example reads an argument object such as `{"name":"list_project_items","arguments":{"includeBins":true,"includeMetadata":false}}`. Use an argument file for complex text and paths instead of interpolating JSON into shell code. Optional flags include `--node node`, `--timeout 90`, and `--log-dir /absolute/path/logs`. The helper does not install/configure the server and never retries a request; inspect Premiere state after an uncertain result before issuing a mutation again.

## Import and establish the native project

1. Save a new working `.prproj` under the authorized output location. Keep originals intact and retain the initial project/checkpoint.
2. Before a large XML import, test a short representative interchange containing each source resolution, nested camera sequences, and the intended audio layout.
3. After import, read sequence dimensions, rational frame rate, duration, clip counts, source in/out points, and media paths. Compare them with the edit manifest; a successful import message is insufficient.
4. Prefer one full-length angle sequence per camera when a shared grade should propagate to all cuts. Inspect the source-to-angle and angle-to-program transforms independently.
5. In the tested UHD program, a native 1920×1080 angle nest needed 200% Motion Scale to fill 3840×2160; native UHD nests used 100%. This follows the actual nested dimensions, pixel aspect ratio, and existing scaling—not the camera name. Verify a rendered test before applying across the edit.
6. Inspect at least one wide shot and each close-up for unintended borders, excessive crop, distorted aspect ratio, or quarter-size nested pictures.
7. After grading and native corrections, the saved `.prproj` is the authoritative edit. Label generated XML by what it preserves; an ungraded reconstruction XML does not automatically contain native Lumetri changes.
8. Reimporting regenerated XML can create new sequences and IDs. Do not replace a graded native edit merely to mirror a correction already applied there; validate both deliverables separately.

## Operate on the intended sequence

- Use `set_active_sequence`, then `set_playhead_position`, and verify the active sequence and visible frame. In the tested build, setting a playhead with a sequence ID alone did not reliably put that sequence in the Program Monitor.
- A newly opened HEVC angle can temporarily show “Media pending” or its old frame while decoding. A playhead acknowledgment does not establish that the displayed picture has refreshed; re-observe before judging its content.
- Read current track/clip state before a mutation and read it again afterwards. On timeout or an ambiguous response, check whether the change happened before retrying.
- Save checkpoints around structural changes. Prefer a bounded change whose before/after state can be compared over a large unverified batch.

### Nested overwrite and audio preservation

- Snapshot all audio clip IDs, project-item references, source in/out points, timeline bounds, gain, mute state, and track locks before replacing a camera turn.
- Lock the master and retained stem tracks before a video overwrite. Restore their prior lock state after verification.
- In the tested build, `add_to_timeline` with `insertMode:"overwrite"` and `linkAudio:false` could still create an empty linked audio insertion from a nested sequence. Do not assume the flag prevents all audio side effects.
- After the overwrite, compare all protected audio clip IDs and timing with the snapshot; confirm program duration, neighbouring video boundaries, and the inserted angle/source range.
- Remove only the newly created, verified empty audio insertion. If it leaves an unused track, confirm the entire track is empty before `delete_track`; resolve its current index rather than hardcoding one. Preserve every retained audio clip.
- Recheck audio counts, routing, mute/gain state, and sequence duration after cleanup. A clean-looking video track does not establish audio preservation.

## Detect camera filename collisions across episodes

Recorder exports commonly reuse names such as `1_CAMERA 1.mp4`. A media item can be online and readable while linked to an entirely different recording. A matching basename, resolution, frame rate, or unchanged timeline snapshot does not establish source identity.

- When resuming a moved/relinked project or investigating wrong pictures, compare every angle's resolved full media path and proxy path with the episode's original manifest and last known-correct native snapshot. Trace nested angle sequences down to their physical media items.
- Confirm candidate originals with byte size, duration/frame count, and fresh early/middle/late pictures of the expected people and setup. Check that referenced source-out bounds fit the actual file. In the observed failure, all three camera names matched but the replacement recording was about 29 minutes shorter.
- A rendered trailer can remain correct while the editable full episode is wrong. Verify the full episode's native picture separately; do not use the trailer as proof of camera links.
- Save a separate project checkpoint before relinking shared project items. Relink the precisely identified camera items to verified episode originals, then read back paths and offline/proxy state. This fixes their uses throughout that project while preserving camera nests and grading.
- Compare native state before/after: only the intended media paths and project save path should change. Preserve source/timeline bounds, effects, audio routing/automation, markers, and track state. Then inspect actual Premiere-rendered samples across all angles and near the end, where a shorter mistaken source might have run out.
- Record what the evidence establishes. Historical snapshots can show when a wrong link was already present; they do not by themselves establish who or which relinking action caused it.

## Paths and native file dialogs

- Use canonical absolute filesystem paths for local media and outputs. Distinguish a local POSIX path from an XML `file://` URL; decode/normalize deliberately rather than stripping characters from every URI.
- XML imports in this session produced local paths like `///Volumes/...`. Premiere could show `offline:false` while the MCP export validator reported `fileExists:false`.
- For that specific mismatch, verify the canonical `/Volumes/...` file exists and identifies the same media, then use `relink_media` on the current project item. Re-read the path and rerun validation; never dismiss an offline warning solely because the picture is cached.
- Use fresh computer-use snapshots/accessibility state for native dialogs. Window layout, panel focus, and accessibility indexes change; do not reuse old coordinates or element indexes without a new observation.
- For Open/Import/LUT dialogs, navigate to the existing file, select its Finder-style file-list item, and activate the dialog's Open action. Entering a path into a filename field did not consistently select the intended file in the tested macOS dialogs.
- When the live CUA accessibility state advertises `Open Finder item`, `performSecondaryAction(currentIndex, "Open Finder item")` successfully opened folders and LUT files where plain item clicks or keyboard navigation had no effect. Use only actions exposed by the current state, with freshly observed indexes.
- For Save As, set the destination folder and the actual filename field separately, then verify both before Save. A folder navigation action is not a filename change.
- Pasting a complete POSIX output path into the tested Save As filename field converted slashes into filename characters rather than navigating. If folder navigation is unreliable, a unique temporary local export followed by a verified filesystem move is a workable fallback; do not overwrite an existing output.
- After every file dialog, verify the loaded item or saved path in Premiere and on disk. Recover from the visible current state instead of repeating blind keystrokes.

## Identify and transform camera color once

1. Inspect camera metadata and sidecar XML before choosing a LUT. Camera model, filename, or a user's approximate profile name alone is insufficient.
2. The tested Sony FX3A sidecars reported `CaptureGammaEquation=s-log3-cine` and `CaptureColorPrimaries=s-gamut3-cine`: S-Log3/S-Gamut3.Cine. `CodingEquations=rec709` was the coding matrix, not evidence that log footage was already display-ready. ffprobe transfer/primaries can be absent.
3. For that profile, the official Sony `SL3SG3Ctos709.cube` gave a useful s709 starting point. Obtain it from Sony's [camera knowledge page](https://www.sony.jp/ls-camera/knowledge/) / [s709 archive](https://www.sony.jp/ls-camera/knowledge/data/s709Cubes.zip), or a verified existing copy. Preserve the source URL, original archive, LUT filename, checksum, and transform assumptions with the project.
4. Confirm the LUT's expected input gamut/gamma and target display space. This particular file is for S-Log3/S-Gamut3.Cine to an s709 display rendering; it is not a generic Sony LUT for every profile.
5. Inspect Premiere's automatic color management, source interpretation, Input LUT, Creative Look, adjustment layers, and nested effects. Use one intended log-to-display transform. Do not stack the same transform at source, angle, and program levels.
6. When RODE program/ISO footage is established to contain a rendered display look, do not add another Sony log conversion. Recorder tags alone do not establish that transform; distinguish a practical grading assumption from verified capture provenance.

### Recorder ISO provenance and separate color trials

- Treat a sample studio guide as contextual setup guidance. A guide naming S-Cinetone and a user's recollection of S-Log can disagree without establishing either for the supplied recording. Record the competing evidence and inspect the actual files and available sidecars; avoid silently turning an old setup example into capture metadata.
- Probe each delivered angle for codec, pixel format/bit depth, resolution, range, transfer, primaries, matrix and encoder. RODE ISO files can be 8-bit HD with Rec.709 tags yet contain no original Sony profile or LUT identity. “ISO” means a separately recorded input, not necessarily an ungraded internal camera original. Rec.709 tags and a finished-looking image do not identify the exact upstream transform.
- An output LUT baked into a camera's HDMI/SDI signal can survive in the external recorder's pixels. Distinguish that possibility from a monitor-only LUT or an embedded LUT file. Do not claim the recorder automatically applied or bypassed a LUT without evidence of the actual device, firmware and setup. A camera's higher internal bit depth does not establish the delivered recording's bit depth.
- When capture evidence supports an existing rendered look, refine it conservatively rather than guessing a log conversion. Inspect the entire native transform stack before adding anything. Lowering highlights may improve a bright region, but cannot reconstruct detail already clipped or quantized out of the source. Grade parameters belong to the inspected footage, not a universal recovery preset.
- Save and verify a separate project copy before changing shared angle nests. Duplicating only the main sequence does not isolate a grade inside a shared angle: every sequence using it in that project, including a trailer, can change. Keep the prior project and grade readback as the comparison baseline.
- Keep the trial editable in the intended per-angle Lumetri instance. Read component count and values before and after; modify the existing component rather than adding another on each attempt. Verify the saved native state as well as the rendered result, including the absence of an unintended second technical transform.
- Compare matched before/after native frames at identical source moments and under identical display assumptions. For three angles, an early/middle/late set gives nine source moments to compare. Review skin, practical lights, windows, gradients and shadow texture, including each angle's nested appearance in the full edit and trailer. A separately graded contact sheet is not proof of the saved Premiere look; these samples do not certify every frame.
- Preserve editorial timing and audio. Compare clip bounds, routing, mute/gain state and automation, then decode a native PCM export and verify it matches the prior intended audio sample-for-sample when the trial changes picture only. Report color-frame review and audio preservation separately; do not describe an unfinished full export as validated.

### Verify a LUT actually loaded

- `apply_lut` in the tested MCP build returned `success:true` and “LUT applied” without establishing a visibly working transform. Treat the reply as a request acknowledgment, not color QA.
- The inspected `color_correct` implementation added a Lumetri instance on each call. For an existing grade, inspect components and use `set_effect_property` on the intended component with parameter readback instead of repeatedly adding new effects. The inspected `batch_apply_effect` and `add_adjustment_layer` implementations did not honor their advertised scope/behavior reliably; verify a small test or use native UI before relying on either.
- Inspect Lumetri in the GUI on the intended source/angle clip. If the transform is absent or unchanged, use Basic Correction > Input LUT > Browse and select the actual `.cube` through the native chooser.
- Re-read the clip's Lumetri component state. In this build its packed `Blob` could be decoded for inspection and contained the LUT path. A path string alone is insufficient: also verify the GUI selection and the visible transformed picture.
- Do not write opaque Lumetri Blob payloads copied from another clip or version. Use supported controls; use Blob inspection only as corroborating readback.
- Check each camera, including its nested appearance in the program, before batching or saving the final grade. Remove unintended duplicate Lumetri effects only after identifying them.

### Match and review

- Compare synchronized frames from early, middle, and late in the conversation across all cameras. Judge skin, neutral objects, shadow texture, bright windows, and saturation under the same display assumptions.
- Begin with the verified transform alone. Add exposure, white balance, or contrast adjustments only for visible mismatches; do not force every camera's overall histogram to match a different composition.
- In the tested episode, LUT-only close-ups were already close to the RODE reference. The backlit wide angle benefited from a small optional lift: Exposure +0.15, Shadows +12, Highlights −10. These are an example to evaluate visually, not a preset for future shoots.
- Be conservative with 8-bit HD sources: avoid aggressive saturation/contrast and check gradients, skin, and upscale framing. Bit depth and resolution can differ across cameras even when their models match.
- Inspect representative native rendered frames as well as analytical LUT previews. An independently graded FFmpeg contact sheet validates a proposed look, not the effects currently saved in Premiere.
- State the extent of QA accurately: sampled frames can establish those samples, not prove that an entire long episode is free of framing or color issues.

## Export and validate the real result

### Verify transition placement in the native result

In one tested bridge call, `add_transition_to_clip` with `position: start` reported success but wrote a tail fade. Read-only inspection of the saved `.prproj` established the actual placement. Treat this as an observed wrapper failure, not a universal Premiere behavior. Inspect the native transition bounds/effect state and rendered join before relying on that argument or retrying it.

The exercised recovery used an explicit native Volume ramp over the first 100 ms at the incoming clip's source-in, plus a 100 ms Constant Power tail fade on the outgoing clip at two joins. Confirm the keyframe time domain, source-in, clip bounds and preservation of speech in each case. These are separate head/tail fades; they do not establish an overlapping audio crossfade. A crossfade claim requires verified overlapping source coverage and the actual native transition/rendered sound.

### Export checks

- Run `validate_project_for_export` where available and interpret its scope. Without an output path or preset, “ready” may cover only timeline/media readiness; review warnings.
- The tested MCP `export_sequence` depended on Adobe Media Encoder and returned `MEDIA_ENCODER_NOT_INSTALLED` without dispatching an export. In that case, use Premiere's direct GUI Export workflow; a native export does not require installing AME just to satisfy that MCP wrapper.
- Confirm the intended sequence, export range, output filename/folder, format, frame rate, dimensions, audio configuration, and destination in the live UI. Verify the chosen action exports locally rather than queues elsewhere.
- Start with a short native preview that includes every camera and relevant transition. Confirm the output exists, has completed writing, probes correctly, and decodes without errors.
- Extract actual exported frames and compare their angles, source moments, grade, and scaling with the edit manifest. Do not substitute a separately assembled render as proof of the native project.
- Listen to the actual native preview and verify sync/audio independently. Complete picture QA and timeline checks do not establish the exported sound is correct.
- Save the native project after validated changes and document the preview's actual duration and settings. Keep interchange, native project, and review export clearly identified in the handoff.
