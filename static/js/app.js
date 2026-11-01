/**
 * PlanGenius AI - Main Application Controller
 */

const App = {
  allEvents: [],
  currentEvent: null,
  activeTab: "ideas",

  async init() {
    this.bindEvents();
    this.loadSettings();
    await this.loadEvents();
  },

  bindEvents() {
    // Tab switching
    document.querySelectorAll(".tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        this.switchTab(tab);
      });
    });

    // Event switcher select
    const select = document.getElementById("event-switcher");
    if (select) {
      select.addEventListener("change", (e) => {
        this.selectEvent(e.target.value);
      });
    }

    // Copilot input enter key
    const copilotInput = document.getElementById("copilot-input");
    if (copilotInput) {
      copilotInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") Copilot.sendMessage();
      });
    }
  },

  async loadEvents(selectEventId = null) {
    try {
      this.allEvents = await API.listEvents();
      this.populateEventSelector(selectEventId);

      const targetId = selectEventId || (this.allEvents[0] ? this.allEvents[0].id : null);
      if (targetId) {
        await this.selectEvent(targetId);
      }
    } catch (err) {
      showToast("Error loading events: " + err.message, "error");
    }
  },

  populateEventSelector(selectedId = null) {
    const select = document.getElementById("event-switcher");
    if (!select) return;

    select.innerHTML = this.allEvents.map(e => `
      <option value="${e.id}" ${e.id === selectedId ? 'selected' : ''}>
        ${this.getTypeEmoji(e.eventType)} ${e.title}
      </option>
    `).join("");
  },

  getTypeEmoji(type) {
    if (type === "wedding") return "💍";
    if (type === "birthday") return "🎂";
    return "🏛️";
  },

  async selectEvent(id) {
    try {
      this.currentEvent = await API.getEvent(id);
      const select = document.getElementById("event-switcher");
      if (select) select.value = id;
      this.renderCurrentEvent();
    } catch (err) {
      showToast("Failed to load event: " + err.message, "error");
    }
  },

  renderCurrentEvent() {
    if (!this.currentEvent) return;

    // Hero title & metadata
    document.getElementById("hero-title").innerText = this.currentEvent.title;
    document.getElementById("hero-type-badge").innerText = this.currentEvent.eventType.toUpperCase();
    document.getElementById("hero-type-badge").className = `badge-type badge-${this.currentEvent.eventType}`;
    document.getElementById("hero-subtype-badge").innerText = this.currentEvent.subType || "Celebration";
    document.getElementById("hero-date").innerText = this.currentEvent.date || "Date TBD";
    document.getElementById("hero-location").innerText = this.currentEvent.location || "Location TBD";
    document.getElementById("hero-guests").innerText = `${this.currentEvent.guestCount || 0} Guests`;

    // Countdown calculation
    this.updateCountdown(this.currentEvent.date);

    // KPI Summary
    const curr = this.currentEvent.currency || "$";
    const totalBudget = Number(this.currentEvent.totalBudget) || 0;
    const items = this.currentEvent.budgetItems || [];
    const spent = items.reduce((acc, it) => acc + (Number(it.actual) || 0), 0);
    const budgetPct = totalBudget ? Math.min(100, Math.round((spent / totalBudget) * 100)) : 0;

    document.getElementById("kpi-budget-value").innerText = `${curr}${spent.toLocaleString()} / ${curr}${totalBudget.toLocaleString()}`;
    document.getElementById("kpi-budget-progress").style.width = `${budgetPct}%`;

    // Milestones KPI
    const milestones = this.currentEvent.timelineMilestones || [];
    const completedM = milestones.filter(m => m.completed).length;
    const milePct = milestones.length ? Math.round((completedM / milestones.length) * 100) : 0;
    document.getElementById("kpi-milestones-value").innerText = `${completedM} / ${milestones.length} Done`;
    document.getElementById("kpi-milestones-progress").style.width = `${milePct}%`;

    // Vendors KPI
    const vendors = this.currentEvent.vendors || [];
    const bookedV = vendors.filter(v => v.status === "booked" || v.status === "deposit_paid" || v.status === "completed").length;
    const vendorPct = vendors.length ? Math.round((bookedV / vendors.length) * 100) : 0;
    document.getElementById("kpi-vendors-value").innerText = `${bookedV} / ${vendors.length} Booked`;
    document.getElementById("kpi-vendors-progress").style.width = `${vendorPct}%`;

    // Render active tab content
    this.renderActiveTab();
  },

  updateCountdown(dateStr) {
    const el = document.getElementById("hero-countdown");
    if (!el) return;

    if (!dateStr) {
      el.innerText = "Date TBD";
      return;
    }

    try {
      const target = new Date(dateStr + "T00:00:00");
      const now = new Date();
      const diffTime = target - now;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays > 0) {
        el.innerText = `⏳ ${diffDays} Days to Go!`;
      } else if (diffDays === 0) {
        el.innerText = `🎉 Today is the Big Day!`;
      } else {
        el.innerText = `✨ Celebrated (${Math.abs(diffDays)}d ago)`;
      }
    } catch {
      el.innerText = dateStr;
    }
  },

  switchTab(tabName) {
    this.activeTab = tabName;
    document.querySelectorAll(".tab-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });
    document.querySelectorAll(".tab-panel").forEach(panel => {
      panel.classList.toggle("active", panel.id === `tab-${tabName}`);
    });
    this.renderActiveTab();
  },

  renderActiveTab() {
    if (!this.currentEvent) return;

    switch (this.activeTab) {
      case "ideas":
        IdeasComponent.render(this.currentEvent);
        break;
      case "budget":
        BudgetComponent.render(this.currentEvent);
        break;
      case "timeline":
        TimelineComponent.render(this.currentEvent);
        break;
      case "vendors":
        VendorsComponent.render(this.currentEvent);
        break;
      case "guests":
        GuestsComponent.render(this.currentEvent);
        break;
    }
  },

  async saveCurrentEvent(showToastAlert = false) {
    if (!this.currentEvent) return;
    try {
      this.currentEvent = await API.saveEvent(this.currentEvent);
      this.renderCurrentEvent();
      if (showToastAlert) showToast("Saved changes successfully", "success");
    } catch (err) {
      showToast("Error saving event: " + err.message, "error");
    }
  },

  openCopilotWithPrompt(promptText) {
    Copilot.sendQuickPrompt(promptText);
  },

  async deleteCurrentEvent() {
    if (!this.currentEvent) return;
    if (!confirm(`Are you sure you want to delete "${this.currentEvent.title}"?`)) return;

    try {
      await API.deleteEvent(this.currentEvent.id);
      showToast("Event deleted", "info");
      await this.loadEvents();
    } catch (err) {
      showToast("Error deleting: " + err.message, "error");
    }
  },

  async resetSamples() {
    if (!confirm("Reset all events back to the 4 default sample events? Any unsaved custom events will be replaced.")) return;
    try {
      this.allEvents = await API.resetSamples();
      this.populateEventSelector();
      if (this.allEvents[0]) {
        await this.selectEvent(this.allEvents[0].id);
      }
      showToast("Sample events restored!", "success");
    } catch (err) {
      showToast("Failed to reset: " + err.message, "error");
    }
  },

  exportJson() {
    if (!this.currentEvent) return;
    const str = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.currentEvent, null, 2));
    const a = document.createElement("a");
    a.setAttribute("href", str);
    a.setAttribute("download", `${this.currentEvent.title.replace(/\s+/g, '_')}_backup.json`);
    document.body.appendChild(a);
    a.click();
    a.remove();
    showToast("Event JSON exported", "success");
  },

  importJson(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const imported = JSON.parse(e.target.result);
        if (!imported.title) throw new Error("Invalid event JSON format");
        delete imported.id; // Allow new ID creation
        const saved = await API.saveEvent(imported);
        await this.loadEvents(saved.id);
        showToast("Event imported successfully!", "success");
      } catch (err) {
        showToast("Error importing JSON: " + err.message, "error");
      }
    };
    reader.readAsText(file);
  },

  printEvent() {
    window.print();
  },

  // Settings & Provider Configuration
  selectedProvider: "groq",

  selectProviderTab(provider) {
    this.selectedProvider = provider;
    ["groq", "gemini", "local"].forEach(p => {
      const btn = document.getElementById(`provider-btn-${p}`);
      const panel = document.getElementById(`panel-${p}-settings`);
      if (btn) btn.classList.toggle("active", p === provider);
      if (panel) panel.style.display = p === provider ? "block" : "none";
    });
  },

  loadSettings() {
    const provider = API.getProvider();
    this.selectedProvider = provider;
    this.selectProviderTab(provider);

    // Groq fields
    const groqKey = API.getGroqKey();
    const groqModel = API.getGroqModel();
    const groqInput = document.getElementById("settings-groq-key");
    const groqSelect = document.getElementById("settings-groq-model");
    if (groqInput) groqInput.value = groqKey;
    if (groqSelect) groqSelect.value = groqModel;

    // Gemini fields
    const geminiKey = API.getApiKey();
    const geminiModel = API.getModel();
    const geminiInput = document.getElementById("settings-api-key");
    const geminiSelect = document.getElementById("settings-model");
    if (geminiInput) geminiInput.value = geminiKey;
    if (geminiSelect) geminiSelect.value = geminiModel;

    // Update status badge
    const statusBadge = document.getElementById("gemini-status-indicator");
    if (statusBadge) {
      if (provider === "groq") {
        if (groqKey) {
          statusBadge.innerHTML = `<span style="color: #F97316; font-weight: 600;">⚡ Groq Connected (${groqModel})</span>`;
        } else {
          statusBadge.innerHTML = `<span style="color: #F97316;">⚡ Groq Selected (Key needed)</span>`;
        }
      } else if (provider === "gemini") {
        if (geminiKey) {
          statusBadge.innerHTML = `<span style="color: #34D399; font-weight: 600;">✨ Gemini Connected (${geminiModel})</span>`;
        } else {
          statusBadge.innerHTML = `<span style="color: #34D399;">✨ Gemini Selected (Key needed)</span>`;
        }
      } else {
        statusBadge.innerHTML = `<span style="color: #94A3B8;">💻 Built-in Local Engine (Free / Offline)</span>`;
      }
    }
  },

  openSettings() {
    this.loadSettings();
    document.getElementById("modal-settings")?.classList.add("active");
  },

  closeSettings() {
    document.getElementById("modal-settings")?.classList.remove("active");
  },

  saveSettings() {
    API.setProvider(this.selectedProvider);

    // Save Groq settings
    const groqKey = document.getElementById("settings-groq-key")?.value || "";
    const groqModel = document.getElementById("settings-groq-model")?.value || "qwen/qwen3.8-27b";
    API.setGroqKey(groqKey);
    API.setGroqModel(groqModel);

    // Save Gemini settings
    const geminiKey = document.getElementById("settings-api-key")?.value || "";
    const geminiModel = document.getElementById("settings-model")?.value || "gemini-2.5-flash";
    API.setApiKey(geminiKey);
    API.setModel(geminiModel);

    this.loadSettings();
    this.closeSettings();
    showToast(`AI Engine updated to ${this.selectedProvider.toUpperCase()}`, "success");
  },

  async testKey() {
    const key = document.getElementById("settings-api-key")?.value || "";
    const model = document.getElementById("settings-model")?.value || "gemini-2.5-flash";
    if (!key) {
      showToast("Please enter a Gemini API key to test", "error");
      return;
    }

    const testBtn = document.getElementById("btn-test-key");
    if (testBtn) testBtn.disabled = true;

    try {
      showToast("Testing connection with Gemini...", "info");
      const res = await API.testGeminiKey(key, model);
      if (res.success) {
        showToast("Connection Successful! " + res.message, "success");
      }
    } catch (err) {
      showToast("Gemini key test failed: " + err.message, "error");
    } finally {
      if (testBtn) testBtn.disabled = false;
    }
  },

  async testGroqKey() {
    const key = document.getElementById("settings-groq-key")?.value || "";
    const model = document.getElementById("settings-groq-model")?.value || "qwen/qwen3.8-27b";
    if (!key) {
      showToast("Please enter a Groq API key to test", "error");
      return;
    }

    const testBtn = document.getElementById("btn-test-groq-key");
    if (testBtn) testBtn.disabled = true;

    try {
      showToast("Testing connection with Groq Cloud...", "info");
      const res = await API.testGroqKey(key, model);
      if (res.success) {
        showToast("⚡ " + res.message, "success");
        // Dynamically update model options if list provided
        if (res.models && res.models.length) {
          const select = document.getElementById("settings-groq-model");
          if (select) {
            const current = select.value;
            select.innerHTML = res.models.map(m => `
              <option value="${m}" ${m === current || m === 'qwen/qwen3.8-27b' ? 'selected' : ''}>${m}</option>
            `).join("");
          }
        }
      }
    } catch (err) {
      showToast("Groq test failed: " + err.message, "error");
    } finally {
      if (testBtn) testBtn.disabled = false;
    }
  }
};

