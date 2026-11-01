/**
 * PlanGenius AI - Conversational Co-pilot Drawer Component
 */

const Copilot = {
  isOpen: false,
  messages: [
    {
      role: "ai",
      content: "Hello! I am your **PlanGenius AI Co-pilot**. I have the full context of your event budget, schedule, and vendor contracts. Ask me anything—from optimizing your budget to drafting vendor inquiries or crafting speeches!"
    }
  ],

  toggle() {
    this.isOpen ? this.close() : this.open();
  },

  open() {
    this.isOpen = true;
    const drawer = document.getElementById("copilot-drawer");
    if (drawer) drawer.classList.add("open");
    this.render();
  },

  close() {
    this.isOpen = false;
    const drawer = document.getElementById("copilot-drawer");
    if (drawer) drawer.classList.remove("open");
  },

  render() {
    const container = document.getElementById("copilot-messages");
    const titleEl = document.getElementById("copilot-event-name");
    if (!container) return;

    if (titleEl && App.currentEvent) {
      titleEl.innerText = App.currentEvent.title;
    }

    container.innerHTML = this.messages.map((m, idx) => `
      <div class="chat-msg ${m.role}">
        ${this.formatMarkdown(m.content)}
      </div>
    `).join("");

    container.scrollTop = container.scrollHeight;
  },

  formatMarkdown(text) {
    if (!text) return "";
    let html = text
      // Code blocks
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      // Bold
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italics
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Headers
      .replace(/^### (.*$)/gim, '<h4 style="font-size: 0.95rem; font-weight:700; color:#C7D2FE; margin: 0.4rem 0;">$1</h4>')
      .replace(/^## (.*$)/gim, '<h3 style="font-size: 1.05rem; font-weight:700; color:#C7D2FE; margin: 0.5rem 0;">$1</h3>')
      // Bullet points
      .replace(/^\s*•\s*(.*$)/gim, '<li>$1</li>')
      .replace(/^\s*-\s*(.*$)/gim, '<li>$1</li>')
      .replace(/^\s*\d+\.\s*(.*$)/gim, '<li>$1</li>')
      // Paragraph linebreaks
      .replace(/\n\n/g, '<br><br>');

    // Wrap list items if present
    if (html.includes('<li>')) {
      html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul style="padding-left: 1.25rem; margin: 0.4rem 0;">$1</ul>');
    }

    return html;
  },

  sendQuickPrompt(promptText) {
    this.open();
    const input = document.getElementById("copilot-input");
    if (input) input.value = promptText;
    this.sendMessage();
  },

  async sendMessage() {
    const input = document.getElementById("copilot-input");
    if (!input || !input.value.trim()) return;

    const userText = input.value.trim();
    input.value = "";

    this.messages.push({ role: "user", content: userText });
    this.render();

    // Placeholder AI message
    const aiPlaceholder = { role: "ai", content: "Thinking..." };
    this.messages.push(aiPlaceholder);
    this.render();

    try {
      const cleanedMessages = this.messages.slice(0, -1).map(m => ({
        role: (m.role === "ai" || m.role === "assistant") ? "assistant" : (m.role === "system" ? "system" : "user"),
        content: m.content
      }));
      const res = await API.chat(cleanedMessages, App.currentEvent);
      if (res.success && res.reply) {
        aiPlaceholder.content = res.reply;
      } else {
        aiPlaceholder.content = "Sorry, I couldn't process that query. Please try again.";
      }
    } catch (err) {
      aiPlaceholder.content = `⚠️ ${err.message}`;
    }

    this.render();
  }
};
