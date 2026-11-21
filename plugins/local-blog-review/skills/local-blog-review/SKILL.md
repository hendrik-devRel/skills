---
name: local-blog-review
description: Run a local review of a blog article or website page. Serves the site on localhost with a commenting layer so the user can select text or click a block, leave comments, and have them saved to a JSON file that Claude then works through. Use this whenever the user wants to review, proofread, annotate, mark up or leave feedback on a blog post, article draft, docs page or PR preview before it ships; asks for a "local review", "localhost review" or "review UI"; says they would rather not comment in Google Docs; or asks to "pick up", "work through" or "implement my comments". Also offer it yourself when you have finished writing or rewriting an article and the next step is the user's review.
---

# Local blog review

A review loop that stays on the user's machine. The user reads the real, rendered article in a browser, marks
what they want changed, and the comments land in a file. Claude reads the file, makes the changes, and answers
each comment where the user left it.

It exists because reviewing in a separate document loses the link between a comment and the rendered page:
the layout, the figures and the surrounding text. Here the comment is anchored to the exact words on the page.

## What is in this skill

- `scripts/server.mjs` starts the site's dev server and serves it through a loopback proxy that adds the
  commenting layer. No dependencies; needs Node 18 or newer.
- `scripts/overlay.js` is the commenting layer the proxy injects into every page.
- `scripts/setup.sh` creates or refreshes an isolated copy of the site to review.

Nothing is added to the website's repository, so review tooling cannot ship to production.

## The workspace

Each project gets one workspace folder, `article-review/` by default, holding:

- `comments.json`: every comment.
- `review.config.json`: how to run this site (see below). Write it on first use so later reviews are one step.
- `site/`: the isolated copy of the site, when one is used.

Keep the workspace out of version control, or at least `site/` and `comments.json`. Comments are the user's
working notes and may quote unpublished copy.

`review.config.json` fields, all optional:

```json
{
  "repo": "../website",
  "ref": "feature/my-article",
  "app": "apps/front",
  "prepare": "corepack pnpm run codegen",
  "open": "/blog/my-article",
  "cmd": "",
  "target": ""
}
```

`app` is the subfolder holding the site's `package.json` in a monorepo. `prepare` is any step the site needs
before its dev server can start. `open` is the page to land on. `cmd` overrides the dev command (`{port}` is
replaced). `target` points at a site that is already running. `repo`, `ref` and `prepare` are for `setup.sh`;
pass them as flags.

## Starting a review

1. **Find out how the site runs.** Read the site's `package.json` and its contributor notes (`AGENTS.md`,
   `CLAUDE.md`, `README`). You need the app folder, the dev command, and whether anything must be generated
   first. If a `review.config.json` already exists, use it.

2. **Choose what to serve.** This decides whether the user sees edits live.
   - *The working checkout* (`--site-dir <checkout>/<app>`): edits you make appear in the browser through hot
     reload. Use it when nothing else is running a dev server in that checkout and no other session is
     editing it.
   - *An isolated copy* (`scripts/setup.sh`): a detached git worktree in `article-review/site`. Use it when
     another session or dev server is using the checkout, or when the user wants to review exactly what is
     pushed. It shows committed work only, so re-run `setup.sh` after new commits to refresh it.

   ```bash
   scripts/setup.sh --repo ../website --ref feature/my-article --app apps/front --prepare "corepack pnpm run codegen"
   ```

3. **Start the server.** If the session has a browser preview tool, add a launch entry that runs
   `node <skill>/scripts/server.mjs --dir article-review` on port 4710 and start it that way, so the user
   sees the page beside the chat. Otherwise run the command in the background. The first page load can take
   a while because the site compiles on demand; the page shows "Starting the local site" and reloads itself.

4. **Check it before handing over.** Load the article, confirm the "Comments" button is there, and confirm
   the page is the version the user expects. Then tell the user the address and how to comment.

## What to tell the user

Keep it to these four things:

- Select text and press **Comment** to comment on those words.
- Option-click a paragraph, table or figure to comment on the whole block.
- **Comments** (bottom right) lists everything; clicking a quote jumps to it.
- Say "work through my comments" when ready.

## Working through comments

Read `comments.json` and handle every comment whose `status` is `open`. Each has:

| Field | Meaning |
|---|---|
| `path` | Page it was left on, for example `/blog/my-article` or `/ja/blog/my-article` |
| `section` | Nearest article heading above it |
| `quote` | The exact words selected, or the start of the block |
| `prefix`, `suffix` | Text just before and after, to tell repeated phrases apart |
| `kind` | `text` for a selection, `block` for a whole paragraph, table or figure |
| `comment` | What the user wants |
| `status` | `open` or `done` |
| `reply` | Claude's answer, shown under the comment in the browser |

For each open comment:

1. **Find the source.** Search the article's source file for the quote. Rendered text differs from source:
   smart quotes, markup, links and figure embeds get in the way, so search for a distinctive few words and
   use `section` to narrow it. A quote inside a chart or figure usually lives in a component or data file,
   not the article.
2. **Make the change the comment asks for**, and only that. A comment is about its own words; do not take it
   as licence to rework the paragraph around it.
3. **Follow the repository's own rules** for that content: translations that must stay in step, generated
   images, validation and formatting checks. A comment on one language version normally means the other
   versions change too.
4. **Answer it.** Set `status` to `done` and write one or two plain sentences in `reply` saying what changed.
   The browser picks this up within a few seconds.

When a comment is unclear, or you disagree with it, do not guess and do not silently skip it. Leave it `open`,
put your question or concern in `reply`, and raise it in the chat. The user decides.

Never delete comments or rewrite the user's `comment` text; the file is their record of the review. Edit the
file with a small script or careful edits that keep it valid JSON, since the server reads it on every request.

After the batch, tell the user what was done and what is still open. If the site is an isolated copy, commit
as the user has asked and refresh the copy so they can see the result. Commit or push only when the user asks.

## When something looks wrong

- **"text changed" on a comment:** the words it pointed to are gone, usually because they were rewritten.
  The comment is kept; `section` and `quote` still say what it was about.
- **No highlight but the comment is listed:** highlights need a current Chrome, Edge or Safari. Everything
  else still works.
- **Port in use:** pass `--port` and `--site-port`.
- **The site will not start:** run its dev command by hand in the site folder to see the real error. A
  missing generation step is the usual cause; put it in `prepare`.
- **Two dev servers in one checkout:** many frameworks refuse this. Use an isolated copy, or pass
  `--target http://localhost:<port>` to review a site that is already running.
- **Comments attach to the wrong area:** the layer treats the page's `<article>` (or `<main>`) as the
  article. On a site without either, comments still save but are matched against the whole page.
