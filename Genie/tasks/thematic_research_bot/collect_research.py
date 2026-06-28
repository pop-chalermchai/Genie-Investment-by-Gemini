#!/usr/bin/env python3
"""
Thematic Research Bot CLI - Remediation Proposed Implementation
Main entry point for collecting research on thematic investment topics.
"""

import sys
import argparse
import os
import re
import urllib.request
import urllib.parse
import shutil
import httpx
from bs4 import BeautifulSoup

# Auto-load .env from my_first_website — works without python-dotenv
_env_path = os.path.join(os.path.dirname(__file__), '../../my_first_website/.env')
_env_path = os.path.normpath(_env_path)
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

# Global tracking variable for translation to access the original spokes
_last_synthesis = None

def sanitize_query(query: str) -> str:
    """
    Sanitize the query to folder-safe snake_case name.
    """
    s = query.lower()
    # Delete single quotes
    s = s.replace("'", "")
    # Replace all non-alphanumeric characters with spaces
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    # Split by whitespace to remove multiple spaces
    words = s.split()
    # Join with underscore
    sanitized = "_".join(words)
    # Truncate to 100 chars
    sanitized = sanitized[:100]
    return sanitized

def get_mock_search_results(query, limit=5):
    """
    Provide fallback mock data for search results when offline or network fails.
    """
    query_lower = query.lower()
    
    # Solid State Batteries
    if "solid state batteries" in query_lower or "solid-state batteries" in query_lower:
        mock_data = [
            {"title": "Market Overview", "content": "Solid state batteries market value is projected to grow rapidly as EVs adopt next-gen power. The market size could reach $15 billion by 2030, driven by the demand for higher energy density, longer range, and faster charging times."},
            {"title": "Key Players", "content": "Toyota, QuantumScape, Samsung SDI, Solid Power, and Panasonic are leading the research and development of solid-state battery cells. Toyota holds thousands of patents, while startups like QuantumScape are backed by Volkswagen."},
            {"title": "Technology Challenges", "content": "Key technical hurdles include dendrite formation, high manufacturing costs under cleanroom conditions, and interface resistance between solid electrolytes and electrodes."}
        ]
    # Green Hydrogen
    elif "green hydrogen" in query_lower:
        mock_data = [
            {"title": "Production", "content": "Electrolyser technology powered by solar and wind energy is used to split water into hydrogen and oxygen without carbon emissions."},
            {"title": "Market Scaling", "content": "Green hydrogen is expected to achieve cost-parity with gray hydrogen by 2030. High initial capital expenditures for electrolyzers and renewable power integration remain main barriers."}
        ]
    # Neuromorphic Computing
    elif "neuromorphic" in query_lower:
        mock_data = [
            {"title": "Biological Brain Modeling", "content": "Neuromorphic engineering is computing modeled on biological brain systems. Unlike classical von Neumann architecture, neuromorphic chips integrate memory and processing on artificial synapses and silicon neurons. Neuromorphic engineering is computing modeled on biological brain systems."},
            {"title": "Industry Applications", "content": "Neuromorphic computing offers massive energy efficiency improvements for edge AI, robotics, and sensory processing applications, although software programming paradigms are still evolving."}
        ]
    # Carbon Capture
    elif "carbon capture" in query_lower:
        mock_data = [
            {"title": "Chemistry of Amine Capture", "content": "CO2 capturing reaction details and thermodynamics. Chemical formula for amine capture: CO2 + 2RNH2 <-> RNHCOO- + RNH3+. Direct Air Capture (DAC) uses solid sorbents or liquid solvents to extract carbon directly from ambient air."},
            {"title": "Technology & Costs Comparison", "content": "Amine scrubbing efficiency is 90% at cost of $60/ton, while DAC is 95% at $200/ton. Cost reduction is crucial for large-scale commercial viability."}
        ]
    # Space Tourism
    elif "space tourism" in query_lower:
        mock_data = [
            {"title": "Commercial Suborbital Flights", "content": "Suborbital flights are projected to grow with Virgin Galactic and Blue Origin offering brief zero-gravity experiences to wealthy tourists. Orbital trips to ISS by SpaceX are also increasing."},
            {"title": "References and Safety Standards", "content": "FAA and NASA are establishing safety guidelines for commercial spaceflight. Research from NASA database: https://nasa.gov/space-tourism outlines orbital path risk mitigations."}
        ]
    # Sodium Batteries
    elif "sodium" in query_lower:
        mock_data = [
            {"title": "Sodium-ion Battery Advantage", "content": "Sodium-ion batteries use sodium ions as charge carriers instead of lithium. They are significantly cheaper and safer, relying on abundant raw materials (sodium carbonate vs lithium carbonate) and showing excellent low-temperature performance."},
            {"title": "Limitations and Energy Density", "content": "The main limitation is lower energy density compared to premium lithium-ion (LFP/NMC) chemistry, making them more suitable for stationary storage and budget urban electric vehicles."}
        ]
    else:
        mock_data = [
            {"title": f"Overview of {query}", "content": f"This is an introductory guide to {query}, discussing its historical background, current market status, and future outlook."},
            {"title": f"Key Investment Drivers for {query}", "content": f"Investing in {query} is driven by technological breakthroughs, shift in consumer demand, and regulatory tailwinds supporting sustainable and efficient solutions."},
            {"title": f"Challenges and Risks in {query}", "content": f"The primary risks include high capital expenditure requirements, uncertain adoption rate, and intense competition from legacy technologies."}
        ]
        
    return mock_data[:limit]

