console.log("[Tutor DEBUG] sidebar.js LOADED");

// Sidebar UI controller logic

const API_BASE = "http://localhost:8000";

let currentContext = null;
let tutorState = {
  mode: "debug",
  hint_level: 0
};
let isWaiting = false;
let conversationHistory = [];

document.addEventListener('DOMContentLoaded', () => {
  console.log("[Tutor DEBUG] sidebar initialization started");
  initTabs();
  initListeners();
  loadInitialProfile();
});

// 1. Tab Navigation
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  const panels = document.querySelectorAll('.tab-panel');
  
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetPanel = tab.getAttribute('data-tab');
      
      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      document.getElementById(targetPanel).classList.add('active');
    });
  });
}

// 2. Event Listeners
function initListeners() {
  const syncBtn = document.getElementById('sync-btn');
  const analyzeBtn = document.getElementById('analyze-btn');
  const hintBtn = document.getElementById('hint-btn');
  const sendBtn = document.getElementById('send-btn');
  const chatInput = document.getElementById('chat-input');
  const resetBtn = document.getElementById('reset-btn');

  console.log("[Tutor DEBUG] Sync:", syncBtn);
  console.log("[Tutor DEBUG] Analyze:", analyzeBtn);
  console.log("[Tutor DEBUG] Next Hint:", hintBtn);
  console.log("[Tutor DEBUG] Send:", sendBtn);

  // Trigger DOM scraping from LeetCode page context
  syncBtn.addEventListener('click', () => {
    console.log("[Tutor DEBUG] SYNC CLICKED");
    console.log("[Tutor] Sync clicked. Requesting code context from LeetCode page.");
    appendSystemMessage("Requesting code context from LeetCode...");
    window.parent.postMessage({ type: 'GET_CONTEXT' }, '*');
  });

  // Listener for scraped responses from content.js
  window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'CONTEXT_RESPONSE') {
      currentContext = event.data.context;
      console.log("[Tutor] Context extracted successfully:", currentContext);
      document.getElementById('problem-title-display').innerText = currentContext.problem_title;
      appendSystemMessage(`Synced context: **${currentContext.problem_title}** (${currentContext.language}). Ready for analysis!`);
    }
  });

  // Analyze student's current code
  analyzeBtn.addEventListener('click', () => {
    console.log("[Tutor DEBUG] ANALYZE CLICKED");
    console.log("[Tutor] Analyze Code clicked.");
    if (!currentContext) {
      appendSystemMessage("⚠️ Please click **Sync** first to capture your LeetCode code!");
      return;
    }
    // Pull fresh code block from Monaco prior to analysis
    console.log("[Tutor] Requesting fresh code sync prior to analysis...");
    window.parent.postMessage({ type: 'GET_CONTEXT' }, '*');
    
    // Slight timeout to let context update
    setTimeout(() => {
      // Set level to 0 as this is a fresh attempt submission
      tutorState.hint_level = 0;
      console.log("[Tutor] Sending code analysis request to backend...");
      sendCodeAnalysisRequest();
    }, 300);
  });

  // Ask for progressive hint escalations
  hintBtn.addEventListener('click', () => {
    console.log("[Tutor DEBUG] NEXT HINT CLICKED");
    if (!currentContext) return;
    tutorState.hint_level += 1;
    console.log(`[Tutor] Next Hint clicked. Escalating hint level to: ${tutorState.hint_level}`);
    sendCodeAnalysisRequest();
  });

  // Send textual response (General chat or teach back answers)
  sendBtn.addEventListener('click', handleChatSubmit);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChatSubmit();
    }
  });

  // Reset demo databases
  resetBtn.addEventListener('click', () => {
    if (confirm("Reset tutor history and learner mastery scores?")) {
      resetTutorSession();
    }
  });
}

// 3. API Communication
async function sendCodeAnalysisRequest() {
  if (isWaiting) return;
  setLoadingState(true);
  
  appendSystemMessage("Analyzing your solution correctness and patterns...");

  const payload = {
    ...currentContext,
    tutor_state: tutorState
  };

  try {
    console.log(`[Tutor] Sending POST request to ${API_BASE}/api/analyze with payload size: ${JSON.stringify(payload).length} bytes`);
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    console.log(`[Tutor] Received response status: ${res.status} ${res.statusText}`);
    if (!res.ok) throw new Error(`API Server error (status: ${res.status})`);
    
    const data = await res.json();
    console.log("[Tutor] Successfully parsed JSON response data:", data);
    
    // Update active state
    tutorState = data.tutor_state;
    
    // Display response
    appendMessage("assistant", data.tutor_response);
    
    // Update complexity highlights and meters
    updateComplexityViews(data.analysis);
    
    // Update learner profile
    updateProfileViews(data.profile, data.recommendation);
    
    // Update tutoring controls panel (progressive hints, optimization tag)
    updateTutorControlsPanel();
    
  } catch (err) {
    console.error("[Tutor] Code analysis fetch request failed:", err);
    appendMessage("assistant", `❌ Failed to communicate with Antigravity server. Verify the FastAPI backend is running on \`http://localhost:8000\`.\n\nError details: \`${err.message}\``);
  } finally {
    setLoadingState(false);
  }
}

