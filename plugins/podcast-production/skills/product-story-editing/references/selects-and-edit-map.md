# Selects and edit-map contract

Use the smallest table or JSON structure that preserves the relationships below. The field names are suggestions, not a required interchange format. A readable proposal and machine-readable map should describe the same version of the edit.

## Sources and evidence

Give each media input a stable `source_id` and a relative filename or external-media token. Keep machine-specific absolute paths in a separate local relink table. Record whether sources are consecutive chunks, simultaneous independent recordings, shared mixes, backups or still unresolved. Link to measured synchronization evidence instead of inventing an offset from file order.

Keep the transcript's source ID, clock and model/review status. Corrected text should retain its relationship to raw ASR; do not silently replace uncertain words. A speaker role or name can remain provisional independently of the timestamp.

## Candidate selects

For each candidate, retain:

| Field | Purpose |
| --- | --- |
| Select ID, source ID, source in/out and clock | Locate the actual words. Use per-file seconds for a rough transcript plan; identify estimates explicitly. |
| Speaker and verification status | Avoid attributing a director's read-through to the presenter. |
| Verbatim text and correction status | Separate recorded wording from an editorial summary. |
| Original question/context | Preserve the question answered, antecedents and necessary qualifications, including relevant source intervals. |
| Story beat and inclusion reason | Explain what this passage contributes to the chosen argument. |
| Dependencies and unresolved evidence | Record retained questions, uncertain words, missing history, product-scope checks or required surrounding passages. |

Store rejected alternatives separately from selected material. A shortlist is not the approved output order, and selection does not establish that the source was heard or visually reviewed.

## Ordered assembly

For every retained span, map its select/source ID and exact source interval to an output interval. Split a span whenever it crosses removed material; do not represent a stitched sentence as one continuous original interval. Retain camera source choices separately from the dialogue source.

Before native construction, resolve rough boundaries to the actual rational frame grid and appropriate audio sample clock. Declare half-open ranges `[in, out)` and units. Store the measured source-to-camera mapping or its version rather than recomputing an offset from output positions. Include any intended gaps, holds or overlaps explicitly so duration is reproducible.

Check ordered output coverage, positive source ranges, source coverage limits and duration arithmetic. These checks establish map consistency, not natural speech or factual fidelity. Listen to refined joins and review their original context; inspect the composed picture separately.

## Handoff and portability

Record the brief/script version, transcript revision, edit-map revision, native sequence/version when one exists, and performed review checks. Mark missing beats and remaining questions. Keep source recordings and private production examples outside the portable skill unless explicitly included for a separate worked example. Never convert case-specific identities, durations, offsets or camera roles into defaults.