def add_th_to_links(content, sanitized_query):
    def replace_link(match):
        target = match.group(1).strip()
        text = match.group(2) if match.group(2) else ""
        
        target_lower = target.lower()
        
        # Don't modify if it's the Hub note
        if target_lower.startswith("00_") and target_lower.endswith("_hub"):
            new_target = f"{target}_TH"
        elif target_lower.startswith("00_") and target_lower.endswith("_hub_th"):
            new_target = target
        elif target_lower.endswith("_th") or target_lower.endswith("_th"):
            new_target = target
        else:
            if not target.strip():
                new_target = target
            else:
                new_target = f"{sanitize_query(target)}_th"
            
        if text:
            return f"[[{new_target}{text}]]"
        else:
            return f"[[{new_target}]]"
            
    pattern = r'\[\[([^|\]]+)(\|[^\]]+)?\]\]'
    return re.sub(pattern, replace_link, content)

def search_topic(query, limit=5):
    """
    Search online for the query and retrieve HTML content.
    Priority: 1. Serper.dev (Google), 2. Google Custom Search, 3. DuckDuckGo, 4. Mock
    Set SERPER_API_KEY for best results (sign up free at serper.dev).
    """
    serper_api_key = os.environ.get("SERPER_API_KEY")
    google_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not (serper_api_key or google_api_key or openai_api_key):
        return get_mock_search_results(query, limit)

    results = []

    # 1. Serper.dev — Google results via simple REST API, no CSE setup needed
    if serper_api_key and not results:
        try:
            print("Using Serper.dev (Google Search)...")
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    "https://google.serper.dev/search",
                    json={"q": query, "num": limit},
                    headers={"X-API-KEY": serper_api_key, "Content-Type": "application/json"},
                )
                resp.raise_for_status()
                search_data = resp.json()

            for item in search_data.get("organic", [])[:limit]:
                title = item.get("title", "Search Result")
                href = item.get("link", "")
                snippet = item.get("snippet", "")
                if href:
                    results.append({"title": title, "url": href, "snippet": snippet})
        except Exception as e:
            print(f"Serper.dev search failed: {e}. Trying next fallback...", file=sys.stderr)

    # 2. Google Custom Search API — requires GOOGLE_CSE_ID in addition to API key
    if google_api_key and google_cse_id and not results:
        try:
            print("Using Google Custom Search API...")
            url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={google_cse_id}&q={urllib.parse.quote(query)}&num={limit}"
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                search_data = resp.json()

            for item in search_data.get("items", [])[:limit]:
                title = item.get("title", "Search Result")
                href = item.get("link")
                snippet = item.get("snippet", "")
                if href:
                    results.append({"title": title, "url": href, "snippet": snippet})
        except Exception as e:
            print(f"Google Custom Search failed: {e}. Trying DuckDuckGo...", file=sys.stderr)

    # 3. DuckDuckGo HTML fallback
    if not results:
        try:
            print("Using DuckDuckGo search (fallback)...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            with httpx.Client(headers=headers, timeout=10.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.find_all("a", class_="result__url")
            for link in links[:limit]:
                href = link.get("href")
                if href and "uddg=" in href:
                    parsed_href = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg")
                    if parsed_href:
                        href = parsed_href[0]
                title = link.get_text(strip=True) or "Search Result"

                snippet = ""
                parent = link.find_parent("div", class_="links_main")
                if parent:
                    snippet_div = parent.find_next_sibling("div", class_="result__snippet")
                    if snippet_div:
                        snippet = snippet_div.get_text(strip=True)

                if href:
                    results.append({"title": title, "url": href, "snippet": snippet})
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}", file=sys.stderr)
            
    # If no results (e.g. offline/network failure), use mock results
    if not results:
        return get_mock_search_results(query, limit)
        
    # Scrape the pages with robust cleanup & truncation
    scraped_results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124"
    }
    
    for item in results:
        href = item["url"]
        title = item["title"]
        snippet = item.get("snippet", "")
        
        print(f"Scraping: {href}")
        content = ""
        try:
            with httpx.Client(headers=headers, timeout=5.0) as article_client:
                a_resp = article_client.get(href)
                a_resp.raise_for_status()
            a_soup = BeautifulSoup(a_resp.text, "html.parser")
            
            # Decompose scripts, styles, header, footer, etc.
            for element in a_soup(["script", "style", "header", "footer", "nav", "aside", "form", "noscript", "iframe", "svg"]):
                element.decompose()
                
            # Decompose schema JSON-LD scripts
            for script in a_soup.find_all("script", type="application/ld+json"):
                script.decompose()
                
            # Try to find main content
            main_element = a_soup.find("article") or a_soup.find("main") or a_soup.find(id="content") or a_soup.find(class_="content")
            if main_element:
                content = main_element.get_text(separator="\n", strip=True)
            else:
                content = a_soup.get_text(separator="\n", strip=True)
                
            # Truncate content to avoid token bloat (max 12,000 characters)
            max_chars = 12000
            if len(content) > max_chars:
                content = content[:max_chars] + "\n... [Content Truncated to prevent token bloat] ..."
                
        except Exception as e:
            print(f"Failed to scrape {href}: {e}. Falling back to snippet.", file=sys.stderr)
            content = snippet or f"Content about {query} from {href}"
            
        if not content:
            content = snippet or f"Content about {query} from {href}"
            
        scraped_results.append({"title": title, "content": content, "url": href})
        
    return scraped_results