// Global Toast System
function showToast(msg, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  let icon = "💡";
  if (type === "success") icon = "✅";
  if (type === "error") icon = "⚠️";
  t.innerHTML = `<span>${icon}</span> <span>${msg}</span>`;
  container.appendChild(t);
  setTimeout(() => {
    t.style.opacity = "0";
    setTimeout(() => t.remove(), 300);
  }, 4000);
}

// Celebration particle trigger
function triggerCelebration() {
  // Simple CSS canvas / particle celebration
  const count = 30;
  for (let i = 0; i < count; i++) {
    const particle = document.createElement("div");
    particle.innerText = ["🎉", "✨", "💫", "🥂", "💖", "🌟"][Math.floor(Math.random() * 6)];
    particle.style.position = "fixed";
    particle.style.left = `${Math.random() * 90 + 5}vw`;
    particle.style.top = `${Math.random() * 30 + 10}vh`;
    particle.style.fontSize = `${Math.random() * 20 + 16}px`;
    particle.style.zIndex = "9999";
    particle.style.pointerEvents = "none";
    particle.style.transition = "all 1.5s cubic-bezier(0.25, 1, 0.5, 1)";
    document.body.appendChild(particle);

    setTimeout(() => {
      particle.style.transform = `translateY(${Math.random() * 200 - 100}px) scale(1.5)`;
      particle.style.opacity = "0";
      setTimeout(() => particle.remove(), 1500);
    }, 50);
  }
}

// Bootstrap on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
