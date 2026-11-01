/**
 * PlanGenius AI - Backend API Client & Settings Storage
 * Supports Google Gemini, Groq API, and Local Built-in Engine
 */

const API = {
  // Provider: 'groq' | 'gemini' | 'local'
  getProvider() {
    return localStorage.getItem("plangenius_ai_provider") || "groq";
  },
  setProvider(provider) {
    localStorage.setItem("plangenius_ai_provider", provider);
  },

  // Gemini Key & Model
  getApiKey() {
    return localStorage.getItem("plangenius_gemini_key") || "";
  },
  setApiKey(key) {
    if (key) {
      localStorage.setItem("plangenius_gemini_key", key.trim());
    } else {
      localStorage.removeItem("plangenius_gemini_key");
    }
  },
  getModel() {
    return localStorage.getItem("plangenius_gemini_model") || "gemini-2.5-flash";
  },
  setModel(model) {
    localStorage.setItem("plangenius_gemini_model", model);
  },

  DEFAULT_GROQ_KEY: "",
  DEFAULT_GROQ_MODEL: "qwen/qwen3.8-27b",

  // Groq Key & Model
  getGroqKey() {
    return localStorage.getItem("plangenius_groq_key") || this.DEFAULT_GROQ_KEY;
  },
  setGroqKey(key) {
    if (key) {
      localStorage.setItem("plangenius_groq_key", key.trim());
    } else {
      localStorage.removeItem("plangenius_groq_key");
    }
  },
  getGroqModel() {
    return localStorage.getItem("plangenius_groq_model") || this.DEFAULT_GROQ_MODEL;
  },
  setGroqModel(model) {
    localStorage.setItem("plangenius_groq_model", model);
  },

  // Active Key and Model resolver
  getActiveCredentials() {
    let provider = this.getProvider();
    if (provider === "gemini" && !this.getApiKey()) {
      provider = "groq";
    }
    if (provider === "groq") {
      return {
        provider: "groq",
        apiKey: this.getGroqKey(),
        model: this.getGroqModel()
      };
    } else if (provider === "gemini") {
      return {
        provider: "gemini",
        apiKey: this.getApiKey(),
        model: this.getModel()
      };
    } else {
      return {
        provider: "local",
        apiKey: "",
        model: "local"
      };
    }
  },

  async request(endpoint, options = {}) {
    const res = await fetch(endpoint, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      },
      ...options
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || `HTTP error ${res.status}`);
    }
    return data;
  },

  async listEvents() {
    const data = await this.request("/api/events");
    return data.events || [];
  },

  async getEvent(id) {
    const data = await this.request(`/api/events/${id}`);
    return data.event;
  },

  async saveEvent(eventData) {
    const data = await this.request("/api/events", {
      method: "POST",
      body: JSON.stringify(eventData)
    });
    return data.event;
  },

  async deleteEvent(id) {
    return await this.request(`/api/events/${id}`, {
      method: "DELETE"
    });
  },

  async generatePlan(params) {
    const { provider, apiKey, model } = this.getActiveCredentials();
    return await this.request("/api/generate", {
      method: "POST",
      body: JSON.stringify({
        params,
        provider,
        apiKey,
        model,
        autoSave: true
      })
    });
  },

  async chat(messages, currentEvent) {
    const { provider, apiKey, model } = this.getActiveCredentials();
    return await this.request("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        messages,
        currentEvent,
        provider,
        apiKey,
        model
      })
    });
  },

  async draftVendorEmail(vendor, event) {
    const { provider, apiKey, model } = this.getActiveCredentials();
    return await this.request("/api/vendor-email", {
      method: "POST",
      body: JSON.stringify({ vendor, event, provider, apiKey, model })
    });
  },

  async getExtraIdeas(category, event) {
    const { provider, apiKey, model } = this.getActiveCredentials();
    return await this.request("/api/extra-ideas", {
      method: "POST",
      body: JSON.stringify({ category, event, provider, apiKey, model })
    });
  },

  async resetSamples() {
    const data = await this.request("/api/reset-samples", { method: "POST" });
    return data.events || [];
  },

  async testGeminiKey(key, model) {
    return await this.request("/api/test-gemini-key", {
      method: "POST",
      body: JSON.stringify({ apiKey: key, model: model || "gemini-2.5-flash" })
    });
  },

  async testGroqKey(key, model) {
    const targetModel = model || "qwen/qwen3.8-27b";
    // 1. Attempt direct browser fetch first (avoids any sandbox/proxy rules)
    try {
      const directRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${key.trim()}`
        },
        body: JSON.stringify({
          model: targetModel,
          messages: [{ role: "user", content: "hi" }],
          max_tokens: 5
        })
      });
      if (directRes.ok) {
        // Also fetch available models
        let models = [];
        try {
          const mRes = await fetch("https://api.groq.com/openai/v1/models", {
            headers: { "Authorization": `Bearer ${key.trim()}` }
          });
          if (mRes.ok) {
            const mData = await mRes.json();
            models = (mData.data || [])
              .map(m => m.id)
              .filter(id => !id.includes("whisper") && !id.includes("guard") && !id.includes("orpheus"));
          }
        } catch (_) {}
        return {
          success: true,
          message: `Connected to Groq Cloud using ${targetModel}!`,
          models: models.length ? models : [targetModel]
        };
      }
    } catch (_) {
      // Direct browser fetch failed (e.g. adblocker), proceed to backend
    }

    // 2. Fallback to backend route
    return await this.request("/api/test-groq-key", {
      method: "POST",
      body: JSON.stringify({ apiKey: key, model: targetModel })
    });
  }
};
