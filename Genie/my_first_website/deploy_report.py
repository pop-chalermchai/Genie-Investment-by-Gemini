#!/usr/bin/env python3
"""
deploy_report.py — Genie research report deployment script

Usage (INSERT):
  python deploy_report.py --ticker RKLB --company "Rocket Lab USA" \\
    --sector "Aerospace & Defense" --rating "SPECULATIVE BUY" \\
    --positive --pt 130 --price 107

Usage (UPDATE existing report):
  python deploy_report.py --ticker RKLB --company "Rocket Lab USA" \\
    --sector "Aerospace & Defense" --rating "SPECULATIVE BUY" \\
    --positive --pt 130 --price 107 --mode update

File paths are auto-resolved from ticker convention:
  research/{TICKER}/03_Valerie_{TICKER}_Overview_AUDITED.md
  research/{TICKER}/04_Serene_{TICKER}_Overview_TH.md
  research/{TICKER}/03_Valerie_{TICKER}_ReverseDCF_AUDITED.md
  research/{TICKER}/04_Serene_{TICKER}_ReverseDCF_TH.md
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"
RESEARCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research")


def resolve_paths(ticker):
    t = ticker.upper()
    base = os.path.join(RESEARCH_DIR, t)
    return {
        "en_overview": os.path.join(base, f"03_Valerie_{t}_Overview_AUDITED.md"),
        "th_overview": os.path.join(base, f"04_Serene_{t}_Overview_TH.md"),
        "en_dcf":      os.path.join(base, f"03_Valerie_{t}_ReverseDCF_AUDITED.md"),
        "th_dcf":      os.path.join(base, f"04_Serene_{t}_ReverseDCF_TH.md"),
    }


def read_file(label, path):
    if not os.path.exists(path):
        print(f"  ERROR [{label}]: File not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    size_kb = len(content.encode("utf-8")) // 1024
    print(f"  {label}: {os.path.basename(path)} ({size_kb} KB)")
    return content


def deploy(args):
    ticker = args.ticker.upper()
    report_key = args.key or f"{ticker}_2026"
    paths = resolve_paths(ticker)

    print(f"\n[deploy_report] {ticker} — mode={args.mode}")
    print(f"  report_key : {report_key}")
    print(f"  company    : {args.company}")
    print(f"  sector     : {args.sector}")
    print(f"  rating     : {args.rating} (positive={args.positive})")
    print(f"  PT ${args.pt}  |  analysis price ${args.price}")
    print(f"  Loading markdown files...")

    payload = {
        "report_key":    report_key,
        "ticker":        ticker,
        "company_name":  args.company,
        "subtitle":      args.subtitle or f"Institutional Equity Research | {args.rating}",
        "sector":        args.sector,
        "prepared_by":   "Valerie (The Quantitative Oracle)",
        "audited_by":    "Christian (The Forensic Auditor)",
        "rating":        args.rating,
        "is_positive":   args.positive,
        "price_target":  args.pt,
        "analysis_price": args.price,
        "en_overview":   read_file("en_overview", paths["en_overview"]),
        "th_overview":   read_file("th_overview", paths["th_overview"]),
        "en_dcf":        read_file("en_dcf",      paths["en_dcf"]),
        "th_dcf":        read_file("th_dcf",      paths["th_dcf"]),
    }

    body = json.dumps(payload).encode("utf-8")

    if args.mode == "update":
        url = f"{BASE_URL}/api/research-report?key={report_key}"
        req = urllib.request.Request(url, data=body, method="PUT")
    else:
        url = f"{BASE_URL}/api/research-report"
        req = urllib.request.Request(url, data=body, method="POST")

    req.add_header("Content-Type", "application/json")

    print(f"  Sending {args.mode.upper()} → {url}")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("success"):
                print(f"  ✓ SUCCESS: {ticker} deployed to DB\n")
            else:
                print(f"  ✗ FAILED: {result}\n")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        print(f"  ✗ HTTP {e.code}: {err}\n")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"  ✗ Connection error: {e.reason}")
        print(f"    Is the server running? python server.py")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deploy equity research report to Genie DB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--ticker",   required=True,  help="Stock ticker e.g. RKLB")
    parser.add_argument("--company",  required=True,  help="Full company name")
    parser.add_argument("--sector",   required=True,  help="Sector classification")
    parser.add_argument("--rating",   required=True,  help="e.g. BUY, SPECULATIVE BUY, AVOID")
    parser.add_argument("--pt",       required=True,  type=float, help="Price target (number)")
    parser.add_argument("--price",    required=True,  type=float, help="Analysis price (number)")
    parser.add_argument("--subtitle", default=None,   help="Report subtitle/tagline")
    parser.add_argument("--key",      default=None,   help="Report key override, default: {TICKER}_2026")
    parser.add_argument("--mode",     choices=["insert", "update"], default="insert")

    sentiment = parser.add_mutually_exclusive_group()
    sentiment.add_argument("--positive", dest="positive", action="store_true",  default=True)
    sentiment.add_argument("--negative", dest="positive", action="store_false")

    args = parser.parse_args()
    deploy(args)
