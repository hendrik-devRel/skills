# Current 10-second pilot: dialogue and word onsets

Source: `dialogue-first10.wav`, native output from current Premiere sequence, 10.010 seconds.

No one model had ever really passed the CAD bench until Astra just blew it away. So prompt engineering still plays a role, you say? Definitely.

The primary onsets below come from a new large-v3-turbo pass. Base.en independently agrees on the words apart from “you say” being decoded as “to say.” Times are ASR estimates, quantized to the nearest 59.94 fps frame; they are not a substitute for playback timing review.

|Word|ASR onset (s)|Frame @59.94|
|---|---:|---:|
|No|0.00|0|
|one|0.20|12|
|model|0.46|28|
|had|0.76|46|
|ever|0.92|55|
|really|1.12|67|
|passed|1.42|85|
|the|1.92|115|
|CAD|2.54|152|
|bench|2.74|164|
|until|3.10|186|
|Astra|4.04|242|
|just|5.12|307|
|blew|5.70|342|
|it|6.10|366|
|away.|6.26|375|
|So|7.00|420|
|prompt|7.10|426|
|engineering|7.34|440|
|still|7.74|464|
|plays|8.06|483|
|a|8.38|502|
|role,|8.50|509|
|you|8.94|536|
|say?|9.04|542|
|Definitely.|9.38|562|

Build complete phrases in fixed positions, revealing one word at each onset. Hold CAD BENCH after it completes; start a fresh stack for “until ASTRA just BLEW IT AWAY”; clear at the change to the prompting question. Keep DEFINITELY visible through the pilot endpoint.

Timing cautions: “the,” “until,” and “Astra” absorb pauses in the ASR; engineering/still onsets differ by as much as0.18s between models. Listen during the finalpilot review before claiming frame-accurate sync. The last word ends in ongoing speech, not an established natural break.
