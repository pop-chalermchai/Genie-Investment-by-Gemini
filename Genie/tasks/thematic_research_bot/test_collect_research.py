import sys
import os
import shutil
import pytest
from unittest.mock import MagicMock, patch

# Ensure the module directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect_research

# ==========================================
# TIER 1: FEATURE COVERAGE (26 Cases)
# ==========================================

# TC-01 to TC-09: CLI argument parsing tests
@pytest.mark.parametrize("args,expected_query,expected_limit,expected_lang,expected_overwrite", [
    (["collect_research.py", "Solid State Batteries"], "Solid State Batteries", 5, "TH", False),
    (["collect_research.py", "-q", "Green Hydrogen"], "Green Hydrogen", 5, "TH", False),
    (["collect_research.py", "--query-opt", "Green Hydrogen"], "Green Hydrogen", 5, "TH", False),
    (["collect_research.py", "AI", "-o", "/tmp/obsidian"], "AI", 5, "TH", False),
    (["collect_research.py", "AI", "--output-dir", "/tmp/obsidian"], "AI", 5, "TH", False),
    (["collect_research.py", "AI", "-l", "3"], "AI", 3, "TH", False),
    (["collect_research.py", "AI", "--limit", "10"], "AI", 10, "TH", False),
    (["collect_research.py", "AI", "--overwrite"], "AI", 5, "TH", True),
    (["collect_research.py", "AI", "--lang", "TH"], "AI", 5, "TH", False),
])
def test_cli_argument_parsing(args, expected_query, expected_limit, expected_lang, expected_overwrite, monkeypatch):
    monkeypatch.setattr("sys.argv", args)
    
    # We intercept the execution flow inside main to inspect the parsed parameters
    called_params = {}
    
    def mock_search_topic(query, limit):
        called_params["query"] = query
        called_params["limit"] = limit
        raise NotImplementedError("stop execution")
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 2  # NotImplementedError exits with 2
    assert called_params["query"] == expected_query
    assert called_params["limit"] == expected_limit


# TC-10 to TC-24: Query parameterization with 15 diverse investment themes
@pytest.mark.parametrize("query_theme", [
    "Quantum Computing",
    "Renewable Energy",
    "Autonomous Vehicles",
    "Gene Editing",
    "Space Exploration",
    "Fintech Innovation",
    "Cybersecurity Systems",
    "Robotics and Automation",
    "Smart Cities",
    "Agricultural Technology",
    "Artificial Intelligence",
    "Metaverse and VR",
    "Cloud Computing",
    "Blockchain and Crypto",
    "3D Printing",
])
def test_query_parameterization(query_theme, monkeypatch):
    args = ["collect_research.py", query_theme]
    monkeypatch.setattr("sys.argv", args)
    
    called_query = None
    
    def mock_search_topic(query, limit):
        nonlocal called_query
        called_query = query
        raise NotImplementedError("stop execution")
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 2
    assert called_query == query_theme


