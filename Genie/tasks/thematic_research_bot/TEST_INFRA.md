# Test Infrastructure: Thematic Research Bot

This document outlines the test architecture, test cases, and offline execution plan for the Thematic Research Bot.

## Overview
The Thematic Research Bot compiles investment research into Obsidian Hub and Spoke markdown notes. Because network access is restricted in CODE_ONLY mode, the test suite utilizes `pytest` with parameterized test cases and comprehensive Python mocks to simulate CLI execution, web scraping (using HTML fixtures), LLM synthesis, translation, and filesystem operations.

---

## Test Suite Structure
The test suite is divided into 4 tiers, covering a minimum of 60 test cases:

- **Tier 1: Feature Coverage (>=25 test cases)** – Validates CLI arguments, basic option parsing, directory creation, and query parameterization.
- **Tier 2: Boundary & Corner Cases (>=25 test cases)** – Validates input sanitization, empty queries, special characters, directory traversal attempts, network failures, LLM API exceptions, translation errors, and filesystem write blocks.
- **Tier 3: Cross-Feature Integration (>=5 test cases)** – Validates interaction between search, synthesis, and translation; handles consecutive queries (same or different) with and without overwrite flags.
- **Tier 4: Real-World Applications (>=5 test cases)** – End-to-end flow execution using local mock fixtures to verify directory structure, Hub & Spoke links, frontmatter properties, and translation outputs.

---

## Mapped Test Cases

### Tier 1: Feature Coverage (26 Cases)

| Test Case ID | Name | Description | Input / Parameters | Expected Behavior |
|---|---|---|---|---|
| **TC-01** | `test_cli_positional_query` | Valid positional query input | `sys.argv = ["collect_research.py", "Solid State Batteries"]` | Parses query as "Solid State Batteries" |
| **TC-02** | `test_cli_option_query_short` | Valid short option query | `sys.argv = ["collect_research.py", "-q", "Green Hydrogen"]` | Parses query as "Green Hydrogen" |
| **TC-03** | `test_cli_option_query_long` | Valid long option query | `sys.argv = ["collect_research.py", "--query-opt", "Green Hydrogen"]` | Parses query as "Green Hydrogen" |
| **TC-04** | `test_cli_output_dir_short` | Custom output directory short flag | `sys.argv = ["collect_research.py", "AI", "-o", "/tmp/obsidian"]` | Output directory set to `/tmp/obsidian` |
| **TC-05** | `test_cli_output_dir_long` | Custom output directory long flag | `sys.argv = ["collect_research.py", "AI", "--output-dir", "/tmp/obsidian"]` | Output directory set to `/tmp/obsidian` |
| **TC-06** | `test_cli_limit_short` | Custom limit short flag | `sys.argv = ["collect_research.py", "AI", "-l", "3"]` | Search limit parameter set to 3 |
| **TC-07** | `test_cli_limit_long` | Custom limit long flag | `sys.argv = ["collect_research.py", "AI", "--limit", "10"]` | Search limit parameter set to 10 |
| **TC-08** | `test_cli_overwrite_flag` | Overwrite flag option | `sys.argv = ["collect_research.py", "AI", "--overwrite"]` | Overwrite option set to True |
| **TC-09** | `test_cli_lang_flag` | Custom translation language option | `sys.argv = ["collect_research.py", "AI", "--lang", "TH"]` | Target language set to "TH" |
| **TC-10** to **TC-24** | `test_query_parameterization[<theme>]` | Verification of query parameter handling for 15 diverse investment themes | Parameterized list of 15 queries (e.g. "Quantum Computing", "Fusion Energy", "Gene Editing", etc.) | Query string parsed and passed to search function correctly |
| **TC-25** | `test_output_dir_creation_default` | Automatically creates missing target directory | Directory `/Users/popular/Desktop/Genie/thematic/` does not exist | Directory is created recursively on execution |
| **TC-26** | `test_output_dir_creation_nested` | Creates deeply nested directory | Custom path: `/tmp/nonexistent/deep/path/thematic` | Directory path is created recursively without error |

