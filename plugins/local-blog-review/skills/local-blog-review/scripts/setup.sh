#!/usr/bin/env bash
# Prepare (or refresh) an isolated copy of a website for local review.
#
#   setup.sh --repo <git checkout> --ref <branch or ref> [--dir article-review] [--app <subfolder>] [--prepare "<command>"]
#
# Creates <dir>/site as a detached git worktree of <repo> at <ref>, installs dependencies, and runs
# an optional prepare command inside the app folder. Run it again to move the copy to a newer commit.
# The copy is separate from the working checkout, so reviewing never disturbs work in progress there.
set -euo pipefail

repo="" ref="" dir="article-review" app="" prepare=""
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) repo="$2"; shift 2 ;;
    --ref) ref="$2"; shift 2 ;;
    --dir) dir="$2"; shift 2 ;;
    --app) app="$2"; shift 2 ;;
    --prepare) prepare="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$repo" ] && [ -n "$ref" ] || { echo "usage: setup.sh --repo <checkout> --ref <branch or ref> [--dir <workspace>] [--app <subfolder>] [--prepare \"<command>\"]" >&2; exit 2; }

repo="$(cd "$repo" && pwd -P)"
mkdir -p "$dir"
site="$(cd "$dir" && pwd -P)/site"

# Prefer the pushed state of a branch; fall back to a local branch, tag or commit.
git -C "$repo" fetch --quiet origin "$ref" 2>/dev/null || true
if git -C "$repo" rev-parse --verify --quiet "refs/remotes/origin/$ref" >/dev/null; then
  target="refs/remotes/origin/$ref"
else
  target="$ref"
fi
commit="$(git -C "$repo" rev-parse --verify "$target^{commit}")"

if [ -e "$site/.git" ]; then
  if [ -n "$(git -C "$site" status --porcelain)" ]; then
    echo "The review copy at $site has local changes. Commit or discard them before refreshing." >&2
    exit 1
  fi
  git -C "$site" checkout --quiet --detach "$commit"
else
  git -C "$repo" worktree add --quiet --detach "$site" "$commit"
fi
echo "review copy: $site at $(git -C "$site" log -1 --format='%h %s')"

# Install with whichever package manager the site uses.
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
cd "$site"
pinned="$(node -p "(require('./package.json').packageManager||'').split('+')[0]" 2>/dev/null || true)"
if [ -n "$pinned" ]; then
  case "$pinned" in
    pnpm@*) corepack "$pinned" install --frozen-lockfile ;;
    yarn@*) corepack "$pinned" install --immutable ;;
    *) corepack "$pinned" install ;;
  esac
elif [ -f pnpm-lock.yaml ]; then corepack pnpm install --frozen-lockfile
elif [ -f yarn.lock ]; then corepack yarn install --immutable
elif [ -f package-lock.json ]; then npm ci
elif [ -f package.json ]; then npm install
fi

if [ -n "$prepare" ]; then
  (cd "$site/$app" && eval "$prepare")
fi
echo "ready: start the review server with --dir \"$dir\""
