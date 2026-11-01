/**
 * PlanGenius AI - Universal Backend API & Standalone Client Engine
 * Operates seamlessly with Flask backend OR 100% serverless on GitHub Pages
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

  isStaticHost() {
    return (
      window.location.protocol === "file:" ||
      window.location.hostname.includes("github.io") ||
      window.location.hostname.includes("gitlab.io")
    );
  },

  async request(endpoint, options = {}) {
    if (this.isStaticHost()) {
      throw new Error("STATIC_HOST");
    }
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

  // Local Storage Event Helpers
  getLocalEvents() {
    let stored = localStorage.getItem("plangenius_events");
    if (!stored) {
      stored = typeof SAMPLE_EVENTS !== "undefined" ? JSON.stringify(SAMPLE_EVENTS) : "[]";
      localStorage.setItem("plangenius_events", stored);
    }
    try {
      return JSON.parse(stored);
    } catch (_) {
      return [];
    }
  },

  saveLocalEvents(events) {
    localStorage.setItem("plangenius_events", JSON.stringify(events));
  },

  async listEvents() {
    try {
      const data = await this.request("/api/events");
      return data.events || [];
    } catch (_) {
      return this.getLocalEvents();
    }
  },

  async getEvent(id) {
    try {
      const data = await this.request(`/api/events/${id}`);
      return data.event;
    } catch (_) {
      const list = this.getLocalEvents();
      return list.find(e => e.id === id) || list[0] || null;
    }
  },

  async saveEvent(eventData) {
    try {
      const data = await this.request("/api/events", {
        method: "POST",
        body: JSON.stringify(eventData)
      });
      return data.event;
    } catch (_) {
      const list = this.getLocalEvents();
      const idx = list.findIndex(e => e.id === eventData.id);
      if (idx >= 0) {
        list[idx] = eventData;
      } else {
        list.unshift(eventData);
      }
      this.saveLocalEvents(list);
      return eventData;
    }
  },

  async deleteEvent(id) {
    try {
      return await this.request(`/api/events/${id}`, { method: "DELETE" });
    } catch (_) {
      let list = this.getLocalEvents();
      list = list.filter(e => e.id !== id);
      this.saveLocalEvents(list);
      return { success: true };
    }
  },

  async resetSamples() {
    try {
      const data = await this.request("/api/reset-samples", { method: "POST" });
      return data.events || [];
    } catch (_) {
      if (typeof SAMPLE_EVENTS !== "undefined") {
        this.saveLocalEvents(SAMPLE_EVENTS);
        return SAMPLE_EVENTS;
      }
      return [];
    }
  },

  // Direct Groq Cloud Browser Fetch
  async callGroqDirect(promptOrMessages, systemInstruction = "", apiKey = "", model = "qwen/qwen3.8-27b", jsonMode = false) {
    const key = (apiKey || this.getGroqKey()).trim();
    if (!key) throw new Error("Missing Groq API Key. Please enter it in Settings.");

    const activeModel = model || "qwen/qwen3.8-27b";
    const messages = [];
    if (systemInstruction) {
      messages.push({ role: "system", content: systemInstruction });
    }
    if (Array.isArray(promptOrMessages)) {
      promptOrMessages.forEach(m => {
        const rawRole = m.role || "user";
        const role = (rawRole === "ai" || rawRole === "assistant") ? "assistant" : (rawRole === "system" ? "system" : "user");
        const content = (m.content || "").trim();
        if (content) messages.push({ role, content });
      });
    } else {
      messages.push({ role: "user", content: String(promptOrMessages) });
    }

    const payload = {
      model: activeModel,
      messages,
      temperature: 0.7,
      max_tokens: 750
    };
    if (jsonMode) {
      payload.response_format = { type: "json_object" };
    }

    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${key}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      // Auto retry alternative model if 429 rate limit or not found
      if ((res.status === 429 || err.error?.message?.includes("model_not_found")) && activeModel !== "openai/gpt-oss-20b") {
        return this.callGroqDirect(promptOrMessages, systemInstruction, key, "openai/gpt-oss-20b", jsonMode);
      }
      throw new Error(err.error?.message || `Groq API Error (${res.status})`);
    }

    const data = await res.json();
    return data.choices?.[0]?.message?.content || "";
  },

  async generatePlan(params) {
    const { provider, apiKey, model } = this.getActiveCredentials();
    try {
      return await this.request("/api/generate", {
        method: "POST",
        body: JSON.stringify({ params, provider, apiKey, model, autoSave: true })
      });
    } catch (e) {
      if (provider === "groq" && apiKey) {
        try {
          const sysPrompt = "You are PlanGenius AI. Return ONLY a single raw JSON object matching the master plan schema.";
          const userPrompt = `Generate a master event plan for ${params.eventType} '${params.title}', budget: ${params.currency || '$'}${params.totalBudget}, guests: ${params.guestCount}, date: ${params.date}, location: ${params.location}. Return JSON with keys: title, eventType, subType, date, location, guestCount, totalBudget, currency, theme, priorities, dietaryNotes, colorPalette (5 items), creativeIdeas (4 items), budgetItems (8 items), timelineMilestones (6 items), runOfShow (7 items), vendors (5 items).`;
          const raw = await this.callGroqDirect(userPrompt, sysPrompt, apiKey, model, true);
          let cleaned = raw.trim();
          if (cleaned.startsWith("```json")) cleaned = cleaned.slice(7);
          if (cleaned.startsWith("```")) cleaned = cleaned.slice(3);
          if (cleaned.endsWith("```")) cleaned = cleaned.slice(0, -3);
          const parsed = JSON.parse(cleaned.trim());
          parsed.id = `evt-${Date.now()}`;
          const saved = await this.saveEvent(parsed);
          return { success: true, event: saved, isLocal: false };
        } catch (_) {}
      }
      // Built-in client-side generator
      const localPlan = this.buildLocalPlan(params);
      const saved = await this.saveEvent(localPlan);
      return { success: true, event: saved, isLocal: true };
    }
  },

  buildLocalPlan(params) {
    const type = params.eventType || "wedding";
    const budget = Number(params.totalBudget) || 15000;
    const curr = params.currency || "$";
    const date = params.date || "2027-06-20";

    return {
      id: `evt-${Date.now()}`,
      title: params.title || `Special ${type.toUpperCase()}`,
      eventType: type,
      subType: params.subType || "Celebration",
      date,
      location: params.location || "Scenic Venue",
      guestCount: Number(params.guestCount) || 100,
      totalBudget: budget,
      currency: curr,
      theme: params.theme || "Modern Celebration",
      priorities: params.priorities || "Atmosphere, cuisine, guest delight",
      dietaryNotes: params.dietaryNotes || "Vegetarian options provided",
      colorPalette: [
        { name: "Primary Tone", hex: "#6366F1" },
        { name: "Warm Accent", hex: "#F59E0B" },
        { name: "Cream White", hex: "#F8FAFC" },
        { name: "Deep Navy", hex: "#1E293B" },
        { name: "Champagne Gold", hex: "#E2E8F0" }
      ],
      creativeIdeas: [
        { title: "Signature Welcome Toast", category: "Hospitality", description: "Personalized welcome beverages served in etched glassware upon guest entry." },
        { title: "Interactive Memory Wall", category: "Decor", description: "Hanging floral grid where guests leave handwritten cards and candid snapshots." },
        { title: "Surprise Late Night Bites", category: "Catering", description: "Mini sliders and artisanal gelato passed on the dance floor at 10 PM." },
        { title: "Acoustic Sunset Prelude", category: "Music", description: "Live violin/guitar arrangements of contemporary anthems during golden hour." }
      ],
      budgetItems: [
        { id: "b1", category: "Venue", name: "Venue Booking & Facility Fee", estimated: Math.round(budget * 0.35), actual: 0, status: "pending", notes: "Initial deposit due" },
        { id: "b2", category: "Catering", name: "Dinner & Beverage Package", estimated: Math.round(budget * 0.30), actual: 0, status: "pending", notes: "Includes bar service" },
        { id: "b3", category: "Photography", name: "Photo & Video Team", estimated: Math.round(budget * 0.12), actual: 0, status: "pending", notes: "Full day coverage" },
        { id: "b4", category: "Music", name: "DJ / Live Ensemble", estimated: Math.round(budget * 0.08), actual: 0, status: "pending", notes: "Sound & lighting setup" },
        { id: "b5", category: "Decor", name: "Florals & Design Rentals", estimated: Math.round(budget * 0.08), actual: 0, status: "pending", notes: "Tables & entryway" },
        { id: "b6", category: "Stationery", name: "Invitations & Signage", estimated: Math.round(budget * 0.03), actual: 0, status: "pending", notes: "Physical & digital" },
        { id: "b7", category: "Contingency", name: "Emergency Buffer Fund", estimated: Math.round(budget * 0.04), actual: 0, status: "pending", notes: "Unforeseen expenses" }
      ],
      timelineMilestones: [
        { id: "m1", phase: "9-12 Months Out", task: "Lock venue and target date", completed: true, dueDate: date },
        { id: "m2", phase: "6 Months Out", task: "Contract primary catering and photo teams", completed: false, dueDate: date },
        { id: "m3", phase: "3 Months Out", task: "Send invitations & finalize design palette", completed: false, dueDate: date },
        { id: "m4", phase: "1 Month Out", task: "Confirm final RSVPs and dietary counts", completed: false, dueDate: date },
        { id: "m5", phase: "1 Week Out", task: "Rehearse schedule and hand off run-of-show", completed: false, dueDate: date },
        { id: "m6", phase: "Day Of", task: "Execute master event celebration!", completed: false, dueDate: date }
      ],
      runOfShow: [
        { id: "r1", time: "14:00", activity: "Vendor load-in & technical sound check", responsible: "Lead Coordinator", location: "Main Venue" },
        { id: "r2", time: "16:00", activity: "Guest arrivals & welcome cocktail reception", responsible: "Host Team", location: "Entry Courtyard" },
        { id: "r3", time: "17:00", activity: "Main ceremony / keynote opening celebration", responsible: "Host", location: "Central Lawn" },
        { id: "r4", time: "18:00", activity: "Cocktail transition & golden hour photo session", responsible: "Photo Team", location: "Terrace" },
        { id: "r5", time: "19:15", activity: "Dinner service & celebration toasts", responsible: "Catering Lead", location: "Dining Hall" },
        { id: "r6", time: "20:45", activity: "Party opening dance & evening entertainment", responsible: "DJ / Band", location: "Dance Floor" },
        { id: "r7", time: "23:00", activity: "Grand farewell send-off & guest departures", responsible: "All Leads", location: "Main Gate" }
      ],
      vendors: [
        { id: "v1", category: "Venue", name: "Venue Management Team", contact: "events@venue.com", phone: "+1 (555) 234-5678", status: "to_research", quoted: Math.round(budget * 0.35), notes: "Check curfew and insurance policy" },
        { id: "v2", category: "Catering", name: "Artisanal Feast Catering", contact: "catering@food.com", phone: "+1 (555) 345-6789", status: "to_research", quoted: Math.round(budget * 0.30), notes: "Tasting menu scheduled" },
        { id: "v3", category: "Photography", name: "Luminous Story Photographers", contact: "hello@luminous.com", phone: "+1 (555) 456-7890", status: "to_research", quoted: Math.round(budget * 0.12), notes: "8 hours coverage" },
        { id: "v4", category: "Music", name: "SoundWave Entertainment", contact: "dj@soundwave.com", phone: "+1 (555) 567-8901", status: "to_research", quoted: Math.round(budget * 0.08), notes: "Wireless mic package included" },
        { id: "v5", category: "Florals", name: "Botanical Bloom Studio", contact: "blooms@studio.com", phone: "+1 (555) 678-9012", status: "to_research", quoted: Math.round(budget * 0.08), notes: "Locally sourced seasonal florals" }
      ]
    };
  },

  async chat(messages, currentEvent) {
    const { provider, apiKey, model } = this.getActiveCredentials();
    try {
      return await this.request("/api/chat", {
        method: "POST",
        body: JSON.stringify({ messages, currentEvent, provider, apiKey, model })
      });
    } catch (_) {
      // If Groq key is available, call Groq Cloud directly from browser!
      if (provider === "groq" && apiKey) {
        const eventCtx = currentEvent ? `
Active Event:
- Title: ${currentEvent.title}
- Type: ${currentEvent.eventType} (${currentEvent.subType})
- Date: ${currentEvent.date} | Location: ${currentEvent.location}
- Guests: ${currentEvent.guestCount}
- Budget: ${currentEvent.currency || '$'}${currentEvent.totalBudget}
- Theme: ${currentEvent.theme}
- Priorities: ${currentEvent.priorities}
` : "";
        const sys = `You are PlanGenius AI Co-pilot, an elite event planning strategist. Provide clear, structured, actionable advice tailored to the active event.\n${eventCtx}`;
        try {
          const reply = await this.callGroqDirect(messages, sys, apiKey, model);
          return { success: true, reply };
        } catch (err) {
          return { success: true, reply: `⚠️ Groq Direct Error: ${err.message}` };
        }
      }

      // Local rule-based chat fallback
      const lastMsg = (messages[messages.length - 1]?.content || "").toLowerCase();
      const title = currentEvent?.title || "your celebration";
      const curr = currentEvent?.currency || "$";
      const budget = currentEvent?.totalBudget || 15000;

      if (lastMsg.includes("budget") || lastMsg.includes("cost") || lastMsg.includes("reduce") || lastMsg.includes("save")) {
        const cut = Math.round(budget * 0.15);
        return {
          success: true,
          reply: `### 💡 Budget Optimization for **${title}**\n\nTo trim **15% (${curr}${cut.toLocaleString()})** without impacting guest delight:\n\n1. **High-Impact Adjustments**: Shift bar service to premium signature cocktails and local wine/beer.\n2. **Floral & Decor Repurposing**: Move ceremony arrangements to the dining reception.\n3. **Vendor Synergy**: Book photo and video with the same team for multi-service discounts.`
        };
      }

      return {
        success: true,
        reply: `### 🌟 Planning Insights for **${title}**\n\nI am active with the full context of your event (${currentEvent?.guestCount || 100} guests, ${curr}${budget.toLocaleString()} budget).\n\n*   **Vendor Check**: Check your **Vendors** tab to confirm top deliverables.\n*   **Timeline Roadmap**: Mark completed milestones to keep coordination on track.\n\n*Tip: Enter a free Groq API key in Settings (⚡ icon) for live multi-turn GenAI responses!*`
      };
    }
  },

  async draftVendorEmail(vendor, event) {
    const { provider, apiKey, model } = this.getActiveCredentials();
    try {
      return await this.request("/api/vendor-email", {
        method: "POST",
        body: JSON.stringify({ vendor, event, provider, apiKey, model })
      });
    } catch (_) {
      if (provider === "groq" && apiKey) {
        try {
          const prompt = `Draft a warm, professional inquiry email for ${vendor.category} services from vendor '${vendor.name}' for '${event.title}' on ${event.date} at ${event.location}. Estimated guests: ${event.guestCount}, target budget: ${event.currency || '$'}${vendor.quoted}. Include subject line and call to action.`;
          const email = await this.callGroqDirect(prompt, "You are a luxury event planner drafting correspondence. Output only the finished email with Subject: line.", apiKey, model);
          return { success: true, email };
        } catch (_) {}
      }
      return {
        success: true,
        email: `Subject: Inquiry for ${vendor.category} Services: ${event.title} (${event.date})

Hello ${vendor.name},

I hope you're having a wonderful week!

We are currently planning ${event.title} and love your work in ${vendor.category}. We would love to check your availability for our date and explore working together.

Key Event Details:
• Event: ${event.title}
• Date: ${event.date}
• Venue / Location: ${event.location}
• Estimated Guest Count: ${event.guestCount}
• Target Budget: around ${event.currency || '$'}${Number(vendor.quoted || 0).toLocaleString()}

Could you please confirm if your team is available on ${event.date}? If so, please share your standard package brochure and next steps.

Best regards,

[Your Name]
[Your Phone Number]
[Your Email]`
      };
    }
  },

  async getExtraIdeas(category, event) {
    const { provider, apiKey, model } = this.getActiveCredentials();
    try {
      return await this.request("/api/extra-ideas", {
        method: "POST",
        body: JSON.stringify({ category, event, provider, apiKey, model })
      });
    } catch (_) {
      return {
        success: true,
        ideas: [
          { title: `${category.toUpperCase()} Interactive Experience`, category: category.charAt(0).toUpperCase() + category.slice(1), description: `Curated bespoke element tailored to ${event.title} and ${event.theme}.` },
          { title: `Signature ${category.toUpperCase()} Highlight`, category: category.charAt(0).toUpperCase() + category.slice(1), description: `Engaging focal moment that creates memorable photos for all ${event.guestCount} guests.` }
        ]
      };
    }
  },

  async testGeminiKey(key, model) {
    try {
      return await this.request("/api/test-gemini-key", {
        method: "POST",
        body: JSON.stringify({ apiKey: key, model: model || "gemini-2.5-flash" })
      });
    } catch (_) {
      // Direct browser test for Gemini
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${model || 'gemini-2.5-flash'}:generateContent?key=${key.trim()}`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: "Hello! Respond with OK." }] }]
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error?.message || `HTTP ${res.status}`);
      }
      return { success: true, message: "Connected to Gemini directly from browser!" };
    }
  },

  async testGroqKey(key, model) {
    const targetModel = model || "qwen/qwen3.8-27b";
    try {
      const res = await this.callGroqDirect("Hello! Respond with OK.", "", key, targetModel);
      let models = [targetModel];
      try {
        const mRes = await fetch("https://api.groq.com/openai/v1/models", {
          headers: { "Authorization": `Bearer ${key.trim()}` }
        });
        if (mRes.ok) {
          const mData = await mRes.json();
          models = (mData.data || []).map(m => m.id).filter(id => !id.includes("whisper") && !id.includes("guard"));
        }
      } catch (_) {}
      return {
        success: true,
        message: `Connected to Groq Cloud using ${targetModel}!`,
        models: models.length ? models : [targetModel]
      };
    } catch (err) {
      try {
        return await this.request("/api/test-groq-key", {
          method: "POST",
          body: JSON.stringify({ apiKey: key, model: targetModel })
        });
      } catch (_) {
        throw new Error(err.message);
      }
    }
  },

  exportICS(event) {
    if (!event) return;
    const lines = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//PlanGenius AI//Event Schedule//EN",
      "CALSCALE:GREGORIAN",
      "METHOD:PUBLISH"
    ];
    const eventDate = (event.date || "").replace(/-/g, "");
    (event.runOfShow || []).forEach(item => {
      lines.push("BEGIN:VEVENT");
      lines.push(`SUMMARY:${item.activity || 'Activity'}`);
      lines.push(`DESCRIPTION:Lead: ${item.responsible || 'Team'} | Location: ${item.location || 'Venue'}`);
      lines.push(`LOCATION:${item.location || event.location || 'Venue'}`);
      if (eventDate.length === 8) {
        lines.push(`DTSTART;VALUE=DATE:${eventDate}`);
        lines.push(`DTEND;VALUE=DATE:${eventDate}`);
      }
      lines.push(`UID:evt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}@plangenius.ai`);
      lines.push("STATUS:CONFIRMED");
      lines.push("END:VEVENT");
    });
    lines.push("END:VCALENDAR");

    const blob = new Blob([lines.join("\r\n")], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(event.title || 'event').replace(/[^a-zA-Z0-9]/g, '_')}_schedule.ics`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
};
