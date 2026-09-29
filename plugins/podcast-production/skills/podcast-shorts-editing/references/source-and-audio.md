# Source clocks, edit manifest and honest audio control

## Audit the actual available media

Confirm speaker identities and camera mapping from actual frames or reliable records; host/guest filenames can be misleading. Probe source dimensions, rational frame rate, color metadata, audio rate/channel layout and available duration. Verify missing media and installed fonts before building many compositions. Record the accepted native camera-grade sources and which cleaned audio is authoritative.

The worked source was already display-referred HD Rec.709 despite Sony log capture upstream. Its accepted Lumetri corrections were preserved inside named angle precompositions. Applying another S-Log conversion would have transformed the material twice. The reusable rule is to establish the current file's state, not copy this episode's correction values to new footage.

## Use one authoritative edit manifest

Keep frame counts and rational frame rate canonical; derive seconds and audio sample positions. A useful manifest contains:

| Field | Purpose |
|---|---|
| `fps: [numerator, denominator]`, canvas, audio rate | The actual delivery clock and format |
| Media roles and speaker/camera mapping | Local files, verified identities and a consistent speaker-color legend, separate from historical native IDs |
| Camera-to-recorder offset with units/sign | Calibrated synchronization applied once |
| Edited-master keep ranges | Original source intervals mapped into the accepted edited audio clock |
| Clip ID, title, editorial hook, output names | A stable identity across captions, files, QA and gallery |
| Retained source spans | Half-open intervals, cumulative output positions and exact frame counts |
| Speaker turns | Mapped into each retained output span, with overlap provenance |
| Raw/corrected words | Source clock, output clock, correction and uncertainty evidence |
| Caption groups and emphasis beats | Visible text, timing, layout and whether quote or editorial summary |
| Native project/comp identity and version | Readable topic/format names plus re-inspected IDs for the current app session |
| Review and handoff metadata | Playable review link/path, editable project and comp, approved audio file/version, editorial priority |
| Fingerprints and delivery status | Detect stale outputs and distinguish planned, rendered, verified and delivered clips |

The worked implementation's fields included `source_in/out`, `camera_in`, `full_audio_in`, `program_in/out`, `frames`, `words`, `turns`, `beats` and `total_frames`. These are a practical schema, not mandatory field names. Regenerate dependent audio, words, graphics, SRT and review durations after a timing change. Never reuse a filename's former duration as evidence of freshness.

## Map four clocks explicitly

Let the frame rate be `F = numerator/denominator` frames per second. Let a keep range map recorder frames `[a,b)` onto edited-master start frame `c`.

For recorder frame `r` inside that range:

`edited_frame = c + r - a`

For recorder seconds `t` inside the same span:

`edited_seconds = t + (c-a)/F`

For a selected recorder span beginning at `s` and cumulative output frame `p`:

`program_seconds = p/F + (t-s)`

If calibrated camera time equals recorder time plus offset `d`:

`camera_seconds = t + d`

State the offset sign and each input clock in the manifest. If supplied source times have no named clock, a provisional plan can state its assumption, but resolve that ambiguity before extracting or syncing actual media. In the worked episode it was negative 1024/48000 seconds; this is historical evidence, not a default. Map selections through every owning keep range; split at removed spans rather than pretending the accepted edited audio shares the original recorder clock. Reject uncovered source intervals until a deliberate source choice is made.

For output frame boundary `f` and audio rate `R`, use `sample(f) = round(f * R / F)` with an explicit rounding convention. Derive each segment's sample length by subtracting its two absolute sample boundaries, instead of independently rounding durations and accumulating drift. Quantize picture cuts once; preserve justified subframe speech handles in the audio plan. Use the source transcript clock for selection and the output clock for captions.

## Refine words in context

Retain raw ASR and store corrected production words separately. Transcribe candidate excerpts with context handles using an available local model. The worked set used cached Whisper large-v3-turbo, then focused checks and waveforms for disputed onsets. That model is an option, not a required install.

Word timestamps are estimates. ASR may stretch a word across room tone, compress repetitions or borrow a following word. Compare actual source excerpts, onset/tail measurements and the surrounding sentence. Keep explicit changes for names, acronyms, negations, numbers and speaker turns. The later production transcript and finishing decisions supersede earlier candidate maps.

After an internal removal, map every retained word through the appropriate span. Suppress words from removed material; a boundary tolerance is a search aid, not permission to show a word whose speech was cut. Corrected multiword tokens must be counted as their actual displayed words for native word selectors. An uncertain incidental clause can be omitted as a complete clause if meaning survives. Supported keywords may be used as selective emphasis while uncertain verbatim captions are suppressed. Do not invent a fluent quotation.

## Build dialogue without losing the accepted treatment

Use the latest accepted cleaned dialogue and map through its edit clock. Do not return to camera AAC when that loses approved leveling or reaction reduction, or apply the same restoration twice. When native footage reload retains a stale WAV duration, import/relink a uniquely versioned file and read back its duration; a successful reload message alone is insufficient.

If isolated microphones exist, preserve them separately. When only a shared mix exists, speaker-named tracks can hold speaking-turn selections from that mix. Label them `Turns-SHARED-MIX`; overlapping voices, bleed and reactions remain. The combined reference must not play on top of the turn tracks. Disable camera audio and any duplicate reference layer. Keep optional music independent; the accepted longer Shorts were dialogue-only.

For turn-selected shared mix, assign every retained sample exactly once. Verify the sum of the active turn stems equals the approved combined reference, including boundaries. A turn label is a control convenience, not source separation. With real isolated microphones, this partition invariant does not apply; mix them according to their actual content.

The worked audio builder used short 5 ms cosine edge fades on retained segments. Treat that as an initial anti-click treatment, not a cure for a clipped consonant. Preserve the complete word first. If a fade affects useful speech, revise the edit or use an appropriate overlap. Audition joins when possible; numerical similarity cannot certify natural delivery. Keep gain, rate and sample count stable unless the edit explicitly changes them.

## Keep analysis and native execution separate

Build local manifests and bounded operation batches before native execution. The episode's source-specific builders are implementation evidence, not portable scripts to run unchanged: they contain local paths, source ranges, historical IDs and per-episode corrections. Reconstruct/adapt their contracts with the new manifest and current catalog. Preserve the approved source project, create a versioned destination and save before handoff. Never operate another task's live Adobe instance without its release.