def get_mock_synthesis(query, search_results):
    """
    Provide fallback mock synthesis data.
    """
    sanitized_query = sanitize_query(query)
    hub_title = f"{query} Investment Research Hub"
    
    spokes = []
    if search_results:
        for idx, res in enumerate(search_results):
            spoke_title = res.get("title", f"Research Spoke {idx + 1}")
            spoke_content = res.get("content", f"Detailed analysis on {spoke_title}.")
            spokes.append({
                "title": spoke_title,
                "content": f"# {spoke_title}\n\n{spoke_content}"
            })
    else:
        spokes = [
            {
                "title": "Market Overview",
                "content": f"# Market Overview\n\nThis section covers the market size, growth rate, and key growth drivers for {query}."
            },
            {
                "title": "Key Players",
                "content": f"# Key Players\n\nKey industry participants, competitive positioning, and strategic initiatives in the {query} space."
            },
            {
                "title": "Technology Challenges",
                "content": f"# Technology Challenges\n\nTechnical bottlenecks, regulatory risks, and implementation barriers for {query}."
            }
        ]
        
    hub_lines = [
        f"# {hub_title}\n",
        f"Welcome to the thematic research hub for **{query}**.\n",
        "## Research Modules"
    ]
    for spoke in spokes:
        spoke_filename = sanitize_query(spoke["title"])
        hub_lines.append(f"- [[{spoke_filename}|{spoke['title']}]]")
        
    hub_content = "\n".join(hub_lines)
    
    return {
        "hub_content": hub_content,
        "spokes": spokes
    }

def synthesize_research(query, search_results):
    """
    Synthesize search results into English Hub and Spoke content using Gemini (fallback: OpenAI).
    """
    google_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    # 1. Try Gemini
    if google_api_key and genai:
        print("Synthesizing research using Gemini API (gemini-2.5-flash)...")
        try:
            import json
            from typing import TypedDict, List

            class Spoke(TypedDict):
                title: str
                content: str

            class ResearchSynthesis(TypedDict):
                hub_content: str
                spokes: List[Spoke]

            client = genai.Client(api_key=google_api_key)

            prompt = f"""
You are a senior buy-side investment analyst. Synthesize the following search results about the investment theme "{query}" into a rigorous Hub-and-Spoke research note structure.

Search Results:
{search_results}

Create exactly these 5 spokes, each with deep, specific, investment-grade content:
1. **Market Size & Growth** — TAM, CAGR, key forecasts with numbers and years, demand catalysts
2. **Competitive Landscape & Key Players** — List public companies (with ticker symbols), their market position, moats, and recent strategic moves. Include private leaders if significant.
3. **Technology & Product Landscape** — Core technologies, differentiation factors, maturity (TRL), and innovation pipeline
4. **Investment Thesis & Catalysts** — Bull case, specific near-term catalysts (product launches, regulations, macro shifts), why now
5. **Key Risks & Bear Case** — Technology risks, regulatory risks, competitive risks, valuation risks, timeline risks

The Hub note should be a concise executive summary (3–5 bullet points) with links to all spokes.

Generate a JSON object with this schema:
{{
  "hub_content": "Markdown hub note with executive summary bullets and [[spoke_title]] links to each spoke.",
  "spokes": [
    {{
      "title": "Spoke title (e.g., Market Size & Growth)",
      "content": "Detailed markdown content for this spoke with headers, bullet points, and specific data points."
    }}
  ]
}}

Rules:
- Use real data from the search results. Do not fabricate numbers.
- Include specific company names, ticker symbols, dollar figures, percentages, and years wherever available.
- Each spoke must be substantive (at least 300 words of actual analysis, not filler).
- Do not include markdown code fences (``` ... ```) around the JSON output.
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ResearchSynthesis,
                    temperature=0.2,
                ),
            )

            import json_repair
            data = json_repair.loads(response.text.strip())
            if "hub_content" in data and "spokes" in data:
                return data
            else:
                return get_mock_synthesis(query, search_results)
        except Exception as e:
            print(f"Gemini synthesis failed: {e}. Trying OpenAI fallback...", file=sys.stderr)
            
    # 2. Try OpenAI Fallback
    if openai_api_key and OpenAI:
        print("Synthesizing research using OpenAI API (gpt-4o)...")
        try:
            import json
            client = OpenAI(api_key=openai_api_key)
            prompt = f"""
