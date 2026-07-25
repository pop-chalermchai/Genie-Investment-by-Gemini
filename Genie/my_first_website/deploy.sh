#!/bin/bash
# Deploy script for Genie Investment
#
# Usage:
#   ./deploy.sh          → deploy code to Vercel only (safe, no DB overwrite)
#   ./deploy.sh --sync   → sync local DB → Supabase, THEN deploy code
#
# WARNING: --sync overwrites all Supabase data with local SQLite.
# Only use --sync when you intentionally want to push local data to production.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ "$1" == "--sync" ]]; then
    echo "=== Step 1: Sync portfolio DB → Supabase ==="
    echo "⚠️  WARNING: This will overwrite all Supabase data with your local DB."
    read -p "Continue? (y/N) " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi
    cd "$SCRIPT_DIR"
    python3 sync_portfolio_to_supabase.py
    echo ""
fi

echo "=== Deploy → Vercel (genie-investment-by-gemini) ==="
cd "$GIT_ROOT"
npx vercel --prod

echo ""
echo "✅ Deploy complete — https://genieports.com"