async function handleChatSubmit() {
  const inputEl = document.getElementById('chat-input');
  const answer = inputEl.value.trim();
  if (!answer || isWaiting) return;

  console.log("[Tutor DEBUG] SEND CLICKED");
  inputEl.value = "";
  appendMessage("user", answer);
  console.log("[Tutor] User submitted text message:", answer);

  // If in teach back mode, hit the evaluation endpoint
  if (tutorState.mode === "teach_back") {
    console.log("[Tutor] In teach_back mode. Sending user explanation answer to backend...");
    setLoadingState(true);
    try {
      console.log(`[Tutor] Sending POST request to ${API_BASE}/api/teach-back`);
      const res = await fetch(`${API_BASE}/api/teach-back`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_answer: answer })
      });
      
      console.log(`[Tutor] Received response status: ${res.status} ${res.statusText}`);
      if (!res.ok) throw new Error(`Evaluation error (status: ${res.status})`);
      
      const data = await res.json();
      console.log("[Tutor] Successfully parsed JSON response data:", data);
      appendMessage("assistant", data.feedback);
      
      // Update mastery and recommendation
      updateProfileViews(data.profile, data.recommendation);
      
      // Clear teach back tags once completed
      tutorState.mode = "congratulate";
      updateTutorControlsPanel();
      
    } catch (err) {
      appendMessage("assistant", `❌ Evaluation failed: ${err.message}`);
    } finally {
      setLoadingState(false);
    }
  } else {
    // Treat as general chat. Fetch backend API.
    setLoadingState(true);
    try {
      const payload = {
        message: answer,
        problem_title: currentContext ? currentContext.problem_title : "Two Sum",
        code: currentContext ? currentContext.code : "",
        language: currentContext ? currentContext.language : "python",
        tutor_state: tutorState,
        conversation_history: conversationHistory
      };
      
      console.log(`[Tutor] Sending POST request to ${API_BASE}/api/chat`);
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      console.log(`[Tutor] Received response status: ${res.status} ${res.statusText}`);
      if (!res.ok) throw new Error(`Chat error (status: ${res.status})`);
      
      const data = await res.json();
      console.log("[Tutor] Successfully parsed JSON response data:", data);
      
      appendMessage("assistant", data.response);
      tutorState = data.tutor_state;
      updateTutorControlsPanel();
      
    } catch (err) {
      console.error("[Tutor] Chat fetch request failed:", err);
      appendMessage("assistant", `❌ Failed to communicate with Antigravity server. Verify the FastAPI backend is running on \`http://localhost:8000\`.\n\nError details: \`${err.message}\``);
    } finally {
      setLoadingState(false);
    }
  }
}

async function loadInitialProfile() {
  try {
    const res = await fetch(`${API_BASE}/api/profile`);
    if (res.ok) {
      const data = await res.json();
      updateProfileViews(data.profile, data.recommendation);
    }
  } catch (e) {
    console.warn("Could not load initial profile from backend", e);
  }
}

async function resetTutorSession() {
  try {
    const res = await fetch(`${API_BASE}/api/reset`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      // Clear chat
      const messagesContainer = document.getElementById('chat-messages');
      messagesContainer.innerHTML = "";
      
      tutorState = { mode: "debug", hint_level: 0 };
      currentContext = null;
      conversationHistory = [];
      document.getElementById('problem-title-display').innerText = "No context synced";
      
      appendMessage("assistant", "Database and learning profiles reset! I am ready to sync a new problem.");
      updateProfileViews(data.profile, null);
      updateComplexityViews(null);
      updateTutorControlsPanel();
    }
  } catch (e) {
    alert("Reset failed: " + e.message);
  }
}

