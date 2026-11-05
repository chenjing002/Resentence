#!/bin/bash
# Rebuild sentences.json from the Rewords export; commit and push when it changed and the network is up.
# Run by launchd (see install.sh).
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
REPO="$(cd "$(dirname "$0")" && pwd)"
SRC="${RESENTENCE_SRC:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Rewords/rewords-vocabulary.json}"
log() { echo "$(date '+%F %T') $*"; }

cd "$REPO" || exit 1
[ -f "$SRC" ] || brctl download "$SRC" 2>/dev/null
[ -f "$SRC" ] || { log "source not found: $SRC"; exit 0; }

python3 build.py "$SRC" >/dev/null || { log "build failed"; exit 1; }

if [ -n "$(git status --porcelain -- sentences.json)" ]; then
  n=$(python3 -c 'import json;print(len(json.load(open("sentences.json"))))')
  git add sentences.json
  git commit -q -m "Update sentences ($n cards)" && log "committed: $n cards"
fi

# Push only when there is something unpushed and GitHub is reachable.
ahead=$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo 1)
[ "$ahead" = "0" ] && exit 0
if ! curl -s --max-time 8 -o /dev/null https://github.com; then
  log "offline; $ahead commit(s) waiting"
  exit 0
fi
git pull -q --rebase origin main 2>/dev/null
if git push -q -u origin main; then log "pushed"; else log "push failed"; fi
