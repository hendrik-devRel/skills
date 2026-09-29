# Adapt an approved portrait edit to landscape

Use this when the user wants the same approved passages as horizontal social clips.
Preserve the editorial/audio decisions unless a framing problem calls for a local change.
A landscape version should use the landscape camera originals or graded angle precomps;
enlarging a finished portrait MP4 loses source detail and bakes in its old typography.

## Preserve the approved edit

- Save a separate native project and composition set. Record the source manifest/project
  fingerprint and keep the portrait exports unchanged. Use distinct horizontal filenames.
- Reuse the source-to-program mapping, total frames, source camera offset, word onsets,
  cleaned dialogue and real speaker turns. Copy approved native layers when that preserves
  local fixes more reliably than rebuilding from an earlier generator.
- Compare the resulting native layers with the source: audio item IDs and timing;
  camera in/out/start times and enabled state; caption word sequence and in/out points.
  Rewrapping text must retain the same word order and reveal keys.
- Replace portrait-panel sources with the original graded landscape angles. Preserve
  camera time mapping and mute source-camera audio. Keep disabled alternate angles editable.
  For a moderator visible only in the shared wide, use the authentic wide rather than
  pretending that the portrait crop is a separate camera.
- Preserve accepted grading. Reframing is not a reason to apply a second log transform.
  Speaking-turn tracks selected from a shared mix remain shared mixes.

## A landscape architecture that worked

The [landscape layout configuration](../assets/landscape-layout.json) records a 1920×1080
example. A 480px editorial rail sits beside a 1440×810 full landscape image; a 96px header
and a separate caption band keep all authored text off the speakers. The picture uses
the complete 1920×1080 source at 75% scale, centered at `[1200,501]`.

Use the rail for the hook, then a few changing ideas with explanatory context. A small
chapter index distinguishes editorial summaries from the spoken captions. Keep important
qualifiers visually attached to the claim, such as “of new capacity” beside a percentage.
Place the current speaker's identity in the rail. Use the same palette/typefaces as the
accepted set, with the real logo in the header and a quiet progress line.

Recompose title line breaks deliberately instead of shrinking a long line to fit. In
this example, openings used 46–52px Plus Jakarta SemiBold and subsequent headings 46px,
with context at about 27px. Long unbreakable words still need measured fitting. The rail
heading, context and identity occupy distinct vertical zones; test all beats, not only
the opening. The exact sizes are a starting point for this source, not universal defaults.

Rewrap the speech captions at 58px into at most two rows across the lower picture width.
Keep their word-based opacity selector and original hold keys. Setting new text/style can
reset character ranges, so reapply emphasis after wrapping. Do not animate glyph width to
force a fit. Use native bounds after editing: the second row, punctuation overhang and
descenders can exceed an offline width estimate. In the worked adaptation, caption bounds
were below the picture and ended before the canvas edge; this is a measured result for
that set, not a guarantee for replacement text.

## Verify the adaptation before batch rendering

Check an opening, the longest heading, both founder singles, the moderator's wide and a
real speaker handoff. Inspect a native motion proof through that handoff; full-frame stills
alone do not verify timing. Test an actual text replacement in a temporary duplicate, then
remove only that check composition. Verify installed fonts, missing media and saved state.

Record unchanged duration/audio/camera/caption invariants. Preserve the existing approved
word endings. During wide covers, ensure the layer fully occludes the underlying single;
bound a cover to the source span it belongs to. Turn-map entries split at a source edit are
not necessarily speaker changes.

Render at the requested landscape dimensions and the source rational frame rate. Use the
[resource workflow](adobe-resource-checks.md) for short exact native ranges if needed, and
[delivery verification](verification-delivery.md) for concatenation, fresh AAC from approved
PCM, full decode, exact frames and distributed audio alignment/tail checks. A changed aspect
ratio does not justify loosening audio verification. Rebuild contact sheets and the review
gallery for 16:9 and check links to this version's MP4s and editable project.

## Uploading both formats

When the user authorizes upload, resolve the actual project and existing vertical/horizontal
folders live. Use the current Frame.io upload workflow if available. Upload only the requested
approved MP4s into the correct format folder, check same-name collisions before submitting,
and verify the exact final names/count. Distinguish finished upload from ongoing preview
processing. Keep internal folder/asset links and local hashes in the episode evidence;
publishing social posts or creating public share links is a separate action.

The repeatable skill contains the layout and workflow. Keep episode footage, the native
project, private transcript, machine-specific item IDs and upload receipts with the episode.