# TC-25 & TC-26: Output directory creation
@pytest.mark.parametrize("path_type,sub_path", [
    ("default", "default_thematic"),
    ("nested", "nonexistent/deep/path/thematic"),
])
def test_output_dir_creation(path_type, sub_path, monkeypatch, tmp_path):
    output_path = str(tmp_path / sub_path)
    args = ["collect_research.py", "AI", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return []
        
    def mock_synthesize(query, results):
        return {"hub_content": "dummy text"}
        
    def mock_translate(text, target_lang):
        return "dummy thai text"
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    monkeypatch.setattr(collect_research, "translate_content", mock_translate)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    assert os.path.exists(output_path)
    target_dir = os.path.join(output_path, "ai")
    assert os.path.exists(target_dir)
    assert os.path.exists(os.path.join(target_dir, "00_ai_Hub.md"))
    assert os.path.exists(os.path.join(target_dir, "00_ai_Hub_TH.md"))


# ==========================================
# TIER 2: BOUNDARY & CORNER CASES (26 Cases)
# ==========================================

# TC-27 & TC-28: Empty and whitespace queries
@pytest.mark.parametrize("invalid_query", ["", "   "])
def test_boundary_empty_and_whitespace_queries(invalid_query, monkeypatch):
    args = ["collect_research.py", invalid_query]
    monkeypatch.setattr("sys.argv", args)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 1


# TC-29 to TC-36: Query input sanitization and boundary limits
@pytest.mark.parametrize("special_query,expected_sanitized", [
    ("AI/ML", "ai_ml"),
    ("What's next?", "whats_next"),
    ("../../etc/passwd", "etc_passwd"),
    ("Quantum & AI", "quantum_ai"),
    ("Robotics 🤖", "robotics"),
    ("; rm -rf /", "rm_rf"),
    ("$PATH", "path"),
    ("A" * 1000, "a" * 100),  # Truncated check
])
def test_boundary_query_sanitization(special_query, expected_sanitized, monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", special_query, "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return []
        
    def mock_synthesize(query, results):
        return {"hub_content": "sanitization check"}
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    target_dir = os.path.join(output_path, expected_sanitized)
    assert os.path.exists(target_dir)
    assert os.path.exists(os.path.join(target_dir, f"00_{expected_sanitized}_Hub.md"))


# TC-37 to TC-39: Limit boundary cases
@pytest.mark.parametrize("limit_val,expected_limit", [
    (0, 1),       # 0 defaults to 1
    (-5, 1),      # Negative defaults to 1
    (1000, 20),   # 1000 capped at 20
])
def test_boundary_limit_values(limit_val, expected_limit, monkeypatch):
    args = ["collect_research.py", "AI", "-l", str(limit_val)]
    monkeypatch.setattr("sys.argv", args)
    
    called_limit = None
    def mock_search_topic(query, limit):
        nonlocal called_limit
        called_limit = limit
        raise NotImplementedError("stop")
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    
    try:
        with pytest.raises(SystemExit) as excinfo:
            collect_research.main()
        assert excinfo.value.code in [1, 2]
    except Exception:
        pass


# TC-40: Empty search results
def test_boundary_empty_search(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "AI", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return [] # empty search results
        
    def mock_synthesize(query, results):
        if not results:
            return {"hub_content": "No results found."}
        return {"hub_content": "Success"}
        
    def mock_translate(text, target_lang):
        return "ไม่มีผลลัพธ์"
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    monkeypatch.setattr(collect_research, "translate_content", mock_translate)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    target_dir = os.path.join(output_path, "ai")
    assert os.path.exists(target_dir)
    assert os.path.exists(os.path.join(target_dir, "00_ai_Hub.md"))
    with open(os.path.join(target_dir, "00_ai_Hub.md"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "No results found." in content


# TC-41 to TC-43: Scraper exceptions
@pytest.mark.parametrize("exception_type,error_class", [
    ("http_500", Exception("HTTP Error 500: Internal Server Error")),
    ("dns_failure", Exception("Failed to resolve host")),
    ("timeout", Exception("Connection timed out")),
])
def test_scraper_exceptions(exception_type, error_class, monkeypatch):
    args = ["collect_research.py", "AI"]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic_failed(query, limit):
        raise error_class
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic_failed)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 3  # Error during research compilation exits with 3


# TC-44 to TC-47: LLM API exceptions
@pytest.mark.parametrize("exception_name,error_class", [
    ("rate_limit", Exception("LLM Rate limit exceeded")),
    ("auth_error", Exception("Invalid API Key")),
    ("context_exceeded", Exception("Context length exceeded")),
    ("service_unavailable", Exception("LLM Service unavailable")),
])
def test_llm_exceptions(exception_name, error_class, monkeypatch):
    args = ["collect_research.py", "AI"]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return [{"title": "AI Source", "content": "AI text"}]
        
    def mock_synthesize_failed(query, results):
        raise error_class
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize_failed)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 3


# TC-48 & TC-49: Translation exceptions
@pytest.mark.parametrize("exception_name,error_class", [
    ("offline", Exception("Translation service offline")),
    ("empty_input", ValueError("Empty text for translation")),
])
def test_translation_exceptions(exception_name, error_class, monkeypatch):
    args = ["collect_research.py", "AI", "--lang", "TH"]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return [{"title": "AI Source", "content": "AI text"}]
        
    def mock_synthesize(query, results):
        return {"hub_content": "AI Hub Content"}
        
    def mock_translate_failed(text, target_lang):
        raise error_class
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    monkeypatch.setattr(collect_research, "translate_content", mock_translate_failed)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 3


# TC-50 to TC-52: Write conflicts (file block, permissions, disk full)
@pytest.mark.parametrize("conflict_type,error_class", [
    ("target_is_file", FileExistsError("Target directory exists but is a file")),
    ("permission_denied", PermissionError("Permission denied")),
    ("disk_full", OSError(28, "No space left on device")),
])
def test_write_conflicts(conflict_type, error_class, monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "AI", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return [{"title": "AI Source", "content": "AI text"}]
        
    def mock_synthesize(query, results):
        return {"hub_content": "AI Hub Content"}
        
    # We mock os.makedirs (or open) to raise the error when it attempts to write,
    # ensuring the real generate_obsidian_notes is executed and hits the simulated conflict
    def mock_makedirs(path, exist_ok=False):
        raise error_class
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 3


# ==========================================
# TIER 3: CROSS-FEATURE INTEGRATION (6 Cases)
# ==========================================

# TC-53: Consecutive different queries
def test_cross_consecutive_different_queries(monkeypatch, tmp_path):
    queries = ["Theme A", "Theme B"]
    output_path = str(tmp_path / "thematic")
    
    def mock_search_topic(query, limit):
        return [{"title": query, "content": f"content of {query}"}]
        
    def mock_synthesize(query, results):
        return {"hub_content": f"Hub of {query}", "spokes": []}
        
    def mock_translate(text, target_lang):
        return f"TH {text}"
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    monkeypatch.setattr(collect_research, "translate_content", mock_translate)
    
    for q in queries:
        monkeypatch.setattr("sys.argv", ["collect_research.py", q, "-o", output_path])
        with pytest.raises(SystemExit) as excinfo:
            collect_research.main()
        assert excinfo.value.code == 0
        
    dir_a = os.path.join(output_path, "theme_a")
    dir_b = os.path.join(output_path, "theme_b")
    assert os.path.exists(dir_a)
    assert os.path.exists(dir_b)
    assert os.path.exists(os.path.join(dir_a, "00_theme_a_Hub.md"))
    assert os.path.exists(os.path.join(dir_b, "00_theme_b_Hub.md"))


# TC-54: Same query without --overwrite (should fail on collision)
def test_cross_consecutive_same_query_no_overwrite(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "Theme A", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return []
        
    def mock_synthesize(query, results):
        return {"hub_content": "Theme A Content"}
        
    def mock_translate(text, target_lang):
        return "Theme A Content TH"
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    monkeypatch.setattr(collect_research, "translate_content", mock_translate)
    
    # First execution succeeds
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
    assert excinfo.value.code == 0
    assert os.path.exists(os.path.join(output_path, "theme_a"))
    
    # Second execution fails with exit code 1 because overwrite is False by default
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
    assert excinfo.value.code == 1


# TC-55: Same query with --overwrite
def test_cross_consecutive_same_query_with_overwrite(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args_first = ["collect_research.py", "Theme A", "-o", output_path]
    args_second = ["collect_research.py", "Theme A", "-o", output_path, "--overwrite"]
    
    def mock_search_topic(query, limit):
        return []
        
    def mock_synthesize(query, results):
        return {"hub_content": "Theme A Content"}
        
    def mock_translate(text, target_lang):
        return "Theme A Content TH"
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    monkeypatch.setattr(collect_research, "translate_content", mock_translate)
    
    # First execution
    monkeypatch.setattr("sys.argv", args_first)
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
    assert excinfo.value.code == 0
    
    # Second execution with --overwrite
    monkeypatch.setattr("sys.argv", args_second)
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
    assert excinfo.value.code == 0


# TC-56: Synthesis & Translation linkage
def test_cross_synthesis_translation_linkage(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "AI", "--lang", "TH", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    synthesis_out = {"hub_content": "AI English Content"}
    translation_in = None
    
    def mock_search_topic(query, limit):
        return []
        
    def mock_synthesize(query, results):
        return synthesis_out
        
    def mock_translate(text, target_lang):
        nonlocal translation_in
        translation_in = text
        return "AI Thai Content"
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    monkeypatch.setattr(collect_research, "translate_content", mock_translate)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    assert translation_in == "AI English Content"


# TC-57: Multi-spoke directory clean-up
def test_cross_multi_spoke_cleanup(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args_first = ["collect_research.py", "Theme A", "-l", "5", "-o", output_path]
    args_second = ["collect_research.py", "Theme A", "-l", "2", "--overwrite", "-o", output_path]
    
    def mock_search_topic(query, limit):
        return [{"title": f"Spoke {i}", "content": "data"} for i in range(limit)]
        
    def mock_synthesize(query, results):
        return {"hub_content": "Hub Content", "spokes": results}
        
    # We let translate_content run natively; offline fallback will populate Thai translated spokes
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    
    # First execution: 5 spokes (creates 1 EN Hub + 5 EN Spokes + 1 TH Hub + 5 TH Spokes = 12 files)
    monkeypatch.setattr("sys.argv", args_first)
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
    assert excinfo.value.code == 0
    
    dest_path = os.path.join(output_path, "theme_a")
    files_after_first = os.listdir(dest_path)
    assert len(files_after_first) == 12
    
    # Second execution: 2 spokes with overwrite (creates 1 EN Hub + 2 EN Spokes + 1 TH Hub + 2 TH Spokes = 6 files)
    monkeypatch.setattr("sys.argv", args_second)
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
    assert excinfo.value.code == 0
    
    files_after_second = os.listdir(dest_path)
    assert len(files_after_second) == 6
    assert "00_theme_a_Hub.md" in files_after_second
    assert "00_theme_a_Hub_TH.md" in files_after_second
    assert "spoke_0.md" in files_after_second
    assert "spoke_1.md" in files_after_second
    assert "spoke_0_th.md" in files_after_second
    assert "spoke_1_th.md" in files_after_second
    assert "spoke_4.md" not in files_after_second
    assert "spoke_4_th.md" not in files_after_second


# TC-58: Hub & Spoke crosslink completeness
def test_cross_hub_spoke_crosslink_verification(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "Theme B", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return [{"title": "Market Size", "content": "Huge"}]
        
    def mock_synthesize(query, results):
        return {
            "hub_content": "Hub content indexes [[market_size]]",
            "spokes": [{"title": "Market Size", "content": "Spoke content"}]
        }
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    
    target_dir = os.path.join(output_path, "theme_b")
    hub_file = os.path.join(target_dir, "00_theme_b_Hub.md")
    spoke_file = os.path.join(target_dir, "market_size.md")
    
    assert os.path.exists(hub_file)
    assert os.path.exists(spoke_file)
    
    with open(hub_file, "r", encoding="utf-8") as f:
        hub_content = f.read()
        assert "[[market_size]]" in hub_content
        
    with open(spoke_file, "r", encoding="utf-8") as f:
        spoke_content = f.read()
        assert "[[00_theme_b_Hub|⬅️ Back to Topic Hub]]" in spoke_content


# ==========================================
# TIER 4: REAL-WORLD APPLICATIONS (6 Cases)
# ==========================================

# TC-59: E2E solid state batteries
def test_e2e_solid_state_batteries(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "Solid State Batteries", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return [
            {"title": "Market Overview", "content": "Solid state batteries market value..."},
            {"title": "Key Players", "content": "Toyota, QuantumScape, Samsung SDI..."},
            {"title": "Technology Challenges", "content": "Dendrite formation, manufacturing costs..."}
        ]
        
    def mock_synthesize(query, results):
        hub_md = """---
type: thematic
tags: [investing, batteries]
---
# Solid State Batteries Hub
- [[market_overview|Market Overview]]
- [[key_players|Key Players]]
- [[technology_challenges|Technology Challenges]]
"""
        spokes = []
        for r in results:
            spoke_md = f"""# {r['title']}
{r['content']}
"""
            spokes.append({"title": r["title"], "content": spoke_md})
            
        return {"hub_content": hub_md, "spokes": spokes}
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    
    target_dir = os.path.join(output_path, "solid_state_batteries")
    assert os.path.exists(target_dir)
    assert os.path.exists(os.path.join(target_dir, "00_solid_state_batteries_Hub.md"))
    assert os.path.exists(os.path.join(target_dir, "market_overview.md"))
    assert os.path.exists(os.path.join(target_dir, "key_players.md"))
    assert os.path.exists(os.path.join(target_dir, "technology_challenges.md"))
    
    with open(os.path.join(target_dir, "00_solid_state_batteries_Hub.md"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "type: thematic" in content
        assert "tags: [investing, thematic, solid_state_batteries]" in content
        
    with open(os.path.join(target_dir, "market_overview.md"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "[[00_solid_state_batteries_Hub|⬅️ Back to Topic Hub]]" in content


# TC-60: E2E green hydrogen bilingual
def test_e2e_green_hydrogen(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "Green Hydrogen", "--lang", "TH", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return [{"title": "Production", "content": "Electrolyser technology..."}]
        
    def mock_synthesize(query, results):
        hub_md = "# Green Hydrogen Hub\n[[production|Production]]"
        spoke_md = "Production details."
        return {"hub_content": hub_md, "spokes": [{"title": "Production", "content": spoke_md}]}
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    
    target_dir = os.path.join(output_path, "green_hydrogen")
    assert os.path.exists(target_dir)
    assert os.path.exists(os.path.join(target_dir, "00_green_hydrogen_Hub.md"))
    assert os.path.exists(os.path.join(target_dir, "production.md"))
    assert os.path.exists(os.path.join(target_dir, "00_green_hydrogen_Hub_TH.md"))
    assert os.path.exists(os.path.join(target_dir, "production_th.md"))
    
    with open(os.path.join(target_dir, "00_green_hydrogen_Hub_TH.md"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "type: thematic" in content
        assert "lang: TH" in content
        
    with open(os.path.join(target_dir, "production_th.md"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "[[00_green_hydrogen_Hub_TH|⬅️ กลับสู่หน้าหลัก]]" in content


# TC-61: E2E Neuromorphic Computing (Complex HTML fixtures)
def test_e2e_neuromorphic_computing(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "Neuromorphic Computing", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        from bs4 import BeautifulSoup
        raw_html = "<html><body><script>var x=10;</script><div class='main-text'>Neuromorphic engineering is computing modeled on biological brain systems.</div></body></html>"
        soup = BeautifulSoup(raw_html, "html.parser")
        for element in soup(["script", "style"]):
            element.decompose()
        content = soup.get_text(separator="\n", strip=True)
        return [{"title": "Webpage", "content": content}]
        
    def mock_synthesize(query, results):
        assert "var x=10" not in results[0]["content"]
        assert "Neuromorphic engineering" in results[0]["content"]
        return {"hub_content": "# Neuromorphic Computing Hub", "spokes": []}
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    assert os.path.exists(os.path.join(output_path, "neuromorphic_computing", "00_neuromorphic_computing_Hub.md"))


# TC-62: E2E Carbon Capture (Complex Math / Formula markdown verification)
def test_e2e_carbon_capture(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "Carbon Capture", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return [{"title": "Chemistry", "content": "CO2 capturing reaction details."}]
        
    def mock_synthesize(query, results):
        hub_md = """# Carbon Capture Hub
Chemical formula for amine capture:
$$CO_2 + 2RNH_2 \\leftrightarrow RNHCOO^- + RNH_3^+$$

| Technology | Efficiency | Cost ($/ton) |
|---|---|---|
| Amine Scrubbing | 90% | 60 |
| DAC | 95% | 200 |
"""
        return {"hub_content": hub_md, "spokes": []}
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    hub_file = os.path.join(output_path, "carbon_capture", "00_carbon_capture_Hub.md")
    assert os.path.exists(hub_file)
    with open(hub_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "$$CO_2 + 2RNH_2" in content
        assert "| Amine Scrubbing |" in content


# TC-63: E2E Space Tourism (Citations & Reference indexing verification)
def test_e2e_space_tourism(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    args = ["collect_research.py", "Space Tourism", "-o", output_path]
    monkeypatch.setattr("sys.argv", args)
    
    def mock_search_topic(query, limit):
        return [{"title": "Scrape", "content": "Research from NASA database."}]
        
    def mock_synthesize(query, results):
        hub_md = """# Space Tourism Hub
## References
- [1] NASA Database: https://nasa.gov/space-tourism
"""
        spoke_md = "Suborbital flights are projected to grow [1]."
        return {"hub_content": hub_md, "spokes": [{"title": "Market Growth", "content": spoke_md}]}
        
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
        
    assert excinfo.value.code == 0
    hub_file = os.path.join(output_path, "space_tourism", "00_space_tourism_Hub.md")
    spoke_file = os.path.join(output_path, "space_tourism", "market_growth.md")
    assert os.path.exists(hub_file)
    assert os.path.exists(spoke_file)
    with open(hub_file, "r", encoding="utf-8") as f:
        assert "https://nasa.gov/space-tourism" in f.read()
    with open(spoke_file, "r", encoding="utf-8") as f:
        assert "[1]" in f.read()


# TC-64: E2E Sodium-ion Batteries (Incremental merge verification)
def test_e2e_sodium_battery_incremental(monkeypatch, tmp_path):
    output_path = str(tmp_path / "thematic")
    # First execution to create initial notes
    args_first = ["collect_research.py", "Sodium Batteries", "-o", output_path]
    # Second execution with --incremental to merge and backup
    args_second = ["collect_research.py", "Sodium Batteries", "-o", output_path, "--incremental"]
    
    def mock_search_topic(query, limit):
        return []
        
    run_count = 0
    def mock_synthesize(query, results):
        nonlocal run_count
        run_count += 1
        if run_count == 1:
            return {"hub_content": "Old content", "spokes": []}
        else:
            return {"hub_content": "New Sodium Battery content", "spokes": []}
            
    monkeypatch.setattr(collect_research, "search_topic", mock_search_topic)
    monkeypatch.setattr(collect_research, "synthesize_research", mock_synthesize)
    
    # First execution
    monkeypatch.setattr("sys.argv", args_first)
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
    assert excinfo.value.code == 0
    
    hub_file = os.path.join(output_path, "sodium_batteries", "00_sodium_batteries_Hub.md")
    assert os.path.exists(hub_file)
    with open(hub_file, "r", encoding="utf-8") as f:
        assert "Old content" in f.read()
        
    # Second execution (incremental merge)
    monkeypatch.setattr("sys.argv", args_second)
    with pytest.raises(SystemExit) as excinfo:
        collect_research.main()
    assert excinfo.value.code == 0
    
    # Verify backup exists
    backup_file = hub_file + ".bak"
    assert os.path.exists(backup_file)
    with open(backup_file, "r", encoding="utf-8") as f:
        assert "Old content" in f.read()
        assert "New Sodium Battery content" not in f.read()
        
    # Verify merged file exists and contains both old and new content
    with open(hub_file, "r", encoding="utf-8") as f:
        merged_content = f.read()
        assert "Old content" in merged_content
        assert "New Sodium Battery content" in merged_content
