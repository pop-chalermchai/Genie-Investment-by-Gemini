import urllib.request
import json

url = "https://genie-investment-by-gemini.vercel.app/api/init-data"
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        reports = data.get("reports", {})
        print("Total reports in production:", len(reports))
        print("-" * 80)
        for key in ['iren', 'nbis', 'mu', 'aapl']:
            r = reports.get(key)
            if not r:
                print(f"Key: {key} NOT found in production reports!")
                continue
            print(f"Key: {key}")
            print(f"  Ticker: {r.get('ticker')}")
            print(f"  Company: {r.get('companyName')}")
            print(f"  Price Target: {r.get('priceTarget')}")
            print(f"  Analysis Price: {r.get('analysisPrice')}")
            print(f"  Rating: {r.get('rating')}")
            print(f"  Sector: {r.get('sector')}")
            print(f"  EN Overview length: {len(r.get('en_overview') or '')} chars")
            print(f"  TH Overview length: {len(r.get('th_overview') or '')} chars")
            print(f"  EN DCF length: {len(r.get('en_dcf') or '')} chars")
            print(f"  TH DCF length: {len(r.get('th_dcf') or '')} chars")
            print("-" * 80)
except Exception as e:
    print("Error:", e)