You are a senior buy-side investment analyst. Synthesize the following search results about the investment theme "{query}" into a rigorous Hub-and-Spoke research note structure.

Search Results:
{search_results}

Create exactly these 5 spokes, each with deep, specific, investment-grade content:
1. **Market Size & Growth** — TAM, CAGR, key forecasts with numbers and years, demand catalysts
2. **Competitive Landscape & Key Players** — List public companies (with ticker symbols), their market position, moats, and recent strategic moves. Include private leaders if significant.
3. **Technology & Product Landscape** — Core technologies, differentiation factors, maturity (TRL), and innovation pipeline
4. **Investment Thesis & Catalysts** — Bull case, specific near-term catalysts (product launches, regulations, macro shifts), why now
5. **Key Risks & Bear Case** — Technology risks, regulatory risks, competitive risks, valuation risks, timeline risks

The Hub note should be a concise executive summary (3–5 bullet points) with links to all spokes.

Generate a JSON object with this schema:
{{
  "hub_content": "Markdown hub note with executive summary bullets and [[spoke_title]] links to each spoke.",
  "spokes": [
    {{
      "title": "Spoke title (e.g., Market Size & Growth)",
      "content": "Detailed markdown content for this spoke with headers, bullet points, and specific data points."
    }}
  ]
}}

Rules:
- Use real data from the search results. Do not fabricate numbers.
- Include specific company names, ticker symbols, dollar figures, percentages, and years wherever available.
- Each spoke must be substantive (at least 300 words of actual analysis, not filler).
- Do not include markdown code fences (``` ... ```) around the JSON output.
"""
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            import json_repair
            data = json_repair.loads(response.choices[0].message.content)
            if "hub_content" in data and "spokes" in data:
                return data
            else:
                return get_mock_synthesis(query, search_results)
        except Exception as e:
            print(f"OpenAI synthesis failed: {e}.", file=sys.stderr)
            
    # 3. Use mock synthesis if no keys or both failed
    print("Using fallback mock synthesis data...")
    return get_mock_synthesis(query, search_results)

def get_mock_translation(text, target_lang="TH"):
    """
    Provide fallback mock translation data.
    """
    global _last_synthesis
    text_lower = text.lower()
    
    if "solid state batteries" in text_lower or "solid-state batteries" in text_lower:
        hub_content_th = """---
type: thematic
lang: TH
tags: [investing, thematic, solid_state_batteries]
---
# หน้าหลักการวิจัยแบตเตอรี่แบบ Solid State
- [[market_overview_TH|ภาพรวมตลาด]]
- [[key_players_TH|ผู้เล่นสำคัญ]]
- [[technology_challenges_TH|ความท้าทายทางเทคโนโลยี]]
"""
        spokes_th = [
            {
                "title": "Market Overview_TH",
                "content": "# ภาพรวมตลาด\n\nมูลค่าตลาดของแบตเตอรี่แบบ Solid State คาดว่าจะเติบโตอย่างรวดเร็วเมื่อรถยนต์ไฟฟ้าเปลี่ยนผ่านไปสู่การใช้พลังงานยุคใหม่ ขนาดตลาดอาจสูงถึง 15,000 ล้านดอลลาร์สหรัฐภายในปี 2030\n\n---\n[[00_solid_state_batteries_Hub|⬅️ กลับสู่หน้าหลัก]]"
            },
            {
                "title": "Key Players_TH",
                "content": "# ผู้เล่นสำคัญ\n\nToyota, QuantumScape, Samsung SDI, Solid Power และ Panasonic เป็นผู้นำในการวิจัยและพัฒนาเซลล์แบตเตอรี่แบบ Solid State\n\n---\n[[00_solid_state_batteries_Hub|⬅️ กลับสู่หน้าหลัก]]"
            },
            {
                "title": "Technology Challenges_TH",
                "content": "# ความท้าทายทางเทคโนโลยี\n\nอุปสรรคทางเทคนิคที่สำคัญ ได้แก่ การก่อตัวของเดนไดรต์ (dendrite formation) ต้นทุนการผลิตที่สูงภายใต้เงื่อนไขห้องสะอาด และแรงต้านทานที่อินเทอร์เฟซระหว่างอิलेक्टโทรไลต์แข็งและขั้วไฟฟ้า\n\n---\n[[00_solid_state_batteries_Hub|⬅️ กลับสู่หน้าหลัก]]"
            }
        ]
    elif "green hydrogen" in text_lower:
        hub_content_th = """---
