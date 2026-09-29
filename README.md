# AI Coding Tutor - Pedagogical Companion Extension

An intelligent, stateful pedagogical layer injected directly into LeetCode that helps learners understand coding patterns, debug errors, and optimize complexity *without* giving away the solution. 

This project was built for a hackathon vertical slice showcasing **LeetCode Two Sum** with real-time code execution, AST complexity analysis, and context-grounded tutor conversations.

---

## 📂 Repository Structure

```
d:/mai/
├── README.md                      # Setup & Demo Guide (This file)
├── IMPLEMENTATION_STATUS.md      # Milestone & Bugfix log
├── prd.txt                       # Raw domain data
│
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI server (CORS enabled)
│   │   ├── config.py             # Settings manager (picks up .env)
│   │   ├── database.py           # SQLite connection & engine
│   │   ├── models.py             # SQLAlchemy models (Attempt, User)
│   │   └── tutor/
│   │       ├── orchestrator.py   # State coordinator
│   │       ├── policy.py         # Progressive hint state policies
│   │       ├── llm_provider.py   # Groq/Grok/Fallback providers
│   │       ├── learner_model.py  # DB updates & recommendations
│   │       └── analysis/
│   │           ├── static_analyzer.py      # AST nested loop analyzer
│   │           ├── complexity_analyzer.py  # Big-O estimation
│   │           ├── pattern_analyzer.py     # Static signature checks
│   │           └── execution_analyzer.py   # Subprocess code execution sandbox
│   │
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # API keys & endpoints configuration
│   └── tests/
│       ├── test_tutor_core.py    # Generality unit tests
│       └── test_end_to_end_local.py # End-to-end local diagnostic simulator
│
└── extension/
    ├── manifest.json             # Manifest V3 configuration (host permissions enabled)
    ├── content.js                # LeetCode DOM scraper & sidebar injector
    ├── sidebar.html              # Frost-glass tutor sidebar UI
    ├── sidebar.js                # Frontend controller & API fetch dispatcher
    └── sidebar.css               # Premium CSS dark theme layouts & charts
```

---

## ⚡ Quick Start: Running the Entire System

### Prerequisites
1. **Python 3.11+** installed.
2. **Google Chrome** browser.
3. A **Groq API Key** (starts with `gsk_`) or **Grok API Key**. 
   *(If no API key is available, the system will seamlessly run using the static `DemoFallbackProvider` for offline evaluation).*

---

### Step 1: Configure & Run the Backend

1. **Navigate to the Backend Directory:**
   ```bash
   cd backend
   ```

2. **Configure your Environment Variables (`.env`):**
   Create a `.env` file inside the `backend/` directory and populate it:
   ```env
   # SQLite database location (initialized automatically)
   DATABASE_URL=sqlite:///./tutor.db

   # Put your Groq API Key (gsk_...) here. 
   # The backend automatically detects the prefix and routes to Groq (llama-3.1-8b-instant).
   GROK_API_KEY=sample
   ```

3. **Install Dependencies:**
   Create a virtual environment, activate it, and install required libraries:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

4. **Verify the Backend Core via Automated Tests:**
   Run pytest to make sure the AST analyzers, policy orchestrators, and database schemas build correctly:
   ```bash
   python -m pytest tests/
   ```

5. **Start the FastAPI Server:**
   Launch the development server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
   *The server is active when you see: `Uvicorn running on http://127.0.0.1:8000`.*
   *You can visit the health check at `http://127.0.0.1:8000/health` to confirm the selected LLM provider is active.*

---

### Step 2: Load the Chrome Extension

1. Open Google Chrome and go to `chrome://extensions/`.
2. Toggle on **Developer mode** in the top-right corner.
3. Click the **Load unpacked** button in the top-left.
4. Select the `extension/` folder from this repository.
5. The extension card **AI Coding Tutor - Antigravity** will now be loaded.

---

## 🎯 Running the Golden Demo Flow (LeetCode)

Now, test the vertical slice using **LeetCode's Two Sum problem**:

