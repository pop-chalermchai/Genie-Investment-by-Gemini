# Standard Operating Procedure: Web Development Protocol

This document defines the strict standard operating procedure (SOP) for developing, testing, and deploying changes to the Genie Investment web applications.

---

## 💡 Core Philosophy: Local-First Development
To mitigate production downtime risks, maintain clean Git history (audit trail), and ensure a fast development cycle, all website modifications must follow a **Local-First** workflow. No code changes should be deployed directly to production (Vercel) without complete local validation.

---

## 🔄 The 5-Step Development Pipeline

```mermaid
graph TD
    A["1. Local Development & Validation<br>(http://localhost:8000)"] -->|Verify no console errors / full functionality| B["2. Code Review Gate<br>(Lex — The Code Sentinel)"]
    B -->|✅ APPROVED — CLEAR TO COMMIT| C["3. Targeted Code Commit<br>(git commit -m '...')"]
    B -->|🚫 REJECTED — Fix required, re-submit| A
    C -->|Stage and record verified code| D["4. Deploy to GitHub<br>(git push origin main)"]
    D -->|Trigger Vercel Automatic Build| E["5. Production Verification<br>(Hard Reload / Cache Clearance)"]
```

### Phase 1: Local Development & Validation (Local Testing)
1. **Start Local Server:** Always run the local development server before editing files.
   * **Command:** `python3 my_first_website/server.py`
   * **Address:** `http://localhost:8000`
2. **Development:** Implement features or bug fixes directly within the workspace folder (`/my_first_website/`).
3. **Local Audit:** Open the local site in a web browser. Test all interactive features, inspect the developer console for warnings/errors, and ensure layout responsiveness.

### Phase 2: Code Review Gate (Lex — The Code Sentinel)
Before any code is staged for commit, invoke **Lex (The Code Sentinel)** to perform a structured technical audit.
* **Prompt to Lex:** "Review the following code changes for the Genie Investment web platform. Audit for: (1) Security vulnerabilities, (2) Logic bugs and correctness, (3) Performance issues, (4) SOP_Web_Development.md compliance. Files changed: [list modified files]. Output a structured report with severity-classified findings (🔴 CRITICAL / 🟡 WARNING / 🟢 SUGGESTION) with file:line references, and conclude with a clear ✅ APPROVED or 🚫 REJECTED verdict."
* **Gate Rule:** Code may only proceed to Phase 3 (git commit) after Lex issues a `✅ APPROVED — CLEAR TO COMMIT` verdict. A `🚫 REJECTED` verdict requires fixing all CRITICAL and WARNING items and re-submitting to Lex.

### Phase 3: In-Place Code Editing (Token-Efficiency Protocol)
1. **Avoid Full Rewrites:** Do not replace entire files (especially large files like `app.js` or `server.py`) to avoid hitting AI token limits and context bloat.
2. **Targeted Editing:** Use targeted editing tools (`replace_file_content` or `multi_replace_file_content`) to modify only the specific blocks of code requiring changes.

### Phase 4: Version Control & Code Governance (Git)
1. **Stage Changes:** Stage only verified files that are confirmed to work locally (`git add`).
2. **Commit Message:** Write clear, professional, and audit-ready commit messages explaining the change (e.g., `git commit -m "Implement HTML5 History API path routing (pushState/popstate)"`). Avoid generic messages like "fix" or "update".

### Phase 5: Production Deployment & Final Verification
1. **Push to GitHub:** Push the clean commits to the remote repository:
   * **Command:** `git push origin main`
2. **Vercel Automatic Build:** Allow Vercel to automatically compile the build from GitHub (takes 1-2 minutes).
3. **Hard Reload (Cache Clearance):** Clear browser caches to load the updated Javascript/CSS files:
   * **macOS:** `Cmd + Shift + R` (or hold `Shift` and click the refresh button)
   * **Windows/Linux:** `Ctrl + F5`
4. **Final Audit:** Confirm the live Vercel deployment works flawlessly and behaves exactly as validated locally.