---

### Tier 2: Boundary & Corner Cases (26 Cases)

| Test Case ID | Name | Description | Input / Parameters | Expected Behavior |
|---|---|---|---|---|
| **TC-27** | `test_boundary_empty_query` | Query is empty string | `sys.argv = ["collect_research.py", ""]` | Exits with status code 1, prints error |
| **TC-28** | `test_boundary_whitespace_query` | Query is whitespace only | `sys.argv = ["collect_research.py", "   "]` | Exits with status code 1, prints error |
| **TC-29** | `test_boundary_special_char_slash` | Query contains slashes | `"AI/ML"` | Query is sanitized to avoid directory traversal (e.g. folder name `ai_ml`) |
| **TC-30** | `test_boundary_special_char_quotes` | Query contains quotes | `"What's next?"` | Query is sanitized to safe folder name `whats_next` |
| **TC-31** | `test_boundary_directory_traversal` | Query attempts directory traversal | `../../etc/passwd` | Directory traversal prevented; folder created under target dir |
| **TC-32** | `test_boundary_special_char_xml` | Query contains HTML/XML entities | `"Quantum & AI"` | Ampersand sanitized to safe characters |
| **TC-33** | `test_boundary_special_char_unicode` | Query contains emojis/unicode | `"Robotics 🤖"` | Unicode characters handled safely in files/folders |
| **TC-34** | `test_boundary_shell_injection` | Query attempts shell injection | `"; rm -rf /"` | Input is handled strictly as string, no shell evaluation |
| **TC-35** | `test_boundary_env_expansion` | Query attempts environment expansion | `"$PATH"` | Literal `"$PATH"` parsed, no expansion |
| **TC-36** | `test_boundary_very_long_query` | Query is extremely long | String of 1000 "A"s | String truncated or rejected if exceeding limit |
| **TC-37** | `test_boundary_limit_zero` | Search limit set to zero | `--limit 0` | Triggers validation error or defaults to safe value |
| **TC-38** | `test_boundary_limit_negative` | Search limit set to negative | `--limit -5` | Raises argparse or validation error |
| **TC-39** | `test_boundary_limit_large` | Search limit set to very high value | `--limit 1000` | Capped at a reasonable max (e.g. 10 or 20) |
| **TC-40** | `test_boundary_empty_search_results` | Scraper returns no results | HTML search mock returns no data | Gracefully exits or creates a Hub with a warning |
| **TC-41** | `test_error_scraper_http_500` | Scraper receives HTTP 500 error | Mock requests throwing HTTPError | Gracefully exits with error code 3 |
| **TC-42** | `test_error_scraper_dns_failure` | Scraper experiences DNS error | Mock requests throwing ConnectionError | Gracefully exits with error code 3 |
| **TC-43** | `test_error_scraper_timeout` | Scraper experiences timeout | Mock requests throwing TimeoutError | Gracefully exits with error code 3 |
| **TC-44** | `test_error_llm_rate_limit` | LLM API rate limited (HTTP 429) | Mock API throwing RateLimitError | Retries or reports failure cleanly |
| **TC-45** | `test_error_llm_auth` | LLM API authentication error | Mock API throwing AuthenticationError | Reports failure, exits with error code 3 |
| **TC-46** | `test_error_llm_context_exceeded` | LLM input exceeds context limits | Mock API throwing ContextLengthExceeded | Handles truncation or reports error |
| **TC-47** | `test_error_llm_service_unavailable` | LLM API service unavailable | Mock API throwing ServiceUnavailable | Exits cleanly, reporting downstream offline |
| **TC-48** | `test_error_translation_offline` | Translation service offline | Mock translator throwing exception | Completes English notes, warns translation failed |
| **TC-49** | `test_error_translation_empty` | Translation receives empty text | Translating empty/None input | Handles gracefully without crashing |
| **TC-50** | `test_write_conflict_file_exists` | Target directory exists but is a file | Directory path is blocked by a file | Reports conflict error, exits cleanly |
| **TC-51** | `test_write_conflict_permission_denied` | Target directory is read-only | PermissionError on file creation | Reports PermissionError, exits cleanly |
| **TC-52** | `test_write_conflict_disk_full` | Disk full during write operations | OSError (ENOSPC) during write | Handles error, attempts cleanup, exits |

