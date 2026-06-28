#!/bin/bash
# Full deploy: push portfolio data to Supabase, then deploy to Vercel production.
# Run from any directory — this script resolves its own path.
# Usage: ./deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Step 1: Sync portfolio DB → Supabase ==="
cd "$SCRIPT_DIR"
python3 sync_portfolio_to_supabase.py

echo ""
echo "=== Step 2: Deploy → Vercel (genie-investment-by-gemini) ==="
cd "$GIT_ROOT"
npx vercel --prod

echo ""
echo "✅ Deploy complete — https://genie-investment-by-gemini.vercel.app"