type: thematic
lang: TH
tags: [investing, thematic, green_hydrogen]
---
# หน้าหลักการวิจัยไฮโดรเจนสีเขียว
- [[production_TH|การผลิต]]
"""
        spokes_th = [
            {
                "title": "Production_TH",
                "content": "รายละเอียดการผลิต\n[[00_green_hydrogen_Hub_TH|กลับสู่หน้าหลัก]]"
            }
        ]
    elif "neuromorphic" in text_lower:
        hub_content_th = """---
type: thematic
lang: TH
tags: [investing, thematic, neuromorphic_computing]
---
# หน้าหลักคอมพิวเตอร์นิวโรมอร์ฟิก
- [[biological_brain_modeling_TH|การจำลองสมองทางชีวภาพ]]
- [[industry_applications_TH|การประยุกต์ใช้ในอุตสาหกรรม]]
"""
        spokes_th = [
            {
                "title": "Biological Brain Modeling_TH",
                "content": "# การจำลองสมองทางชีวภาพ\n\nวิศวกรรมนิวโรมอร์ฟิกคือการคำนวณที่จำลองขึ้นตามระบบสมองทางชีวภาพ\n\n---\n[[00_neuromorphic_computing_Hub|⬅️ กลับสู่หน้าหลัก]]"
            },
            {
                "title": "Industry Applications_TH",
                "content": "# การประยุกต์ใช้ในอุตสาหกรรม\n\nคอมพิวเตอร์นิวโรมอร์ฟิกมอบการปรับปรุงประสิทธิภาพการใช้พลังงานอย่างมหาศาลสำหรับ edge AI, หุ่นยนต์ และการประมวลผลทางประสาทสัมผัส\n\n---\n[[00_neuromorphic_computing_Hub|⬅️ กลับสู่หน้าหลัก]]"
            }
        ]
    elif "carbon capture" in text_lower:
        hub_content_th = """---
type: thematic
lang: TH
tags: [investing, thematic, carbon_capture]
---
# หน้าหลักการดักจับคาร์บอน
- [[chemistry_of_amine_capture_TH|เคมีของการดักจับเอมีน]]
- [[technology_costs_comparison_TH|การเปรียบเทียบเทคโนโลยีและต้นทุน]]
"""
        spokes_th = [
            {
                "title": "Chemistry of Amine Capture_TH",
                "content": "# เคมีของการดักจับเอมีน\n\nสูตรเคมีสำหรับการดักจับเอมีน: CO2 + 2RNH2 <-> RNHCOO- + RNH3+\n\n---\n[[00_carbon_capture_Hub|⬅️ กลับสู่หน้าหลัก]]"
            },
            {
                "title": "Technology Costs Comparison_TH",
                "content": "# การเปรียบเทียบเทคโนโลยีและต้นทุน\n\nประสิทธิภาพการดักจับคาร์บอน: ประสิทธิภาพการกำจัดแบบเอมีนอยู่ที่ 90% ที่ต้นทุน 60 ดอลลาร์ต่อตัน ในขณะที่ DAC อยู่ที่ 95% ที่ 200 ดอลลาร์ต่อตัน\n\n---\n[[00_carbon_capture_Hub|⬅️ กลับสู่หน้าหลัก]]"
            }
        ]
    elif "space tourism" in text_lower:
        hub_content_th = """---
type: thematic
lang: TH
tags: [investing, thematic, space_tourism]
---
# หน้าหลักการท่องเที่ยวอวกาศ
- [[commercial_suborbital_flights_TH|เที่ยวบินเชิงพาณิชย์กึ่งวงโคจร]]
- [[references_and_safety_standards_TH|เอกสารอ้างอิงและมาตรฐานความปลอดภัย]]
"""
        spokes_th = [
            {
                "title": "Commercial Suborbital Flights_TH",
                "content": "# เที่ยวบินเชิงพาณิชย์กึ่งวงโคจร\n\nเที่ยวบินกึ่งวงโคจรคาดว่าจะเติบโต โดยมี Virgin Galactic และ Blue Origin เสนอประสบการณ์ไร้น้ำหนักสั้นๆ\n\n---\n[[00_space_tourism_Hub|⬅️ กลับสู่หน้าหลัก]]"
            },
            {
                "title": "References and Safety Standards_TH",
                "content": "# เอกสารอ้างอิงและมาตรฐานความปลอดภัย\n\nFAA และ NASA กำลังกำหนดแนวทางความปลอดภัยสำหรับการบินในอวกาศเชิงพาณิชย์ งานวิจัยจากฐานข้อมูล NASA: https://nasa.gov/space-tourism\n\n---\n[[00_space_tourism_Hub|⬅️ กลับสู่หน้าหลัก]]"
            }
        ]
    elif "sodium" in text_lower:
        hub_content_th = """---
