# From an edited episode to a trailer

## 1. Establish the brief and current source

Determine target length, aspect ratio, audience, destination, and whether this is an episode opening or a standalone social clip. Infer sensible defaults from supplied trailers and the live sequence when clear. A 30–60 second range is an editorial constraint, not a requirement to fill exactly sixty seconds.

Read the existing project and any relevant episode notes. Confirm which sequence is the current formal edit and which is the cleaned bonus/pre-intro. Record their IDs, frame rate, native source bounds and microphone/camera mapping. Never infer the visible person solely from a folder named HOST or GUEST; the worked episode's folder labels and people differed.

Save the current project and preserve a checkpoint or duplicate. A newly exported FCP XML can record the latest timeline structure, but it does not supersede the native project or prove a round trip preserves all grading/effects. Avoid rebuilding from stale XML merely to add titles.

## 2. Find compelling excerpts without distorting them

Search transcripts for surprises, concrete consequences, useful disagreements, practical advice, memorable anecdotes and unresolved questions. Read the surrounding exchange before selecting a quote. The formal episode and pre-intro may both contain strong material.

Build a shortlist with source sequence, candidate interval, exact spoken text, speaker, missing context and reason to include it. A practical progression is a specific hook, a useful contrast/question, and an unresolved payoff. Three to five moments can work, but preserve coherent thoughts over a rigid clip count.

Keep material qualifiers such as “seems,” “in this case,” or “I still have not found.” Preserve an answer's original question and reactions. Do not present one informal CAD/game experiment as a controlled benchmark. Use a concise context label if an excerpt omits its subject; label factual context separately from verbatim words.

## 3. Translate transcript clocks into native edits

Transcripts locate candidates; current native clip bounds determine placement. The formal sequence, cleaned bonus, raw recorder audio and camera files may all have different clocks. Preserve an ordered mapping of output start/end frames to source sequence and source in/out frames. A reordered trailer needs an explicit map even if the original episode was continuous.

Use integer frames and the rational rate. At 60000/1001 fps, 600 frames is 10.010 seconds. Premiere ticks are 254016000000 per second; this rate gives 4237833600 ticks per frame. Calculate for the actual rate rather than copying those frame counts blindly.

Trim with context and waveform evidence; ASR alone is not a phoneme-accurate cut list. Use the same keep-map for picture and both microphones. Preserve clean handles for short audio blends. Fixed-clock blend methods should not cumulatively shorten the trailer or reintroduce a deleted filler from the handles. When extensive filler cleanup is requested, use the available podcast skill's tested filler-cleanup workflow.

## 4. Assemble an editable timeline

Use current native graded angle nests. Keep a base wide-camera line and separate lines for each close-up when the user wants finely adjustable camera cut edges. Preserve the current speaker/camera choices unless revising them is in scope. Camera changes should not cut or duplicate continuous microphone audio.

Keep guest and host microphones separately named and adjustable. Preserve manually edited gains, mute states and handoff fades. Save audio counts, clip/source/timeline bounds and routing before structural video changes and compare afterwards. Native nested insertion may create linked or empty audio even with a video-only intent; remove only the verified newly created empty counterpart.

Put photos, screen demonstrations and context labels above cameras. Use the actual assets and actual demonstration timing. Existing readable screen footage can be used directly; transformations or presenter insets need a verified native pilot. Search connected repositories or Slack read-only when requested; discovering an asset does not authorize posting messages.

Keep existing suitable music when the user has chosen it. If selecting new music, establish the available license/source and assess tone against the conversation. Support dialogue rather than masking it. Do not treat a track's availability online as evidence of reuse rights.

## 5. Finish the content edit before word animation

Review the trailer's opening, every join, and ending. Check camera scale, grade continuity, audio handoffs, timing and context. Export a short real native preview to exercise nested effects and mixer routing. Preserve the approved source sequence.

Then use the kinetic workflow on a current picture/audio export. If dialogue edits change after animation starts, regenerate the affected word timing and explicitly map or rebuild the affected graphic interval. A full word animation pass against an obsolete trailer clock is wasted work.

For episode source synchronization, log grading, source relinking, isolated-mic processing or extensive filler removal, consult the available `premiere-podcast-editing` skill rather than expanding this trailer workflow into a second full-episode editor.
