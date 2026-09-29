# Implementation Status

## Current Milestone
- Milestone 8 — "The tutor tells me what to learn next" (Complete, Verified End-to-End)

## Completed
- **Milestone 1 — "I can open the tutor"**
- **Milestone 2 — "The tutor understands what I'm doing"**
- **Milestone 3 — "The tutor understands my mistake"**
- **Milestone 4 — "The tutor teaches instead of solving"**
- **Milestone 5 — "The tutor helps me optimize"**
- **Milestone 6 — "The tutor verifies that I learned"**
- **Milestone 7 — "The tutor remembers me"**
- **Milestone 8 — "The tutor tells me what to learn next"**

## Dynamic Chat Endpoint Added
- **`POST /api/chat`**
  - Accepts `message`, `problem_title`, `code`, `language`, `tutor_state`, and `conversation_history`.
  - Runs the static analysis and correctness pipeline on the *current* code in the request.
  - Generates context-grounded answers based on the user's question, the current code, and the latest analysis results without giving away full code solutions.
  - Preserves the tutor policy hint level state.

## Bugs Found & Repaired

1. **Decommissioned Groq Model:**
   - *Bug:* The model name `llama3-8b-8192` originally requested is decommissioned on Groq.
   - *Fix:* Switched default to the active and recommended `llama-3.1-8b-instant` model.
2. **Provider Key Collision:**
   - *Bug:* A Groq API key (`gsk_...`) was provided under the xAI/Grok configuration field.
   - *Fix:* Added auto-detection in `config.py` that redirects traffic to the Groq API provider when a `gsk_` prefix is detected.
3. **Environment Config Path Resolution:**
   - *Bug:* The settings manager looked for `.env` only in the current working directory. Starting uvicorn from the workspace root caused it to miss `backend/.env`.
   - *Fix:* Set `env_file = ("backend/.env", ".env")` to search both paths recursively.
4. **CORS Allow-Credentials Collision:**
   - *Bug:* CORS allowed wildcard origins `["*"]` but also set `allow_credentials=True`, which is blocked by modern browsers for security.
   - *Fix:* Set `allow_credentials=False` since our endpoints do not require session cookies.
5. **Missing MV3 Host Permissions:**
   - *Bug:* Chrome Manifest V3 blocked fetch requests from the extension iframe to `http://localhost:8000` because no host permissions were declared.
   - *Fix:* Added `"host_permissions": ["http://localhost:8000/*"]` to `manifest.json`.
6. **Monaco Editor Space Character Parsing:**
   - *Bug:* Code lines scraped from LeetCode Monaco DOM contain non-breaking space characters (`\u00a0`), causing Python compile `SyntaxError` on local tests.
   - *Fix:* Added string replacement `code.replace(/\u00a0/g, ' ')` in `content.js`.
7. **Complexity Confidence Lock:**
   - *Bug:* The default complexity placeholder was initialized with a confidence of `1.0`, preventing `ComplexityAnalyzer` (confidence `0.80`) from overwriting it.
   - *Fix:* Set default complexity confidence to `0.0` in `models.py`.
8. **Extension Append Safety:**
   - *Bug:* If the tutor response was null, empty, or undefined, `appendMessage` crashed on `.replace` calls.
   - *Fix:* Added `content = content || ""` fallback in `sidebar.js`.
9. **Missing Diagnostic Endpoints:**
   - *Bug:* No easy endpoints to diagnose key configuration status or connection details.
   - *Fix:* Added `/health` and `/api/diagnostics` to `main.py`.
10. **Developer Logging Visibility:**
    - *Bug:* Insufficient logging details to trace failures at runtime.
    - *Fix:* Wired console logging throughout `sidebar.js` and stdout prints in `llm_provider.py`.
11. **Chat Prompt KeyError:**
    - *Bug:* The system prompt for the chat handler contained JSON schema curly braces (`{` and `}`), causing Python's `.format` call to raise a `KeyError`.
    - *Fix:* Escaped the JSON schema brackets to `{{` and `}}` in `llm_provider.py`.

## Demo Status
- **Extension:** PASS (MV3 compliant, handles cross-origin fetch, scrapes Monaco, normalizes whitespace, logs debug markers)
- **Context:** PASS (Title, description, normalized code, language synced)
- **Backend:** PASS (FastAPI online, SQLite tables initialized, CORS enabled, `/api/chat` route active)
- **Groq Provider:** PASS (Llama-3.1-8b-instant live responses via Groq client, escaped prompts)
- **Demo Fallback:** PASS (Fallback checks complexity signals and returns staged optimization hints and mock chat replies)
- **End-to-End Golden Demo:** PASS (Verified from O(n^2) brute force attempt, progressive hints, O(n) optimal solution, teach-back evaluation, and recommendations updates)