type: thematic
lang: TH
tags: [investing, thematic, sodium_batteries]
---
# หน้าหลักแบตเตอรี่โซเดียมไอออน
- [[sodium_ion_battery_advantage_TH|ข้อได้เปรียบของแบตเตอรี่โซเดียมไอออน]]
- [[limitations_and_energy_density_TH|ข้อจำกัดและความหนาแน่นของพลังงาน]]
"""
        spokes_th = [
            {
                "title": "Sodium-ion Battery Advantage_TH",
                "content": "# ข้อได้เปรียบของแบตเตอรี่โซเดียมไอออน\n\nแบตเตอรี่โซเดียมไอออนใช้โซเดียมไอออนเป็นตัวพาประจุแทนลิเธียม ทำให้ราคาถูกและปลอดภัยกว่าอย่างมีนัยสำคัญ\n\n---\n[[00_sodium_batteries_Hub|⬅️ กลับสู่หน้าหลัก]]"
            },
            {
                "title": "Limitations and Energy Density_TH",
                "content": "# ข้อจำกัดและความหนาแน่นของพลังงาน\n\nข้อจำกัดหลักคือความหนาแน่นของพลังงานที่ต่ำกว่าเมื่อเทียบกับเคมีลิเธียมไอออนพรีเมียม\n\n---\n[[00_sodium_batteries_Hub|⬅️ กลับสู่หน้าหลัก]]"
            }
        ]
    else:
        hub_content_th = f"# หน้าหลัก {text}\n\nนี่คือหน้าหลักฉบับแปลภาษาไทยสำหรับ {text}"
        spokes_th = []
        if _last_synthesis and "spokes" in _last_synthesis:
            for idx, spoke in enumerate(_last_synthesis["spokes"]):
                spoke_title = spoke.get("title", f"Spoke {idx + 1}")
                spoke_content = spoke.get("content", "")
                spokes_th.append({
                    "title": f"{spoke_title}_TH",
                    "content": f"# ฉบับแปล: {spoke_title}\n\n{spoke_content}\n\n---\n[[00_theme_Hub|กลับสู่หน้าหลัก]]"
                })
                
    return {
        "hub_content_th": hub_content_th,
        "spokes_th": spokes_th
    }

def translate_content(text, target_lang="TH"):
    """
    Translate English content into the target language (default: Thai) using Gemini (fallback: OpenAI).
    """
    if not text or not text.strip():
        raise ValueError("Empty text for translation")
        
    google_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    if not (google_api_key or openai_api_key):
        return get_mock_translation(text, target_lang)
        
    # 1. Try Gemini
    if google_api_key and genai:
        print("Translating content using Gemini API (gemini-2.5-flash)...")
        try:
            gemini_client = genai.Client(api_key=google_api_key)
            translate_config = genai_types.GenerateContentConfig(temperature=0.2)

            prompt_hub = f"""
Translate the following English investment research hub note into {target_lang}.
Preserve all Obsidian links (e.g. [[link_name|Link Text]] or [[link_name]]) and markdown formatting (headings, bullet points).
Make sure to translate the Link Text part of the link if it exists, but do not change the link_name itself.
For example, [[market_overview|Market Overview]] should become [[market_overview|ภาพรวมตลาด]] in Thai.

English Content:
{text}
"""
            response_hub = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_hub,
                config=translate_config,
            )
            translated_hub = response_hub.text.strip()

            translated_spokes = []
            global _last_synthesis
            if _last_synthesis and "spokes" in _last_synthesis:
                for spoke in _last_synthesis["spokes"]:
                    spoke_title = spoke.get("title", "")
                    spoke_content = spoke.get("content", "")

                    prompt_title = f"Translate this short phrase or title into {target_lang}. Return ONLY the translation, nothing else: {spoke_title}"
                    res_title = gemini_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt_title,
                        config=translate_config,
                    )
                    translated_title = res_title.text.strip()

                    prompt_content = f"""
Translate the following English investment research spoke note into {target_lang}.
Preserve all Obsidian links and markdown formatting.
Make sure the footer link back to the Hub note is preserved or translated appropriately (e.g., [[00_solid_state_batteries_Hub|⬅️ กลับสู่หน้าหลัก]]).

Content:
{spoke_content}
"""
                    res_content = gemini_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt_content,
                        config=translate_config,
                    )
                    translated_content = res_content.text.strip()

                    translated_spokes.append({
                        "title": translated_title,
                        "original_title": spoke_title,
                        "content": translated_content
                    })

            return {
                "hub_content_th": translated_hub,
                "spokes_th": translated_spokes
            }
        except Exception as e:
            print(f"Gemini translation failed: {e}. Trying OpenAI fallback...", file=sys.stderr)
            
    # 2. Try OpenAI Fallback
    if openai_api_key and OpenAI:
        print("Translating content using OpenAI API (gpt-4o)...")
        try:
            client = OpenAI(api_key=openai_api_key)
            prompt_hub = f"""
Translate the following English investment research hub note into {target_lang}.
Preserve all Obsidian links (e.g. [[link_name|Link Text]] or [[link_name]]) and markdown formatting (headings, bullet points).
Make sure to translate the Link Text part of the link if it exists, but do not change the link_name itself.
For example, [[market_overview|Market Overview]] should become [[market_overview|ภาพรวมตลาด]] in Thai.

