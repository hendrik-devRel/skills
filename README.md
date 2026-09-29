# Skills

Agent skills packaged as a [Claude Code](https://claude.com/claude-code) plugin marketplace. Every skill is a plain `SKILL.md` folder, so it also works in any tool that reads the Agent Skills format (Codex, `.agents/skills/`, and others).

Two plugins are published here:

| Plugin | Skills | Use it for |
| --- | --- | --- |
| `better-typography` | 1 | Reviewing and fixing web typography in frontend code |
| `podcast-production` | 8 | Editing multicamera podcasts, trailers and Shorts in Adobe Premiere Pro and After Effects |

## better-typography

Web typography from choosing fonts to spacing, wrapping and accessibility. Nineteen principles, a review checklist, a common-mistakes table, and six reference files: choosing fonts, variable fonts and OpenType, spacing and sizing, wrapping and punctuation, details and accessibility, and a CSS cheat sheet with Tailwind equivalents. Every fix is expressed in the styling system the project already uses.

Triggers on typography, fonts, woff2, variable fonts, font-weight, OpenType, letter-spacing, line-height, type scale, heading hierarchy, tabular numbers, text-wrap, truncation, underlines, text selection, iOS input zoom, font smoothing, text contrast, and reviewing frontend code for typography.

## podcast-production

A suite of eight skills that grew out of producing a three-camera podcast. Episode-specific values inside the worked cases are examples, not defaults.

| Skill | Use it for |
| --- | --- |
| `premiere-podcast-editing` | Full-episode edits in Premiere Pro: camera and microphone sync, speaker-led cuts, log grading, dialogue balance, muting inactive microphones, filler removal with smooth blends, screen inserts, presenter picture-in-picture, and verified exports. |
| `podcast-multicam-editor` | Config-driven, non-destructive multicam edits as editable Premiere XML: role-based camera and mic mapping, sync and drift checks, FULL plus separately tightened sequences, removal lists, cut CSVs, and an XML validator. |
| `podcast-trailer-editing` | Opening trailers from an existing edit: excerpt selection, source-clock mapping, speech-timed kinetic typography in After Effects, alpha overlays, and preview audio checks. Includes an editable worked pilot. |
| `podcast-shorts-editing` | Standalone social clips: complete-idea passage selection, portable portrait and landscape layouts, speech-timed captions, speaking-turn audio tracks, and verified review exports. |
| `product-story-editing` | Shaping recorded product or company interviews into vision, mission, origin or product stories with take comparison and source-linked selects. |
| `audio-restoration` | Local click, buzz and hiss repair for speech WAV files with measured noise profiles and matched before/after previews. |
| `premiere-pro-mcp` | Installing, verifying and operating the Adobe Premiere Pro MCP server and its CEP bridge. Connection instructions only. |
| `use-after-effects` | Setting up and using the Higgsfield "use After Effects" MCP for native AE projects. Connection instructions only. |

### Requirements

- Adobe Premiere Pro, and After Effects for the trailer typography work.
- Python 3.9 or newer. The XML builders and validators use the standard library only.
- The audio helpers (filler cleanup, streaming preview audio, audio restoration) need `numpy`, `scipy` and `soundfile`.
- `ffmpeg` and `ffprobe` for media probing and previews.
- The Premiere Pro and After Effects MCP servers are not bundled. The two connection skills explain how to install them.

### About the bundled media

`podcast-trailer-editing/assets/worked-pilot/` contains a compact copy of one finished ten-second pilot: an editable After Effects project, its background video, native audio, rendered preview and layout measurements. About 50 MB in total. It is a worked example to open and relink, not a template. Plus Jakarta Sans SemiBold and IBM Plex Mono must be installed for the AEP to render as designed.

## Install in Claude Code

```
/plugin marketplace add hendrik-devRel/skills
/plugin install better-typography@hendrik-skills
/plugin install podcast-production@hendrik-skills
```

## Install anywhere else

Copy a skill folder into your agent's skills directory:

```sh
git clone https://github.com/hendrik-devRel/skills.git
cp -r skills/plugins/better-typography/skills/better-typography ~/.claude/skills/
cp -r skills/plugins/podcast-production/skills/* ~/.codex/skills/
```

The podcast skills link to each other with relative paths, so keep them side by side in the same skills directory.

## Layout

```
.claude-plugin/marketplace.json
plugins/
  better-typography/
    .claude-plugin/plugin.json
    skills/better-typography/          SKILL.md plus six reference .md files
  podcast-production/
    .claude-plugin/plugin.json
    THIRD-PARTY-NOTICES.md
    skills/
      premiere-podcast-editing/        SKILL.md, references/, scripts/, assets/
      podcast-multicam-editor/         SKILL.md, references/, scripts/
      podcast-trailer-editing/         SKILL.md, references/, scripts/, assets/
      podcast-shorts-editing/          SKILL.md, references/, scripts/, assets/
      product-story-editing/           SKILL.md, references/
      audio-restoration/               SKILL.md, references/, scripts/
      premiere-pro-mcp/                SKILL.md
      use-after-effects/               SKILL.md
```

## Running the bundled tests

Each skill with scripts ships its own unit tests:

```sh
cd plugins/podcast-production/skills/<skill-name>
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

## Provenance and license

MIT, see `LICENSE`. `better-typography` originated in CodeRabbit's content-studio repository. The podcast skills were developed for The Merge podcast by CodeRabbit. `premiere-pro-mcp` and `use-after-effects` are copied from their upstream projects; see `plugins/podcast-production/THIRD-PARTY-NOTICES.md`.
