import os
import re

genie_dir = "/Users/popular/Desktop/Genie"

ticker_sectors = {
    # Semiconductors
    "MU": ("Semiconductors", "Semiconductors Sector MOC", "sectors/Semiconductors"),
    "NVDA": ("Semiconductors", "Semiconductors Sector MOC", "sectors/Semiconductors"),
    "LITE": ("Semiconductors", "Semiconductors Sector MOC", "sectors/Semiconductors"),
    "Hynix": ("Semiconductors", "Semiconductors Sector MOC", "sectors/Semiconductors"),
    "AMKR": ("Semiconductors", "Semiconductors Sector MOC", "sectors/Semiconductors"),
    # Technology
    "AAPL": ("Technology", "Technology Sector MOC", "sectors/Technology"),
    "AAOI": ("Technology", "Technology Sector MOC", "sectors/Technology"),
    "AMSC": ("Technology", "Technology Sector MOC", "sectors/Technology"),
    "JBL": ("Technology", "Technology Sector MOC", "sectors/Technology"),
    "NBIS": ("Technology", "Technology Sector MOC", "sectors/Technology"),
    # Energy
    "EOSE": ("Energy", "Energy Sector MOC", "sectors/Energy"),
    "FPS": ("Energy", "Energy Sector MOC", "sectors/Energy"),
    "OKLO": ("Energy", "Energy Sector MOC", "sectors/Energy"),
    # Digital Assets
    "BMNR": ("Digital Assets & Infrastructure", "Digital Assets & Infrastructure Sector MOC", "sectors/Digital_Assets"),
    "IREN": ("Digital Assets & Infrastructure", "Digital Assets & Infrastructure Sector MOC", "sectors/Digital_Assets"),
    "CIFR": ("Digital Assets & Infrastructure", "Digital Assets & Infrastructure Sector MOC", "sectors/Digital_Assets"),
    # Aerospace
    "FLY": ("Aerospace", "Aerospace Sector MOC", "sectors/Aerospace"),
    "RKLB": ("Aerospace", "Aerospace Sector MOC", "sectors/Aerospace"),
}

def extract_company_names():
    moc_path = os.path.join(genie_dir, "research/MOC_Equities.md")
    with open(moc_path, 'r', encoding='utf-8') as f:
        moc_content = f.read()

    company_names = {}
    fallback = {
        "MU": "Micron Technology",
        "NVDA": "NVIDIA Corporation",
        "LITE": "Lumentum Holdings",
        "Hynix": "SK Hynix Inc.",
        "AMKR": "Amkor Technology",
        "AAPL": "Apple Inc.",
        "AAOI": "Applied Optoelectronics",
        "AMSC": "American Superconductor Corp.",
        "JBL": "Jabil Inc.",
        "NBIS": "Nebius Group N.V.",
        "EOSE": "Eos Energy Enterprises",
        "FPS": "Forgent Power Solutions",
        "OKLO": "Oklo Inc.",
        "BMNR": "BitMine Immersion Technologies",
        "IREN": "IREN Limited",
        "CIFR": "Cipher Mining",
        "FLY": "Firefly Aerospace",
        "RKLB": "Rocket Lab USA"
    }

    for ticker in ticker_sectors:
        # Match pattern: [[TICKER/01_Valerie_TICKER_Overview|TICKER (Company Name)]]
        pattern = rf'\[\[{ticker}/[^|]*\|{ticker}\s*\((.*?)\)\]\]'
        match = re.search(pattern, moc_content)
        if match:
            company_names[ticker] = match.group(1).strip()
        else:
            company_names[ticker] = fallback[ticker]
    return company_names

def classify_file(filename, ticker):
    lower_name = filename.lower()
    if "overview_audited" in lower_name:
        return "🇺🇸 English Overview (Audited)"
    elif "overview_th" in lower_name:
        return "🇹🇭 Thai Overview"
    elif "overview" in lower_name:
        return "🇺🇸 English Overview (Draft)"
    elif "reversedcf_audited" in lower_name or "dcf_audited" in lower_name:
        return "🇺🇸 English Reverse DCF (Audited)"
    elif "reversedcf_th" in lower_name or "dcf_th" in lower_name:
        return "🇹🇭 Thai Reverse DCF"
    elif "reversedcf" in lower_name or "dcf" in lower_name:
        return "🇺🇸 English Reverse DCF (Draft)"
    elif "corrections" in lower_name:
        return "Christian's Audit Corrections"
    elif "audit" in lower_name:
        return "Audit Notes"
    else:
        name_no_ext = os.path.splitext(filename)[0]
        # Clean prefix numbers like 01_, 02_
        name_clean = re.sub(r'^\d+_', '', name_no_ext)
        # Clean ticker suffix
        name_clean = re.sub(rf'_{ticker}', '', name_clean, flags=re.IGNORECASE)
        # Convert underscores to space and title case
        name_clean = name_clean.replace('_', ' ').strip()
        return name_clean

