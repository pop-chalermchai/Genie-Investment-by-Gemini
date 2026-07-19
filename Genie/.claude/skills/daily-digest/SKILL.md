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
For today's date, use `WebSearch` to find:
- Key macro/economic news relevant to investors (rates, inflation prints,
  Fed commentary, major index moves)
- Recent news for each ticker in the universe from step 1

**Only use major, reputable financial outlets** — Reuters, Bloomberg, CNBC,
The Wall Street Journal, and Yahoo Finance. Discard results from anywhere
else (blogs, forums, low-quality aggregators, unverified social posts), even
if they seem relevant — accuracy and credibility matter more than coverage.

Skip a ticker if there's nothing notable that day from these sources — don't
force an item or fall back to a weaker source just to fill a gap.

### 3. Draft
Write each finding as one short item:

```json
{ "item_date": "YYYY-MM-DD", "item_type": "macro", "tickers": ["NVDA", "AMD"], "summary": "one-line summary", "source_name": "...", "source_url": "..." }
```

`item_type` is `"macro"` or `"news"`; `tickers` may be empty for pure macro
items. Show the full drafted list to the user in chat and wait for explicit
approval or edits — this is published, shared content the moment it's
inserted; do not publish without confirmation.

### 4. Publish
On approval, write the approved items to a JSON file and run:

```bash
cd ~/Desktop/Genie/my_first_website && python3 insert_feed_items.py <path-to-items.json>
```

This inserts straight into Supabase `feed_items` (same owner id as research
reports) — no local SQLite staging step, since these are lightweight,
non-versioned bulletins.

## Notes
- Manual only — no scheduled/cron run exists yet
- Sources restricted to Reuters, Bloomberg, CNBC, WSJ, Yahoo Finance —
  no blogs, forums, or unverified aggregators
- Always show the draft before publishing; never auto-publish
- Ticker universe is computed fresh each run (union of live portfolio
  holdings + research coverage) — no hardcoded list to maintain as tickers
  change
- `insert_feed_items.py` always inserts (no upsert) — re-running with the
  same items creates duplicates; to fix a published item, delete it via
  `DELETE /api/feed-item?id=<id>` (admin-only) and re-publish
- Requires `DATABASE_URL` in `.env`
