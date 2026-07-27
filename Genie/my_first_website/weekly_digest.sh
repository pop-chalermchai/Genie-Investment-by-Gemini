#!/bin/bash
#
# Weekly investment digest — DRAFT ONLY.
#
# Runs the /daily-digest research + drafting steps unattended (steps 1-3 of
# .claude/skills/daily-digest/SKILL.md) and stops before publishing. Nothing
# reaches the shared feed until a human reviews the draft and runs
# insert_feed_items.py, which keeps the skill's "never auto-publish" rule
# intact even though the run itself is automated.
#
# Scheduled by ~/Library/LaunchAgents/com.genie.weekly-digest.plist
# (Sundays 08:00; launchd runs it on wake if the Mac was asleep).
#
# Manual test: ./weekly_digest.sh

set -uo pipefail

PROJECT_DIR="/Users/popular/Desktop/Genie/my_first_website"
DIGEST_DIR="/Users/popular/Desktop/Genie/digests"
LOG_DIR="$DIGEST_DIR/logs"
RUN_DATE=$(date +%Y-%m-%d)

JSON_OUT="$DIGEST_DIR/draft_${RUN_DATE}.json"
MD_OUT="$DIGEST_DIR/draft_${RUN_DATE}.md"
LOG_FILE="$LOG_DIR/${RUN_DATE}.log"

mkdir -p "$DIGEST_DIR" "$LOG_DIR"

# launchd starts jobs with a bare PATH — claude lives under nvm.
export PATH="/Users/popular/.nvm/versions/node/v24.17.0/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

notify() {
    /usr/bin/osascript -e "display notification \"$2\" with title \"$1\" sound name \"Glass\"" >/dev/null 2>&1
}

exec >>"$LOG_FILE" 2>&1
echo "===================================================="
echo "Weekly digest draft run — $(date '+%Y-%m-%d %H:%M:%S')"
echo "===================================================="

if ! command -v claude >/dev/null 2>&1; then
    echo "❌ claude CLI not found on PATH: $PATH"
    notify "Genie digest failed" "claude CLI not found — see $LOG_FILE"
    exit 1
fi

cd "$PROJECT_DIR" || { echo "❌ cannot cd to $PROJECT_DIR"; exit 1; }

# Watchdog: a research run over ~30 tickers takes a while, but it should never
# sit forever holding a launchd slot.
( sleep 3600; echo "⏱️  watchdog: 60 min elapsed, killing run"; kill -TERM $$ 2>/dev/null ) &
WATCHDOG=$!

# Heredoc goes to a temp file rather than $(cat <<EOF): bash 3.2 (macOS system
# bash) mis-parses apostrophes inside a heredoc nested in command substitution.
PROMPT_FILE=$(mktemp -t genie-digest-prompt)
trap 'kill $WATCHDOG 2>/dev/null; rm -f "$PROMPT_FILE"' EXIT

cat >"$PROMPT_FILE" <<PROMPT_END
Run steps 1-3 of the daily-digest skill (.claude/skills/daily-digest/SKILL.md)
for an unattended weekly run dated ${RUN_DATE}. Read that file first and follow
it exactly — ticker universe, source restrictions, the 7-day freshness cap, and
the real-news-date rule for item_date all still apply.

This run is DRAFT ONLY. Two hard rules:
  1. Do NOT publish. Never run insert_feed_items.py, never write to Supabase,
     never touch feed_items. A human reviews and publishes separately.
  2. There is no user to answer questions — do not ask any. If a ticker has
     nothing notable within the last 7 days from an approved outlet, skip it
     silently rather than stretching the window or weakening the source bar.

Write two files when the draft is done:

  ${JSON_OUT}
    A JSON array, ready for insert_feed_items.py — each element exactly the
    schema in the skill: item_date, item_type, tickers, summary, th_summary,
    source_name, source_url. Do NOT set digest_date; the publish script stamps
    it. Include th_summary (Serene's voice) for every item.

  ${MD_OUT}
    A human review page in markdown:
      - Title with the run date and item count
      - Macro items first, then ticker items, newest item_date first
      - Each item: date, tickers, English summary, Thai summary, and a
        markdown link to the source
      - A "Skipped" section at the end listing every ticker in the universe
        with no qualifying news, so the reviewer can tell "no news" apart
        from "the search missed it"
      - Close with the exact publish command:
        cd ~/Desktop/Genie/my_first_website && python3 insert_feed_items.py ${JSON_OUT}

Finish by printing one line: DRAFT_ITEMS=<number of items written>
PROMPT_END

# Narrow allowlist: research + drafting only. Bash is limited to `python3 -c`
# (the sqlite ticker-universe query in step 1) so the publish script is not
# reachable even if the model tries.
claude -p "$(cat "$PROMPT_FILE")" \
    --allowedTools "WebSearch,WebFetch,Read,Write,Glob,Grep,Bash(python3 -c:*)" \
    --permission-mode dontAsk \
    --output-format text
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo "❌ claude exited with status $STATUS"
    notify "Genie digest failed" "claude exited $STATUS — see $LOG_FILE"
    exit $STATUS
fi

if [ ! -f "$JSON_OUT" ]; then
    echo "❌ run finished but no draft at $JSON_OUT"
    notify "Genie digest failed" "no draft file written — see $LOG_FILE"
    exit 1
fi

COUNT=$(python3 -c "import json,sys; print(len(json.load(open('$JSON_OUT'))))" 2>/dev/null || echo "?")
echo "✅ draft ready: $COUNT item(s) → $JSON_OUT"
notify "Genie digest ready" "$COUNT items drafted — review draft_${RUN_DATE}.md then publish"
