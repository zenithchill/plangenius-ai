/**
 * PlanGenius AI - Event Wizard Component
 */

const Wizard = {
  currentStep: 1,

  presets: {
    wedding: [
      "Rustic Garden Romance",
      "Modern Luxury Black Tie",
      "Desi / South Asian Grand Celebration",
      "Boho Beach / Coastal",
      "Intimate Minimalist City Hall",
      "Vintage Mountain Lodge"
    ],
    birthday: [
      "Kids Space Odyssey Adventure",
      "Kids Dinosaur Safari",
      "Milestone 30th Rooftop Lounge",
      "Golden 50th Gala Dinner",
      "Sweet 16 Glow Neon Dance",
      "Intimate Wine & Chef Tasting"
    ],
    community: [
      "Charity Gala & Silent Auction",
      "Neighborhood Summer Block Party",
      "Cultural Arts & Food Festival",
      "Community 5K Fun Run & Walk",
      "Tech Hackathon & Demo Day",
      "Artisan & Farmers Market"
    ]
  },

  open() {
    this.currentStep = 1;
    this.render();
    const modal = document.getElementById("modal-wizard");
    if (modal) modal.classList.add("active");
  },

  close() {
    const modal = document.getElementById("modal-wizard");
    if (modal) modal.classList.remove("active");
  },

  render() {
    const body = document.getElementById("wizard-body");
    const footer = document.getElementById("wizard-footer");
    if (!body || !footer) return;

    if (this.currentStep === 1) {
      body.innerHTML = `
        <div class="form-group">
          <label class="form-label">Event Type</label>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem;">
            <button type="button" class="btn btn-secondary wizard-type-btn active" data-type="wedding" onclick="Wizard.selectType('wedding', this)">
              ${getIcon('heart')} Wedding
            </button>
            <button type="button" class="btn btn-secondary wizard-type-btn" data-type="birthday" onclick="Wizard.selectType('birthday', this)">
              ${getIcon('cake')} Birthday
            </button>
            <button type="button" class="btn btn-secondary wizard-type-btn" data-type="community" onclick="Wizard.selectType('community', this)">
              ${getIcon('building')} Community
            </button>
          </div>
          <input type="hidden" id="wiz-event-type" value="wedding">
        </div>

        <div class="form-group">
          <label class="form-label">Event Title / Name</label>
          <input type="text" id="wiz-title" class="form-control" placeholder="e.g. Sophia & Liam's Garden Wedding" value="">
        </div>

        <div class="form-group">
          <label class="form-label">Subtype / Vibe Preset</label>
          <div id="wiz-presets-container" style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.4rem;">
            ${this.renderPresets("wedding")}
          </div>
          <input type="text" id="wiz-subtype" class="form-control" placeholder="or enter custom style (e.g. French Chateau Garden)" value="Rustic Garden Romance">
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
          <div class="form-group">
            <label class="form-label">Target Date</label>
            <input type="date" id="wiz-date" class="form-control" value="${this.getDefaultDate()}">
          </div>
          <div class="form-group">
            <label class="form-label">City / Venue Location</label>
            <input type="text" id="wiz-location" class="form-control" placeholder="e.g. Austin, TX" value="Austin, TX">
          </div>
        </div>
      `;

      footer.innerHTML = `
        <button type="button" class="btn btn-secondary" onclick="Wizard.close()">Cancel</button>
        <button type="button" class="btn btn-primary" onclick="Wizard.nextStep(2)">Next: Scale & Budget &rarr;</button>
      `;
    } else if (this.currentStep === 2) {
      body.innerHTML = `
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 0.75rem;">
          <div class="form-group">
            <label class="form-label">Total Target Budget</label>
            <input type="number" id="wiz-budget" class="form-control" min="100" step="500" value="20000">
          </div>
          <div class="form-group">
            <label class="form-label">Currency</label>
            <select id="wiz-currency" class="form-control">
              <option value="$" selected>USD ($)</option>
              <option value="€">EUR (€)</option>
              <option value="£">GBP (£)</option>
              <option value="₹">INR (₹)</option>
              <option value="C$">CAD (C$)</option>
              <option value="A$">AUD (A$)</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Target Guest Count</label>
          <input type="number" id="wiz-guests" class="form-control" min="5" max="10000" value="100">
          <small style="color: var(--text-muted); font-size: 0.75rem;">Budgets and catering quantities will automatically scale to this guest count.</small>
        </div>

        <div class="form-group">
          <label class="form-label">Venue Setting</label>
          <select id="wiz-venue-type" class="form-control">
            <option value="Outdoor Garden / Lawn">Outdoor Garden / Lawn</option>
            <option value="Indoor Banquet / Ballroom">Indoor Banquet / Ballroom</option>
            <option value="Industrial Loft / Gallery">Industrial Loft / Gallery</option>
            <option value="Public City Park / Pavilion">Public City Park / Pavilion</option>
            <option value="Private Home / Backyard">Private Home / Backyard</option>
            <option value="Destination Resort">Destination Resort</option>
          </select>
        </div>
      `;

      footer.innerHTML = `
        <button type="button" class="btn btn-secondary" onclick="Wizard.nextStep(1)">&larr; Back</button>
        <button type="button" class="btn btn-primary" onclick="Wizard.nextStep(3)">Next: Style & Priorities &rarr;</button>
      `;
    } else if (this.currentStep === 3) {
      body.innerHTML = `
        <div class="form-group">
          <label class="form-label">Theme & Aesthetic Vibe</label>
          <textarea id="wiz-theme" class="form-control" rows="2" placeholder="e.g. Warm earthy terracotta tones, organic olive greenery, cozy candlelight, indie acoustic energy"></textarea>
        </div>

        <div class="form-group">
          <label class="form-label">Top Priorities / Must-Haves</label>
          <input type="text" id="wiz-priorities" class="form-control" placeholder="e.g. Unforgettable food, candid photography, lively dance floor" value="Incredible food, great photography, relaxed vibe">
        </div>

        <div class="form-group">
          <label class="form-label">Dietary & Accessibility Considerations</label>
          <input type="text" id="wiz-dietary" class="form-control" placeholder="e.g. Gluten-free options, vegan entrees, ADA wheelchair accessibility" value="Vegetarian and gluten-free friendly">
        </div>

        <div id="wiz-loading" style="display: none; padding: 1rem; background: var(--bg-primary); border-radius: var(--radius-md); text-align: center;">
          <div style="font-size: 1.5rem; margin-bottom: 0.5rem; animation: spin 1.5s linear infinite; display: inline-block;">✨</div>
          <div id="wiz-loading-text" style="font-weight: 600; color: #A5B4FC; font-size: 0.95rem;">PlanGenius AI is orchestrating your master plan...</div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">Synthesizing itemized budgets, milestone timeline, day-of run-of-show, and creative ideas</div>
        </div>
      `;

      footer.innerHTML = `
        <button type="button" class="btn btn-secondary" onclick="Wizard.nextStep(2)">&larr; Back</button>
        <button type="button" id="wiz-submit-btn" class="btn btn-sparkle" onclick="Wizard.submit()">
          ${getIcon('sparkles')} Generate Full Master Plan
        </button>
      `;
    }
  },

  selectType(type, btn) {
    document.querySelectorAll(".wizard-type-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const hidden = document.getElementById("wiz-event-type");
    if (hidden) hidden.value = type;

    const presetsContainer = document.getElementById("wiz-presets-container");
    if (presetsContainer) {
      presetsContainer.innerHTML = this.renderPresets(type);
    }
    const subtypeInput = document.getElementById("wiz-subtype");
    if (subtypeInput) {
      subtypeInput.value = this.presets[type][0] || "";
    }
  },

  renderPresets(type) {
    const list = this.presets[type] || [];
    return list.map(item => `
      <span class="prompt-pill" onclick="Wizard.pickPreset('${item}')">${item}</span>
    `).join("");
  },

  pickPreset(name) {
    const subtypeInput = document.getElementById("wiz-subtype");
    if (subtypeInput) subtypeInput.value = name;
  },

  getDefaultDate() {
    const d = new Date();
    d.setDate(d.getDate() + 180);
    return d.toISOString().split("T")[0];
  },

  // In-memory wizard state across steps
  formData: {
    eventType: "wedding",
    title: "",
    subType: "Rustic Garden Romance",
    date: "",
    location: "Austin, TX",
    totalBudget: 20000,
    currency: "$",
    guestCount: 100,
    venueType: "Outdoor Garden / Lawn",
    theme: "",
    priorities: "",
    dietaryNotes: ""
  },

  nextStep(step) {
    // Save current step data
    if (this.currentStep === 1) {
      this.formData.eventType = document.getElementById("wiz-event-type")?.value || "wedding";
      this.formData.title = document.getElementById("wiz-title")?.value || "";
      this.formData.subType = document.getElementById("wiz-subtype")?.value || "";
      this.formData.date = document.getElementById("wiz-date")?.value || "";
      this.formData.location = document.getElementById("wiz-location")?.value || "";
    } else if (this.currentStep === 2) {
      this.formData.totalBudget = parseFloat(document.getElementById("wiz-budget")?.value || 10000);
      this.formData.currency = document.getElementById("wiz-currency")?.value || "$";
      this.formData.guestCount = parseInt(document.getElementById("wiz-guests")?.value || 80);
      this.formData.venueType = document.getElementById("wiz-venue-type")?.value || "";
    }

    this.currentStep = step;
    this.render();
  },

  async submit() {
    this.formData.theme = document.getElementById("wiz-theme")?.value || `${this.formData.subType} with modern elegance`;
    this.formData.priorities = document.getElementById("wiz-priorities")?.value || "Great guest experience, memorable atmosphere";
    this.formData.dietaryNotes = document.getElementById("wiz-dietary")?.value || "Vegetarian and allergy friendly";

    if (!this.formData.title) {
      this.formData.title = `${this.formData.subType} Celebration`;
    }

    const loadingDiv = document.getElementById("wiz-loading");
    const submitBtn = document.getElementById("wiz-submit-btn");
    if (loadingDiv) loadingDiv.style.display = "block";
    if (submitBtn) submitBtn.disabled = true;

    try {
      const res = await API.generatePlan(this.formData);
      if (res.success && res.event) {
        showToast("✨ Event plan generated successfully!", "success");
        this.close();
        // Trigger app reload with new event
        await App.loadEvents(res.event.id);
        triggerCelebration();
      } else {
        throw new Error(res.error || "Failed to generate plan");
      }
    } catch (err) {
      showToast(err.message, "error");
      if (loadingDiv) loadingDiv.style.display = "none";
      if (submitBtn) submitBtn.disabled = false;
    }
  }
};