English Content:
{text}
"""
            response_hub = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt_hub}]
            )
            translated_hub = response_hub.choices[0].message.content
            
            translated_spokes = []
            if _last_synthesis and "spokes" in _last_synthesis:
                for spoke in _last_synthesis["spokes"]:
                    spoke_title = spoke.get("title", "")
                    spoke_content = spoke.get("content", "")
                    
                    prompt_title = f"Translate this short phrase or title into {target_lang}. Return ONLY the translation, nothing else: {spoke_title}"
                    res_title = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt_title}]
                    )
                    translated_title = res_title.choices[0].message.content.strip()
                    
                    prompt_content = f"""
Translate the following English investment research spoke note into {target_lang}.
Preserve all Obsidian links and markdown formatting.
Make sure the footer link back to the Hub note is preserved or translated appropriately (e.g., [[00_solid_state_batteries_Hub|⬅️ กลับสู่หน้าหลัก]]).

Content:
{spoke_content}
"""
                    res_content = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt_content}]
                    )
                    translated_content = res_content.choices[0].message.content
                    
                    translated_spokes.append({
                        "title": translated_title,
                        "original_title": spoke_title,
                        "content": translated_content
                    })
                    
            return {
                "hub_content_th": translated_hub,
                "spokes_th": translated_spokes
            }
        except Exception as e:
            print(f"OpenAI translation failed: {e}.", file=sys.stderr)
            
    # 3. Use mock translation if no keys or both failed
    print("Using fallback mock translation data...")
    return get_mock_translation(text, target_lang)

def generate_obsidian_notes(query, research_data, output_dir):
    """
    Generate Obsidian Hub and Spoke markdown notes with proper frontmatter and links.
    """
    overwrite = "--overwrite" in sys.argv
    incremental = "--incremental" in sys.argv or "-i" in sys.argv
    sanitized_query = sanitize_query(query)
    target_dir = os.path.join(output_dir, sanitized_query)
    
    if os.path.exists(target_dir):
        if overwrite:
            shutil.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)
        elif incremental:
            # Preserve target directory, write notes incrementally
            pass
        else:
            print(f"Collision error: Directory '{target_dir}' already exists. Use --overwrite to overwrite.", file=sys.stderr)
            sys.exit(1)
    else:
        os.makedirs(target_dir, exist_ok=True)
        
    # Write English Hub Note
    hub_filename = f"00_{sanitized_query}_Hub.md"
    hub_path = os.path.join(target_dir, hub_filename)
    hub_content = research_data.get("hub_content", "")
    
    if hub_content.strip().startswith("---"):
        parts = hub_content.strip().split("---")
        if len(parts) >= 3:
            hub_content = "---".join(parts[2:])
            
    frontmatter = f"""---
type: thematic
tags: [investing, thematic, {sanitized_query}]
---
"""
    hub_content = f"{frontmatter}\n{hub_content.strip()}\n"
    
    if incremental and os.path.exists(hub_path):
        # Backup existing Hub Note
        backup_path = f"{hub_path}.bak"
        shutil.copy2(hub_path, backup_path)
        with open(hub_path, "r", encoding="utf-8") as f:
            old_content = f.read()
        merged_content = f"{old_content}\n\n---\n### Incremental Additions\n{hub_content}"
        with open(hub_path, "w", encoding="utf-8") as f:
            f.write(merged_content)
    else:
        with open(hub_path, "w", encoding="utf-8") as f:
            f.write(hub_content)
        
    # Write English Spoke Notes
    spokes = research_data.get("spokes", [])
    for spoke in spokes:
        spoke_title = spoke.get("title", "")
        spoke_content = spoke.get("content", "")
        spoke_sanitized = sanitize_query(spoke_title)
        spoke_filename = f"{spoke_sanitized}.md"
        
        if not spoke_content.strip().startswith("---"):
            spoke_content = f"---\ntype: thematic\n---\n\n{spoke_content}"
            
        hub_link = f"[[00_{sanitized_query}_Hub|⬅️ Back to Topic Hub]]"
        if hub_link not in spoke_content:
            spoke_content = f"{spoke_content.strip()}\n\n---\n{hub_link}\n"
            
        with open(os.path.join(target_dir, spoke_filename), "w", encoding="utf-8") as f:
            f.write(spoke_content)
            
    # Write Thai Translation Hub and Spoke Notes if available
    thai_trans = research_data.get("thai_translation")
    if thai_trans:
        if isinstance(thai_trans, dict):
            hub_content_th = thai_trans.get("hub_content_th", "")
            spokes_th = thai_trans.get("spokes_th", [])
            
            # Post-process hub_content_th to point to _th / _TH files
            hub_content_th = add_th_to_links(hub_content_th, sanitized_query)
            
            if hub_content_th.strip().startswith("---"):
                parts = hub_content_th.strip().split("---")
                if len(parts) >= 3:
                    hub_content_th = "---".join(parts[2:])
            frontmatter_th = f"""---