// 4. View Rendering Helpers
function appendMessage(role, content) {
  const container = document.getElementById('chat-messages');
  
  const msgEl = document.createElement('div');
  msgEl.className = `msg ${role === 'user' ? 'user-msg' : 'assistant-msg'}`;
  
  const avatar = role === 'user' ? 'U' : 'A';
  
  // Guard against null/undefined content
  content = content || "";
  
  // Track in conversation history
  conversationHistory.push({ role: role, content: content });
  if (conversationHistory.length > 20) {
    conversationHistory.shift();
  }
  
  // Format content as Markdown paragraphs & bold text
  let formattedContent = content
    .replace(/\n\n/g, "</p><p>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\`(.*?)\`/g, "<code>$1</code>")
    .replace(/\$(.*?)\$/g, "<em>$1</em>"); // Basic LaTeX display
    
  msgEl.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-bubble">
      <p>${formattedContent}</p>
    </div>
  `;
  
  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function appendSystemMessage(text) {
  const container = document.getElementById('chat-messages');
  const sysEl = document.createElement('div');
  sysEl.style.fontSize = "11px";
  sysEl.style.color = "var(--text-secondary)";
  sysEl.style.textAlign = "center";
  sysEl.style.margin = "8px 0";
  sysEl.style.animation = "messageSlideUp 0.3s ease";
  sysEl.innerHTML = text;
  
  container.appendChild(sysEl);
  container.scrollTop = container.scrollHeight;
}

function setLoadingState(loading) {
  isWaiting = loading;
  const analyzeBtn = document.getElementById('analyze-btn');
  const syncBtn = document.getElementById('sync-btn');
  
  if (loading) {
    analyzeBtn.disabled = true;
    analyzeBtn.style.opacity = "0.6";
    syncBtn.disabled = true;
    
    // Add loading text bubble
    const container = document.getElementById('chat-messages');
    const loadEl = document.createElement('div');
    loadEl.id = "tutor-loading-bubble";
    loadEl.className = "msg assistant-msg";
    loadEl.innerHTML = `
      <div class="msg-avatar">A</div>
      <div class="msg-bubble" style="font-style: italic; color: var(--text-secondary);">
        Thinking...
      </div>
    `;
    container.appendChild(loadEl);
    container.scrollTop = container.scrollHeight;
  } else {
    analyzeBtn.disabled = false;
    analyzeBtn.style.opacity = "1";
    syncBtn.disabled = false;
    
    const loadEl = document.getElementById('tutor-loading-bubble');
    if (loadEl) loadEl.remove();
  }
}

function updateComplexityViews(analysis) {
  const bruteCard = document.getElementById('tier-brute');
  const betterCard = document.getElementById('tier-better');
  const optimalCard = document.getElementById('tier-optimal');
  
  // Remove glows
  bruteCard.style.boxShadow = "none";
  betterCard.style.boxShadow = "none";
  optimalCard.style.boxShadow = "none";
  
  if (!analysis || !analysis.complexity) return;
  
  const time = analysis.complexity.time;
  
  // Highlight the card representing current submission complexity
  if (time === "O(n^2)") {
    bruteCard.style.boxShadow = "0 0 15px rgba(244, 63, 94, 0.25)";
  } else if (time === "O(n log n)") {
    betterCard.style.boxShadow = "0 0 15px rgba(245, 158, 11, 0.25)";
  } else if (time === "O(n)") {
    optimalCard.style.boxShadow = "0 0 15px rgba(16, 185, 129, 0.25)";
  }
}

function updateProfileViews(profile, recommendation) {
  if (!profile) return;
  
  // Update progress figures
  for (const concept in profile) {
    const valEl = document.getElementById(`mastery-${concept}`);
    const fillEl = document.getElementById(`bar-${concept}`);
    if (valEl && fillEl) {
      const mastery = profile[concept];
      valEl.innerText = `${mastery}%`;
      fillEl.style.width = `${mastery}%`;
    }
  }
  
  // Update recommendation panel
  const recCard = document.getElementById('recommendation-card');
  if (recommendation && recommendation.recommended_concept) {
    recCard.classList.remove('hidden');
    document.getElementById('rec-concept').innerText = recommendation.recommended_concept;
    document.getElementById('rec-problem').innerText = recommendation.recommended_problem;
    document.getElementById('rec-explanation').innerText = recommendation.explanation;
  }
}

function updateTutorControlsPanel() {
  const panel = document.getElementById('tutor-controls');
  const modeTag = document.getElementById('tutor-mode-tag');
  const hintLevelEl = document.getElementById('hint-level-display');
  
  if (tutorState.mode === "optimize") {
    panel.classList.remove('hidden');
    modeTag.innerText = "Optimize";
    modeTag.style.color = "#fbbf24";
    modeTag.style.background = "rgba(245, 158, 11, 0.15)";
    
    const levels = ["", "Intro Hint", "Concept Direction", "Implementation Guidance", "Walkthrough Revealed"];
    const currentLvl = tutorState.hint_level;
    hintLevelEl.innerText = currentLvl > 0 ? `Level ${currentLvl}/4: ${levels[currentLvl]}` : "Optimize Request Ready";
  } else if (tutorState.mode === "teach_back") {
    panel.classList.add('hidden'); // Hide hint trigger since student must type their answer
  } else if (tutorState.mode === "debug") {
    panel.classList.remove('hidden');
    modeTag.innerText = "Debug";
    modeTag.style.color = "#f43f5e";
    modeTag.style.background = "rgba(244, 63, 94, 0.15)";
    hintLevelEl.innerText = "Diagnosis Ready";
  } else {
    panel.classList.add('hidden');
  }
}