def create_ticker_hub(ticker, company_name, files, sector_info):
    sector_name, sector_label, sector_note = sector_info
    
    categories = {
        "Valuation & Overview Reports": [],
        "Reverse DCF Models": [],
        "Audit & Research Notes": [],
        "Other Files & Assets": []
    }
    
    for filename in sorted(files):
        if filename.endswith(".md") and not filename.startswith("00_"):
            name_no_ext = os.path.splitext(filename)[0]
            label = classify_file(filename, ticker)
            link = f"[[{name_no_ext}|{label}]]"
            
            if "Overview" in label:
                categories["Valuation & Overview Reports"].append(link)
            elif "Reverse DCF" in label:
                categories["Reverse DCF Models"].append(link)
            elif "Audit" in label or "Corrections" in label or "Thesis" in label:
                categories["Audit & Research Notes"].append(link)
            else:
                categories["Other Files & Assets"].append(link)
                
    content = f"# 🏢 Stock Hub: {company_name} ({ticker})\n\n"
    
    for cat_name, links in categories.items():
        if links:
            content += f"## {cat_name}\n"
            for link in links:
                content += f"- {link}\n"
            content += "\n"
            
    content += "---\n"
    content += f"**Links:** [[{sector_note}|{sector_label}]] | [[research/MOC_Equities|Equities Dashboard]] | [[000_Index|🏛️ Main Index]]\n"
    
    hub_dir = os.path.join(genie_dir, f"research/{ticker}")
    os.makedirs(hub_dir, exist_ok=True)
    hub_path = os.path.join(hub_dir, f"00_{ticker}_Hub.md")
    with open(hub_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created Hub for {ticker} at {hub_path}")

def update_sub_document_footers(ticker, files):
    for filename in files:
        if filename.endswith(".md") and not filename.startswith("00_"):
            filepath = os.path.join(genie_dir, f"research/{ticker}/{filename}")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Matches any line containing 'Links:' and references either Equities Dashboard or 000_Index
            pattern = r'^.*Links:.*(?:Equities Dashboard|000_Index).*$'
            new_footer = f"**Links:** [[00_{ticker}_Hub|⬅️ Back to {ticker} Stock Hub]]"
            
            modified_content, count = re.subn(pattern, new_footer, content, flags=re.MULTILINE)
            
            if count > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                print(f"  Updated links footer in {filename}")
            else:
                # If links footer not found, check if hub link is missing, and if so append it
                if f"00_{ticker}_Hub" not in content:
                    modified_content = content.rstrip() + f"\n\n---\n**Links:** [[00_{ticker}_Hub|⬅️ Back to {ticker} Stock Hub]]\n"
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    print(f"  Appended footer to {filename}")

def update_sector_files():
    sectors_dir = os.path.join(genie_dir, "sectors")
    for sec_file in os.listdir(sectors_dir):
        if sec_file.endswith(".md"):
            filepath = os.path.join(sectors_dir, sec_file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            modified = False
            for ticker in ticker_sectors:
                # Matches [[research/TICKER/any_text|
                pattern = rf'\[\[research/{ticker}/[^|]*\|'
                replacement = f'[[research/{ticker}/00_{ticker}_Hub|'
                content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    modified = True
                    
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated sector file: {sec_file}")

def rewrite_moc_equities(company_names):
    content = """# 📊 Equities Research Dashboard (MOC)

This Map of Content (MOC) aggregates all stock analyses in the Genie workspace, organized by Industry Sector.

---

## 💻 Semiconductors
"""
    # Semiconductors
    for t in ["MU", "NVDA", "LITE", "Hynix", "AMKR"]:
        content += f"- **[[{t}/00_{t}_Hub|{t} ({company_names[t]})]]**\n"
        
    content += """
---

## 🌐 Technology
"""
    # Technology
    for t in ["AAPL", "AAOI", "AMSC", "JBL", "NBIS"]:
        content += f"- **[[{t}/00_{t}_Hub|{t} ({company_names[t]})]]**\n"
        
    content += """
---

## ⚡ Energy
"""
    # Energy
    for t in ["EOSE", "FPS", "OKLO"]:
        content += f"- **[[{t}/00_{t}_Hub|{t} ({company_names[t]})]]**\n"
        
    content += """
---

## 🪙 Digital Assets & Infrastructure
"""
    # Digital Assets
    for t in ["BMNR", "IREN", "CIFR"]:
        content += f"- **[[{t}/00_{t}_Hub|{t} ({company_names[t]})]]**\n"
        
    content += """
---

## 🚀 Aerospace
"""
    # Aerospace
    for t in ["FLY", "RKLB"]:
        content += f"- **[[{t}/00_{t}_Hub|{t} ({company_names[t]})]]**\n"
        
    moc_path = os.path.join(genie_dir, "research/MOC_Equities.md")
    with open(moc_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Rewrote MOC_Equities.md successfully.")

def main():
    print("Extracting company names...")
    company_names = extract_company_names()
    
    print("\nProcessing tickers...")
    for ticker, sector_info in ticker_sectors.items():
        ticker_dir = os.path.join(genie_dir, f"research/{ticker}")
        if os.path.exists(ticker_dir):
            files = os.listdir(ticker_dir)
            # Create Stock Hub Note
            create_ticker_hub(ticker, company_names[ticker], files, sector_info)
            # Update footer links inside sub-documents
            update_sub_document_footers(ticker, files)
        else:
            print(f"Warning: Directory for {ticker} not found!")

    print("\nUpdating sector files...")
    update_sector_files()
    
    print("\nUpdating MOC_Equities.md...")
    rewrite_moc_equities(company_names)
    
    print("\nAll done!")

if __name__ == "__main__":
    main()
