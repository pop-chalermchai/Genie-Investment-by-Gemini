---
name: daily-digest
description: Draft a daily investment digest (macro news + per-ticker news) and publish it to the Equity Research feed after review. Use when the user wants a summary of today's market-relevant news.
---

# Daily Investment Digest

Manual, on-demand digest — not scheduled. Searches for today's macro news and
news for every ticker in the union of portfolio holdings + equity research
coverage, drafts short bulletin items, and publishes them to the shared
`feed_items` table only after the user reviews and approves the draft.

## Steps

### 1. Build today's ticker universe
Query both sources and union them (no duplicates):

```bash
cd ~/Desktop/Genie/my_first_website && python3 -c "
import sqlite3
conn = sqlite3.connect('portfolio.db')
c = conn.cursor()
c.execute('SELECT DISTINCT ticker FROM assets')
holdings = {r[0] for r in c.fetchall()}
c.execute('SELECT DISTINCT ticker FROM research_reports')
coverage = {r[0] for r in c.fetchall()}
print(sorted(holdings | coverage))
"
```

Falls back to the `tickers` array in `insert_all.py` if `research_reports`
isn't populated locally.

### 2. Research
Use `WebSearch` to find:
- Key macro/economic news relevant to investors (rates, inflation prints,
  Fed commentary, major index moves)
- Recent news for each ticker in the universe from step 1

**Only use major, reputable financial outlets** — Reuters, Bloomberg, CNBC,
The Wall Street Journal, and Yahoo Finance. Discard results from anywhere
else (blogs, forums, low-quality aggregators, unverified social posts), even
if they seem relevant — accuracy and credibility matter more than coverage.

**Freshness — cap item age at 7 days.** WebSearch ranks by relevance, not
publish date, so it will surface things like a stock's 9-day losing streak or
an M&A deal from two weeks ago mixed in with today's breaking news. Discard
anything older than 7 days. For everything else, identify the actual date the
news broke (not today's date) and use that as `item_date` — items land under
their real date header in the feed, not bunched under the day the digest was
run. Skip a ticker if there's nothing notable in the last 7 days from these
sources — don't force an item or fall back to a weaker source just to fill a
gap.

### 3. Draft
Write each finding as one short item, in English first:

```json
{ "item_date": "YYYY-MM-DD", "item_type": "macro", "tickers": ["NVDA", "AMD"], "summary": "one-line summary", "th_summary": "หนึ่งบรรทัดสรุปเป็นภาษาไทย", "source_name": "...", "source_url": "..." }
```

`item_type` is `"macro"` or `"news"`; `tickers` may be empty for pure macro
items. `item_date` is the date the news actually happened, not the date the
digest is being run — it only controls each item's order *inside* the
digest when it's opened. The feed itself files the whole run as one row
under today's date (`digest_date`, auto-stamped by `insert_feed_items.py`);
don't set `digest_date` per item unless deliberately backfilling a past run.

**Thai translation:** draft `th_summary` for every item too — same persona
and tone as Serene's Thai research writing (see `research/*/04_Serene_*_TH.md`
for style reference). It's optional at the schema level (falls back to the
English `summary` in the UI if omitted), but include it by default; only skip
it if the user says otherwise for a given run.

Show the full drafted list (both languages) to the user in chat and wait for
explicit approval or edits — this is published, shared content the moment
it's inserted; do not publish without confirmation.

### 4. Publish
On approval, write the approved items to a JSON file and run:

```bash
cd ~/Desktop/Genie/my_first_website && python3 insert_feed_items.py <path-to-items.json>
```

This inserts straight into Supabase `feed_items` (same owner id as research
reports) — no local SQLite staging step, since these are lightweight,
non-versioned bulletins.

## Automated weekly draft (added 2026-07-27)

`weekly_digest.sh` + `~/Library/LaunchAgents/com.genie.weekly-digest.plist` run
steps 1-3 unattended every **Sunday 08:00** and stop there — publishing stays
manual, so the "never auto-publish" rule below still holds. Sunday cadence lines
up with the 7-day freshness cap exactly: no gaps, no overlap between runs.

Output lands in `Genie/digests/` (gitignored) as `draft_YYYY-MM-DD.json` (ready
for `insert_feed_items.py`) plus a `.md` review page, followed by a macOS
notification. Review the `.md`, then publish with the command printed at its end.

The runner passes a narrow `--allowedTools` list whose only Bash grant is
`Bash(python3 -c:*)` — enough for the step-1 SQLite query, not enough to reach
`insert_feed_items.py`. Publishing is blocked mechanically, not just by prompt
instruction. `--permission-mode dontAsk` keeps it from hanging on a prompt at
08:00 with nobody there, and a 60-minute watchdog kills a stuck run.

macOS TCC gotcha: launchd agents get no access to `~/Desktop` by default, so
`/bin/bash` needs **Full Disk Access** (System Settings → Privacy & Security).
Without it the job dies instantly with `Operation not permitted`.

## Notes
- Weekly draft is automated (see above); publishing is always manual
- Sources restricted to Reuters, Bloomberg, CNBC, WSJ, Yahoo Finance —
  no blogs, forums, or unverified aggregators
- Items older than 7 days are discarded; `item_date` is the news's actual
  date, not the digest run date
- The feed shows one run as a single "📰 Daily Digest" row filed under
  `digest_date` (the run date) — clicking it opens a reader listing every
  item on one page, sorted by `item_date` newest-first. A date can have a
  digest row, full research reports, or both.
- Every item gets a `th_summary` (Thai translation) by default alongside
  the English `summary`; UI falls back to English if it's missing
- Always show the draft before publishing; never auto-publish
- Ticker universe is computed fresh each run (union of live portfolio
  holdings + research coverage) — no hardcoded list to maintain as tickers
  change
- `insert_feed_items.py` always inserts (no upsert) — re-running with the
  same items creates duplicates; to fix a published item, delete it via
  `DELETE /api/feed-item?id=<id>` (admin-only) and re-publish
- Requires `DATABASE_URL` in `.env`
