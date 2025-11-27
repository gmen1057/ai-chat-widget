/**
 * AI Chat Widget - Universal chatbot for any website
 *
 * Usage (just one line!):
 * <script src="https://your-server.com/widget/widget.js" data-api="https://your-server.com/widget-api"></script>
 */

(function () {
  "use strict";

  // ============================================
  // CONFIGURATION
  // ============================================

  const globalConfig = window.AI_CHAT_CONFIG || {};
  let script = document.currentScript;

  // Find script by src if currentScript is null (dynamic loading)
  if (!script) {
    const scripts = document.querySelectorAll('script[src*="widget.js"]');
    script = scripts[scripts.length - 1];
  }

  const getAttr = (name, defaultVal) => {
    if (globalConfig[name]) return globalConfig[name];
    if (script && script.getAttribute("data-" + name)) return script.getAttribute("data-" + name);
    return defaultVal;
  };

  const API_URL = getAttr("api", "");
  const THEME = getAttr("theme", "light");
  const POSITION = getAttr("position", "bottom-right");
  const TITLE = getAttr("title", "AI Assistant");
  const GREETING = getAttr("greeting", "Привет! 👋 Чем могу помочь?");

  // Page filtering (include/exclude)
  // Use data-include="/path1,/path2" or data-exclude="/admin,/checkout"
  // Supports wildcards: /blog/* matches /blog/post-1, /blog/post-2
  const INCLUDE_PAGES = getAttr("include", "");  // Empty = all pages
  const EXCLUDE_PAGES = getAttr("exclude", "");  // Pages to hide widget

  // Privacy settings
  // data-private="/login,/account/*,/checkout" - pages where NO context is sent (only URL)
  // data-no-content="/admin/*" - pages where content is hidden but URL/title sent
  const PRIVATE_PAGES = getAttr("private", "");     // No context at all (max privacy)
  const NO_CONTENT_PAGES = getAttr("no-content", ""); // URL+title only, no page content

  function matchesPattern(path, pattern) {
    // Convert wildcard pattern to regex
    const regex = new RegExp("^" + pattern.replace(/\*/g, ".*") + "$");
    return regex.test(path);
  }

  function shouldShowWidget() {
    const path = window.location.pathname;

    // Check exclude list first
    if (EXCLUDE_PAGES) {
      const excludeList = EXCLUDE_PAGES.split(",").map(p => p.trim());
      for (const pattern of excludeList) {
        if (matchesPattern(path, pattern)) {
          console.log("AI Chat Widget: hidden on excluded page", path);
          return false;
        }
      }
    }

    // If include list specified, path must match
    if (INCLUDE_PAGES) {
      const includeList = INCLUDE_PAGES.split(",").map(p => p.trim());
      for (const pattern of includeList) {
        if (matchesPattern(path, pattern)) {
          return true;
        }
      }
      console.log("AI Chat Widget: hidden - page not in include list", path);
      return false;
    }

    return true;  // Show by default
  }

  // Privacy level: "full" (all context), "limited" (url+title), "private" (url only)
  function getPrivacyLevel() {
    const path = window.location.pathname;

    // Check private pages (maximum privacy - only URL)
    if (PRIVATE_PAGES) {
      const privateList = PRIVATE_PAGES.split(",").map(p => p.trim());
      for (const pattern of privateList) {
        if (matchesPattern(path, pattern)) {
          return "private";
        }
      }
    }

    // Check no-content pages (URL + title only)
    if (NO_CONTENT_PAGES) {
      const noContentList = NO_CONTENT_PAGES.split(",").map(p => p.trim());
      for (const pattern of noContentList) {
        if (matchesPattern(path, pattern)) {
          return "limited";
        }
      }
    }

    return "full";  // Full context by default
  }

  // ============================================
  // EMBEDDED CSS (no external file needed!)
  // ============================================

  const CSS = `
    .ai-chat-widget {
      position: fixed;
      z-index: 99999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    .ai-chat-widget.bottom-right { bottom: 20px; right: 20px; }
    .ai-chat-widget.bottom-left { bottom: 20px; left: 20px; }
    .ai-chat-widget.top-right { top: 20px; right: 20px; }
    .ai-chat-widget.top-left { top: 20px; left: 20px; }

    .ai-chat-toggle {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      border: none;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .ai-chat-toggle:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }

    .ai-chat-window {
      position: absolute;
      bottom: 70px;
      right: 0;
      width: 380px;
      height: 500px;
      max-height: 70vh;
      background: white;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .ai-chat-widget.bottom-left .ai-chat-window { right: auto; left: 0; }
    .ai-chat-widget.top-right .ai-chat-window { bottom: auto; top: 70px; }
    .ai-chat-widget.top-left .ai-chat-window { bottom: auto; top: 70px; right: auto; left: 0; }

    .ai-chat-widget.dark .ai-chat-window {
      background: #1e1e1e;
      color: #e0e0e0;
    }

    .ai-chat-header {
      padding: 16px 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }
    .ai-chat-header h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
    .ai-chat-close {
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      padding: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
      transition: background 0.2s;
    }
    .ai-chat-close:hover {
      background: rgba(255, 255, 255, 0.2);
    }

    .ai-chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .ai-chat-message {
      display: flex;
      max-width: 85%;
    }
    .ai-chat-message.user { align-self: flex-end; }
    .ai-chat-message.assistant { align-self: flex-start; }
    .ai-chat-message-content {
      padding: 10px 14px;
      border-radius: 12px;
      line-height: 1.4;
      font-size: 14px;
      word-wrap: break-word;
    }
    .ai-chat-message.user .ai-chat-message-content {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-bottom-right-radius: 4px;
    }
    .ai-chat-message.assistant .ai-chat-message-content {
      background: #f0f0f0;
      color: #333;
      border-bottom-left-radius: 4px;
    }
    .ai-chat-widget.dark .ai-chat-message.assistant .ai-chat-message-content {
      background: #2a2a2a;
      color: #e0e0e0;
    }
    .ai-chat-widget.dark .ai-chat-message.assistant pre,
    .ai-chat-widget.dark .ai-chat-message.assistant code {
      background: #1a1a1a;
    }

    .ai-chat-typing {
      display: flex;
      gap: 4px;
      padding: 10px 14px;
      background: #f0f0f0;
      border-radius: 12px;
      border-bottom-left-radius: 4px;
      align-self: flex-start;
    }
    .ai-chat-typing span {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #999;
      animation: ai-typing 1.4s infinite;
    }
    .ai-chat-typing span:nth-child(2) { animation-delay: 0.2s; }
    .ai-chat-typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes ai-typing {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
      30% { transform: translateY(-8px); opacity: 1; }
    }

    .ai-chat-input-container {
      padding: 12px;
      border-top: 1px solid #e0e0e0;
      display: flex;
      gap: 10px;
      align-items: flex-end;
      flex-shrink: 0;
    }
    .ai-chat-widget.dark .ai-chat-input-container { border-top-color: #333; }
    .ai-chat-input {
      flex: 1;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 14px;
      resize: none;
      max-height: 100px;
      font-family: inherit;
      transition: border-color 0.2s;
      background: #fff;
      color: #333;
    }
    .ai-chat-input::placeholder {
      color: #888;
      opacity: 1;
    }
    .ai-chat-input:focus {
      outline: none;
      border-color: #667eea;
    }
    .ai-chat-widget.dark .ai-chat-input {
      background: #2a2a2a;
      border-color: #333;
      color: #e0e0e0;
    }
    .ai-chat-send {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      border: none;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s;
      flex-shrink: 0;
    }
    .ai-chat-send:hover { transform: scale(1.05); }
    .ai-chat-send:active { transform: scale(0.95); }

    .ai-chat-messages::-webkit-scrollbar { width: 6px; }
    .ai-chat-messages::-webkit-scrollbar-track { background: transparent; }
    .ai-chat-messages::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }

    @media (max-width: 480px) {
      .ai-chat-window {
        width: calc(100vw - 40px);
        height: 60vh;
        right: 0;
        left: 0;
        margin: 0 auto;
      }
    }
  `;

  // ============================================
  // SESSION & PAGE CONTEXT
  // ============================================

  let sessionId = localStorage.getItem("ai_chat_session_id");
  if (!sessionId) {
    sessionId = "s_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
    localStorage.setItem("ai_chat_session_id", sessionId);
  }

  // ============================================
  // CHAT HISTORY PERSISTENCE
  // ============================================

  const HISTORY_KEY = "ai_chat_history_" + sessionId;

  function saveHistory(messagesArray) {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(messagesArray));
    } catch (e) {
      console.warn("AI Chat: Could not save history", e);
    }
  }

  function loadHistory() {
    try {
      const data = localStorage.getItem(HISTORY_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.warn("AI Chat: Could not load history", e);
      return [];
    }
  }

  function clearHistory() {
    localStorage.removeItem(HISTORY_KEY);
  }

  function getPageContext() {
    const privacyLevel = getPrivacyLevel();

    // Private mode: only URL (no title, no content)
    if (privacyLevel === "private") {
      return {
        url: window.location.origin + window.location.pathname, // Hide query params too
        title: "[Приватная страница]",
        meta_description: "",
        headings: { h1: [], h2: [] },
        selected_text: "",
      };
    }

    // Limited mode: URL + title only
    if (privacyLevel === "limited") {
      return {
        url: window.location.href,
        title: document.title,
        meta_description: "",
        headings: { h1: [], h2: [] },
        selected_text: "",
      };
    }

    // Full mode: all context
    return {
      url: window.location.href,
      title: document.title,
      meta_description: document.querySelector('meta[name="description"]')?.content || "",
      headings: {
        h1: Array.from(document.querySelectorAll("h1")).map(h => h.innerText.trim()).filter(t => t).slice(0, 3),
        h2: Array.from(document.querySelectorAll("h2")).map(h => h.innerText.trim()).filter(t => t).slice(0, 5),
      },
      selected_text: window.getSelection()?.toString() || "",
    };
  }

  // ============================================
  // WIDGET HTML
  // ============================================

  const widgetHTML = `
    <div id="ai-chat-widget" class="ai-chat-widget ${THEME} ${POSITION}">
      <button id="ai-chat-toggle" class="ai-chat-toggle" aria-label="Open chat">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>
      <div id="ai-chat-window" class="ai-chat-window" style="display: none;">
        <div class="ai-chat-header">
          <h3>${TITLE}</h3>
          <button id="ai-chat-close" class="ai-chat-close" aria-label="Close chat">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div id="ai-chat-messages" class="ai-chat-messages">
          <div class="ai-chat-message assistant">
            <div class="ai-chat-message-content">${GREETING}</div>
          </div>
        </div>
        <div class="ai-chat-input-container">
          <textarea id="ai-chat-input" class="ai-chat-input" placeholder="Напишите сообщение..." rows="1"></textarea>
          <button id="ai-chat-send" class="ai-chat-send" aria-label="Send message">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>
  `;

  // ============================================
  // INITIALIZATION
  // ============================================

  function initWidget() {
    // Check page filtering
    if (!shouldShowWidget()) return;

    // Prevent double init
    if (document.getElementById("ai-chat-widget")) return;

    // Inject CSS
    const style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);

    // Inject HTML
    const container = document.createElement("div");
    container.innerHTML = widgetHTML;
    document.body.appendChild(container.firstElementChild);

    // Get elements
    const widget = document.getElementById("ai-chat-widget");
    const toggle = document.getElementById("ai-chat-toggle");
    const closeBtn = document.getElementById("ai-chat-close");
    const chatWindow = document.getElementById("ai-chat-window");
    const messages = document.getElementById("ai-chat-messages");
    const input = document.getElementById("ai-chat-input");
    const sendBtn = document.getElementById("ai-chat-send");

    // Toggle chat
    toggle.onclick = () => {
      chatWindow.style.display = chatWindow.style.display === "none" ? "flex" : "none";
      if (chatWindow.style.display === "flex") input.focus();
    };
    closeBtn.onclick = () => { chatWindow.style.display = "none"; };

    // Chat history array
    let chatMessages = [];

    // Load existing history and render
    function loadAndRenderHistory() {
      chatMessages = loadHistory();
      if (chatMessages.length > 0) {
        // Clear default greeting
        messages.innerHTML = "";
        // Render all messages
        chatMessages.forEach(msg => {
          renderMessage(msg.role, msg.text);
        });
      }
    }

    // Render message to DOM (without saving)
    function renderMessage(role, text) {
      const msg = document.createElement("div");
      msg.className = "ai-chat-message " + role;
      // Use markdown for assistant, plain text for user (security)
      const content = role === "assistant" ? parseMarkdown(text) : escapeHtml(text);
      msg.innerHTML = '<div class="ai-chat-message-content">' + content + "</div>";
      messages.appendChild(msg);
      messages.scrollTop = messages.scrollHeight;
    }

    // Add message to chat (save to history)
    function addMessage(role, text) {
      chatMessages.push({ role, text, timestamp: Date.now() });
      saveHistory(chatMessages);
      renderMessage(role, text);
    }

    // Load history on init
    loadAndRenderHistory();

    function escapeHtml(text) {
      const div = document.createElement("div");
      div.textContent = text;
      return div.innerHTML;
    }

    // Simple Markdown parser (no external dependencies)
    function parseMarkdown(text) {
      // First escape HTML
      let html = escapeHtml(text);

      // Code blocks ```code```
      html = html.replace(/```([\s\S]*?)```/g, '<pre style="background:#f4f4f4;padding:8px;border-radius:4px;overflow-x:auto;font-size:13px;">$1</pre>');

      // Inline code `code`
      html = html.replace(/`([^`]+)`/g, '<code style="background:#f4f4f4;padding:2px 5px;border-radius:3px;font-size:13px;">$1</code>');

      // Bold **text** or __text__
      html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

      // Italic *text* or _text_
      html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
      html = html.replace(/_(.+?)_/g, '<em>$1</em>');

      // Links [text](url)
      html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" style="color:#667eea;">$1</a>');

      // Lists (- item or * item)
      html = html.replace(/^[\-\*] (.+)$/gm, '• $1');

      // Line breaks
      html = html.replace(/\n/g, '<br>');

      return html;
    }

    // Typing indicator
    let typingEl = null;
    function showTyping() {
      typingEl = document.createElement("div");
      typingEl.className = "ai-chat-typing";
      typingEl.innerHTML = "<span></span><span></span><span></span>";
      messages.appendChild(typingEl);
      messages.scrollTop = messages.scrollHeight;
    }
    function hideTyping() {
      if (typingEl) { typingEl.remove(); typingEl = null; }
    }

    // Send message
    async function sendMessage() {
      const text = input.value.trim();
      if (!text) return;

      addMessage("user", text);
      input.value = "";
      input.style.height = "auto";
      showTyping();

      try {
        const response = await fetch(API_URL + "/chat/message", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            message: text,
            page_context: getPageContext(),
          }),
        });

        hideTyping();

        if (!response.ok) throw new Error("HTTP " + response.status);

        const data = await response.json();
        addMessage("assistant", data.reply);
      } catch (err) {
        hideTyping();
        console.error("AI Chat Widget error:", err);
        addMessage("assistant", "Извините, произошла ошибка. Попробуйте позже.");
      }
    }

    sendBtn.onclick = sendMessage;
    input.onkeydown = (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    };

    // Auto-resize textarea
    input.oninput = () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 100) + "px";
    };

    console.log("AI Chat Widget loaded. API:", API_URL);
  }

  // Run init when DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWidget);
  } else {
    initWidget();
  }

})();
