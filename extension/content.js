// Content script for scraping LeetCode and managing the sidebar iframe

let sidebarIframe = null;
let isSidebarOpen = false;

// 1. Create and Inject the Floating "AI Tutor" Button
function injectTutorButton() {
  if (document.getElementById('ai-tutor-trigger-btn')) return;

  const btn = document.createElement('div');
  btn.id = 'ai-tutor-trigger-btn';
  btn.innerHTML = `
    <div class="ai-btn-content">
      <svg class="ai-btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
        <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>AI Tutor</span>
    </div>
  `;
  
  // Style the floating button (sleek gradient, dark border, floating elevation)
  Object.assign(btn.style, {
    position: 'fixed',
    bottom: '30px',
    right: '30px',
    zIndex: '999999',
    background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
    color: '#ffffff',
    padding: '10px 18px',
    borderRadius: '30px',
    cursor: 'pointer',
    boxShadow: '0 10px 25px rgba(124, 58, 237, 0.4)',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    fontWeight: '600',
    fontSize: '14px',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    userSelect: 'none',
    border: '1px solid rgba(255, 255, 255, 0.1)'
  });

  // Hover and active states
  btn.addEventListener('mouseenter', () => {
    btn.style.transform = 'translateY(-3px) scale(1.03)';
    btn.style.boxShadow = '0 15px 30px rgba(124, 58, 237, 0.5)';
  });
  btn.addEventListener('mouseleave', () => {
    btn.style.transform = 'translateY(0) scale(1)';
    btn.style.boxShadow = '0 10px 25px rgba(124, 58, 237, 0.4)';
  });

  btn.addEventListener('click', toggleSidebar);
  document.body.appendChild(btn);
}

// 2. Create and Toggle the Sidebar Drawer
function toggleSidebar() {
  if (isSidebarOpen) {
    closeSidebar();
  } else {
    openSidebar();
  }
}

function openSidebar() {
  if (!sidebarIframe) {
    sidebarIframe = document.createElement('iframe');
    sidebarIframe.id = 'ai-tutor-sidebar-iframe';
    sidebarIframe.src = chrome.runtime.getURL('sidebar.html');
    
    // Style the iframe (frosted glass transition, side alignment)
    Object.assign(sidebarIframe.style, {
      position: 'fixed',
      top: '0',
      right: '0',
      width: '450px',
      height: '100vh',
      border: 'none',
      zIndex: '999998',
      boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.3)',
      transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
      transform: 'translateX(100%)',
      backgroundColor: 'transparent'
    });
    
    document.body.appendChild(sidebarIframe);
  }
  
  // Trigger slide-in
  setTimeout(() => {
    sidebarIframe.style.transform = 'translateX(0)';
  }, 50);
  
  isSidebarOpen = true;
  
  // Shift the floating button leftwards to not overlap with sidebar
  const btn = document.getElementById('ai-tutor-trigger-btn');
  if (btn) {
    btn.style.right = '475px';
    btn.style.background = '#1f2937'; // Change to solid dark as a toggle-close button
    btn.innerHTML = `
      <div class="ai-btn-content">
        <span>Close Tutor</span>
      </div>
    `;
  }
}

function closeSidebar() {
  if (sidebarIframe) {
    sidebarIframe.style.transform = 'translateX(100%)';
  }
  isSidebarOpen = false;
  
  const btn = document.getElementById('ai-tutor-trigger-btn');
  if (btn) {
    btn.style.right = '30px';
    btn.style.background = 'linear-gradient(135deg, #4f46e5, #7c3aed)';
    btn.innerHTML = `
      <div class="ai-btn-content">
        <svg class="ai-btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
          <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>AI Tutor</span>
      </div>
    `;
  }
}

// Helper: Custom CSS inject
const style = document.createElement('style');
style.textContent = `
  .ai-btn-content {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .ai-btn-icon {
    width: 18px;
    height: 18px;
  }
`;
document.head.appendChild(style);

// 3. Scraping Utilities for LeetCode DOM
function scrapeProblemDetails() {
  // Title scraping
  let title = "Two Sum"; // Default fallback
  const titleEl = document.querySelector('div[class*="text-title-large"] h4') || 
                  document.querySelector('.text-title-large') || 
                  document.querySelector('[data-cy="question-title"]');
  if (titleEl) {
    title = titleEl.innerText.replace(/^\d+\.\s*/, "").trim();
  }

  // Description scraping
  let description = "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.";
  const descEl = document.querySelector('div[class*="description_content"]') || 
                 document.querySelector('.elfjS') || 
                 document.querySelector('[data-track-load="description_content"]');
  if (descEl) {
    description = descEl.innerText.trim();
  }

  // Constraints scraping
  const constraints = [];
  if (descEl) {
    const listItems = descEl.querySelectorAll('ul li, ol li');
    listItems.forEach(item => {
      // Typically constraints are after the description keywords
      if (item.innerText.includes('<=') || item.innerText.includes('target') || item.innerText.includes('length')) {
        constraints.push(item.innerText.trim());
      }
    });
  }
  if (constraints.length === 0) {
    // Standard Two Sum fallback constraints
    constraints.push("2 <= nums.length <= 10^4");
    constraints.push("-10^9 <= nums[i] <= 10^9");
    constraints.push("-10^9 <= target <= 10^9");
  }

  // Code extraction from Monaco
  let code = "";
  const monacoLines = document.querySelectorAll('.monaco-editor .view-line');
  if (monacoLines.length > 0) {
    code = Array.from(monacoLines).map(line => line.innerText).join('\n');
  } else {
    const textarea = document.querySelector('.monaco-editor textarea');
    if (textarea) {
      code = textarea.value;
    }
  }

  // Normalize non-breaking spaces (\u00a0) and carriage returns to prevent compile/syntax errors
  if (code) {
    code = code.replace(/\u00a0/g, ' ').replace(/\r/g, '');
  }

  // Language extraction
  let language = "python3";
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    const text = btn.innerText.trim().toLowerCase();
    if (['c++', 'java', 'python3', 'python', 'javascript', 'typescript', 'go', 'rust', 'c#'].includes(text)) {
      language = text;
      break;
    }
  }

  return {
    problem_title: title,
    problem_description: description,
    constraints: constraints,
    examples: [],
    code: code,
    language: language
  };
}

// 4. Communication Interface between content.js and sidebar iframe
window.addEventListener('message', (event) => {
  // Verify message origin matches this extension
  if (!event.data || typeof event.data !== 'object') return;

  const type = event.data.type;
  
  if (type === 'GET_CONTEXT') {
    const context = scrapeProblemDetails();
    // Send captured context back to iframe
    if (sidebarIframe && sidebarIframe.contentWindow) {
      sidebarIframe.contentWindow.postMessage({
        type: 'CONTEXT_RESPONSE',
        context: context
      }, '*');
    }
  } else if (type === 'CLOSE_SIDEBAR') {
    closeSidebar();
  }
});

// Auto-initialize when DOM settles
setTimeout(injectTutorButton, 2000);

// Re-inject on navigation changes (SPA support)
let lastUrl = location.href;
new MutationObserver(() => {
  const url = location.href;
  if (url !== lastUrl) {
    lastUrl = url;
    setTimeout(injectTutorButton, 1500);
  }
}).observe(document, { subtree: true, childList: true });