1. Navigate to the [LeetCode Two Sum Problem](https://leetcode.com/problems/two-sum/).
2. You will see a gradient **AI Tutor** floating button on the bottom-right. Click it to slide open the glassmorphic sidebar.
3. Open the Chrome DevTools console:
   * Right-click inside the AI Tutor sidebar panel and select **Inspect**.
   * Switch to the **Console** tab to view live diagnostic logs (e.g., `[Tutor DEBUG] Sync: <button id="sync-btn" ...>`).
4. Click **Sync** to capture the page details.

### Test A: Brute Force Code & Progressive Hints
* **In the LeetCode Editor, write a nested-loop $O(n^2)$ solution:**
  ```python
  class Solution:
      def twoSum(self, nums: list[int], target: int) -> list[int]:
          for i in range(len(nums)):
              for j in range(len(nums)):
                  if nums[i] + nums[j] == target:
                      return [i, j]
  ```
* **Click Analyze Code:** The backend execution analyzer runs the code, registers that logic passed, determines $O(n^2)$ complexity, and switches the tutor to Hint Level 1.
* **Request Next Hint:** Click **Ask for Next Hint** in the suggestion box. The system escalates to Hint Level 2 (introducing lookbehind complement lookup concepts).
* **Optimization Tab:** Switch to the **Optimization** tab. The $O(n^2)$ Brute Force card will glow to reflect your current complexity profile.

### Test B: Context-Grounded Code Chat
* **Ask a general question:** In the chat box, type *"Why is my code O(n^2)?"* and hit Enter.
* **Observe Response:** Instead of a generic reply, the tutor parses the *current editor code* and explains: *"Your code is O(n^2) because the inner loop `for j in range(len(nums)):` runs for each iteration of the outer loop `for i in range(len(nums)):`..."*

### Test C: Surfacing Logical Bugs
* **Introduce a bug in the editor:** Modify the loop boundaries so it evaluates the same index twice (e.g., `for j in range(len(nums))` without preventing `i == j`).
* **Click Analyze Code:** The sandbox compiler execution fails validation tests. The tutor identifies the same-element reuse issue and guides you: *"It looks like your code returns indices that point to the exact same element... Think about how you can check that indices are distinct."*

### Test D: Optimal Code & Teach-Back Verification
* **Write the optimal $O(n)$ Hash Map solution in LeetCode:**
  ```python
  class Solution:
      def twoSum(self, nums: list[int], target: int) -> list[int]:
          seen = {}
          for i, num in enumerate(nums):
              complement = target - num
              if complement in seen:
                  return [seen[complement], i]
              seen[num] = i
  ```
* **Click Analyze Code:** The sandbox executor validates correct execution, registers $O(n)$ complexity, and triggers **Teach-Back mode**, asking: *"Why does using a Hash Map reduce the time complexity from O(n²) to O(n), and what is the trade-off?"*
* **Complete the Teach-Back:** Answer in the chat: *"Hash maps give O(1) lookups instead of loops, giving up O(n) space."*
* **Personalized Profile Update:** Switch to the **My Profile** tab. Your mastery metrics dynamically increment (Hash Maps $\rightarrow$ 81%, Complexity $\rightarrow$ 64%) and an explainable recommendation for *Sliding Window* practice is surfaced.

---

## 🛠️ Diagnostics & Troubleshooting

* **Check connection:** Visit `http://127.0.0.1:8000/api/diagnostics` directly in the browser. It displays active LLM settings and database connection status.
* **CORS Errors:** If the console reports CORS blocks, confirm that `allow_credentials=False` is set in `app/main.py` CORS middleware (wildcards cannot use credentials).
* **Chrome Extension fetch block:** Confirm that `manifest.json` contains `"host_permissions": ["http://localhost:8000/*"]` to permit extension-level localhost fetches.
* **Sandbox Execution Errors:** If Python code execution is failing due to character syntax, ensure Monaco DOM scraper normalization replaces non-breaking space characters (`\u00a0`) to standard spaces inside `content.js`.