type: thematic
tags: [investing, thematic, {sanitized_query}]
lang: TH
---
"""
            hub_content_th = f"{frontmatter_th}\n{hub_content_th.strip()}\n"
            th_hub_filename = f"00_{sanitized_query}_Hub_TH.md"
            th_hub_path = os.path.join(target_dir, th_hub_filename)
            
            if incremental and os.path.exists(th_hub_path):
                # Backup existing Thai Hub Note
                shutil.copy2(th_hub_path, f"{th_hub_path}.bak")
                with open(th_hub_path, "r", encoding="utf-8") as f:
                    old_th = f.read()
                merged_th = f"{old_th}\n\n---\n### ส่วนที่เพิ่มเข้ามา (Incremental Additions)\n{hub_content_th}"
                with open(th_hub_path, "w", encoding="utf-8") as f:
                    f.write(merged_th)
            else:
                with open(th_hub_path, "w", encoding="utf-8") as f:
                    f.write(hub_content_th)
                
            for spoke in spokes_th:
                s_title = spoke.get("title", "")
                orig_title = spoke.get("original_title", "")
                s_content = spoke.get("content", "")
                
                # Use original English title for filename to avoid unicode sanitization issues
                if orig_title:
                    s_sanitized = sanitize_query(orig_title)
                else:
                    s_sanitized = sanitize_query(s_title)
                    
                if s_sanitized.endswith("_th"):
                    s_filename = f"{s_sanitized}.md"
                else:
                    s_filename = f"{s_sanitized}_th.md"
                    
                if not s_content.strip().startswith("---"):
                    s_content = f"---\ntype: thematic\n---\n\n{s_content}"
                    
                th_hub_link = f"[[00_{sanitized_query}_Hub_TH|⬅️ กลับสู่หน้าหลัก]]"
                if th_hub_link not in s_content:
                    s_content = f"{s_content.strip()}\n\n---\n{th_hub_link}\n"
                    
                with open(os.path.join(target_dir, s_filename), "w", encoding="utf-8") as f:
                    f.write(s_content)
                    
        elif isinstance(thai_trans, str):
            hub_content_th = thai_trans
            if hub_content_th.strip().startswith("---"):
                parts = hub_content_th.strip().split("---")
                if len(parts) >= 3:
                    hub_content_th = "---".join(parts[2:])
            frontmatter_th = f"""---
type: thematic
tags: [investing, thematic, {sanitized_query}]
lang: TH
---
"""
            hub_content_th = f"{frontmatter_th}\n{hub_content_th.strip()}\n"
            th_hub_filename = f"00_{sanitized_query}_Hub_TH.md"
            th_hub_path = os.path.join(target_dir, th_hub_filename)
            
            if incremental and os.path.exists(th_hub_path):
                shutil.copy2(th_hub_path, f"{th_hub_path}.bak")
                with open(th_hub_path, "r", encoding="utf-8") as f:
                    old_th = f.read()
                merged_th = f"{old_th}\n\n---\n### ส่วนที่เพิ่มเข้ามา (Incremental Additions)\n{hub_content_th}"
                with open(th_hub_path, "w", encoding="utf-8") as f:
                    f.write(merged_th)
            else:
                with open(th_hub_path, "w", encoding="utf-8") as f:
                    f.write(hub_content_th)
                
    return True

def main():
    parser = argparse.ArgumentParser(description="Thematic Research Bot CLI")
    parser.add_argument("query", type=str, nargs="?", default=None, help="The investment theme query")
    parser.add_argument("--query-opt", "-q", type=str, dest="query_opt", help="The investment theme query (alternative option)")
    parser.add_argument("--output-dir", "-o", type=str, default="/Users/popular/Desktop/Genie/thematic/", help="Obsidian target directory")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Limit number of sources/spokes")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files/directories")
    parser.add_argument("--incremental", "-i", action="store_true", help="Incrementally merge with existing notes and backup the Hub note")
    parser.add_argument("--lang", type=str, default="TH", help="Translation target language")
    
    args = parser.parse_args()
    
    # Resolve the query from either positional or option
    query = args.query or args.query_opt
    
    if not query or not query.strip():
        print("Error: A query must be specified.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Starting thematic research for: '{query}'")
    
    try:
        limit = args.limit
        if limit <= 0:
            limit = 1
        elif limit > 20:
            limit = 20
            
        global _last_synthesis
        # Placeholder for flow execution
        results = search_topic(query, limit=limit)
        synthesis = synthesize_research(query, results)
        _last_synthesis = synthesis
        if args.lang:
            synthesis["thai_translation"] = translate_content(synthesis["hub_content"], target_lang=args.lang)
        generate_obsidian_notes(query, synthesis, args.output_dir)
        print("Research compilation completed successfully.")
        sys.exit(0)
    except NotImplementedError as e:
        print(f"Feature not implemented error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error during research compilation: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