---

### Tier 3: Cross-Feature Integration (6 Cases)

| Test Case ID | Name | Description | Input / Parameters | Expected Behavior |
|---|---|---|---|---|
| **TC-53** | `test_cross_consecutive_different_queries` | Run query A then query B | "Theme A" then "Theme B" | Both directories are created separately under `/thematic/` with no overlapping files |
| ****TC-54**** | `test_cross_consecutive_same_query_no_overwrite` | Run same query twice without `--overwrite` | "Solid State Batteries" (twice) | Second run fails or prompts, does not overwrite existing files |
| **TC-55** | `test_cross_consecutive_same_query_with_overwrite` | Run same query twice with `--overwrite` | "Solid State Batteries" (twice) | Overwrites existing files with updated content cleanly |
| **TC-56** | `test_cross_synthesis_translation_linkage` | Synthesis & Translation linkage | Bilingual execution | Translated Hub & Spokes link to translation counterparts |
| **TC-57** | `test_cross_multi_spoke_cleanup` | Overwrite reduces number of spokes | Run with 5 spokes, then overwrite with 2 spokes | Only the 2 new spokes exist; leftover spokes are removed or cleaned up |
| **TC-58** | `test_cross_hub_spoke_crosslink_verification` | Link matrix completeness | Multiple spokes generated | All spokes appear in Hub's index; all spokes link back to Hub |

---

### Tier 4: Real-World Applications (6 Cases)

| Test Case ID | Name | Description | Mock Scraped Content / Fixtures | Expected Output / Verifications |
|---|---|---|---|---|
| **TC-59** | `test_e2e_solid_state_batteries` | End-to-end test for "Solid State Batteries" | Mocks for battery tech papers and market reports | Verifies creation of folder `solid_state_batteries/`, Hub file, spokes (e.g. `market_overview.md`), YAML frontmatter (`type: thematic`), and footer links `[[solid_state_batteries_Hub\|Back to Hub]]` |
| **TC-60** | `test_e2e_green_hydrogen` | End-to-end bilingual test for "Green Hydrogen" | Mocks for hydrogen production reports | Verifies creation of English & Thai files (`green_hydrogen_Hub_TH.md`), Thai Spokes linking to Thai Hub with translated footer link `[[green_hydrogen_Hub_TH\|กลับสู่หน้าหลัก]]` |
| **TC-61** | `test_e2e_neuromorphic_computing` | Complex HTML parsing and layout test | Mock HTML with embedded complex JavaScript and structures | Verification that scraper successfully extracts core text and LLM produces correct tables |
| **TC-62** | `test_e2e_carbon_capture` | Math and financial projection verification | Mock reports containing formulas, calculations, and estimates | Verification that Hub/Spokes contain math blocks (LaTeX) and tables, formatted correctly in markdown |
| **TC-63** | `test_e2e_space_tourism` | Footnote and citations validation | Multiple sources with detailed URLs | Verifies that all assertions in spokes contain `[^1]` style references, pointing to links in Hub's references |
| **TC-64** | `test_e2e_sodium_battery_incremental` | Incremental data addition | Existing files under target folder | Verify incremental merging or backup generation of the Hub note |

---

## Execution Environment
1. **Runner**: Python `pytest`.
2. **Offline enforcement**: All network-accessing libraries (e.g. `requests`, `urllib`, `openai`, `google-generativeai`) are mocked at the module level.
3. **Observation/Assertion**: Assertions verify CLI exit codes, directory structure creation under the target path, file contents, YAML frontmatter keys, and wiki-link formats.
