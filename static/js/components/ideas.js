/**
 * PlanGenius AI - Master Plan & Personalized Ideas Component
 */

const IdeasComponent = {
  render(event) {
    const container = document.getElementById("tab-ideas");
    if (!container) return;

    const palette = event.colorPalette || [];
    const ideas = event.creativeIdeas || [];

    container.innerHTML = `
      <!-- Event Theme & Concept Card -->
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">${getIcon('bulb')} Concept & Aesthetic Direction</h2>
            <p class="card-description">Guiding design pillars and personalized atmosphere for this event.</p>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="App.openCopilotWithPrompt('Help me brainstorm 3 new interactive activities for my guests')">
            ${getIcon('sparkles')} Brainstorm with AI
          </button>
        </div>

        <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1.25rem; margin-bottom: 1.5rem;">
          <h3 style="font-size: 1.1rem; font-weight: 700; color: #C7D2FE; margin-bottom: 0.5rem;">
            "${event.theme || 'Unique Celebration'}"
          </h3>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin-top: 1rem; font-size: 0.875rem;">
            <div>
              <span style="color: var(--text-muted); font-size: 0.775rem; text-transform: uppercase; font-weight: 600;">Top Priorities</span>
              <p style="color: var(--text-sub); margin-top: 0.2rem;">${event.priorities || 'Create an unforgettable, seamless celebration'}</p>
            </div>
            <div>
              <span style="color: var(--text-muted); font-size: 0.775rem; text-transform: uppercase; font-weight: 600;">Dietary & Special Notes</span>
              <p style="color: var(--text-sub); margin-top: 0.2rem;">${event.dietaryNotes || 'Standard menu options'}</p>
            </div>
          </div>
        </div>

        <!-- Color Palette -->
        <div>
          <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem;">
            <h3 style="font-size: 0.95rem; font-weight: 600; color: var(--text-main);">Curated Color Palette</h3>
            <span style="font-size: 0.75rem; color: var(--text-muted);">Click any swatch to copy hex code</span>
          </div>

          <div class="palette-row">
            ${palette.map(swatch => `
              <div class="palette-swatch" style="background-color: ${swatch.hex};" onclick="IdeasComponent.copyHex('${swatch.hex}')">
                <span class="swatch-copy-hint">Copy</span>
                <span class="swatch-name">${swatch.name}</span>
                <span class="swatch-hex">${swatch.hex}</span>
              </div>
            `).join("")}
          </div>
        </div>
      </div>

      <!-- Personalized Ideas Grid -->
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">${getIcon('sparkles')} Curated Signature Experiences</h2>
            <p class="card-description">Personalized guest experiences, food & beverage twists, entertainment, and keepsake favors.</p>
          </div>
          <button class="btn btn-sparkle btn-sm" id="btn-more-ideas" onclick="IdeasComponent.generateMoreIdeas()">
            ${getIcon('plus')} Generate More Ideas
          </button>
        </div>

        <div class="ideas-grid" id="ideas-container">
          ${ideas.map(item => `
            <div class="idea-card">
              <div>
                <span class="idea-cat-tag">${item.category || 'Experience'}</span>
                <h4 class="idea-title">${item.title}</h4>
                <p class="idea-desc">${item.description}</p>
              </div>
            </div>
          `).join("")}
        </div>

        <!-- Dilemma Solver Callout -->
        <div style="margin-top: 1.5rem; background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.1)); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: var(--radius-md); padding: 1.25rem;">
          <h4 style="font-size: 0.95rem; font-weight: 600; color: var(--text-main); margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.5rem;">
            ${getIcon('bulb')} Got a Planning Dilemma?
          </h4>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">Ask PlanGenius AI to resolve weather contingencies, awkward seating situations, or budget cuts in real-time.</p>
          <div style="display: flex; gap: 0.5rem;">
            <input type="text" id="dilemma-input" class="form-control" placeholder="e.g. What is our rain backup plan for an outdoor lawn ceremony?" onkeydown="if(event.key==='Enter') IdeasComponent.askDilemma()">
            <button class="btn btn-primary" onclick="IdeasComponent.askDilemma()">Ask Co-pilot</button>
          </div>
        </div>
      </div>
    `;
  },

  copyHex(hex) {
    navigator.clipboard.writeText(hex).then(() => {
      showToast(`Copied ${hex} to clipboard!`, "success");
    });
  },

  async generateMoreIdeas() {
    if (!App.currentEvent) return;
    const btn = document.getElementById("btn-more-ideas");
    if (btn) btn.disabled = true;

    try {
      showToast("Generating extra creative ideas...", "info");
      const res = await API.getExtraIdeas("general", App.currentEvent);
      if (res.success && res.ideas && res.ideas.length) {
        if (!App.currentEvent.creativeIdeas) App.currentEvent.creativeIdeas = [];
        App.currentEvent.creativeIdeas.push(...res.ideas);
        await App.saveCurrentEvent(false);
        this.render(App.currentEvent);
        showToast("✨ Added new signature ideas!", "success");
      }
    } catch (err) {
      showToast("Error generating ideas: " + err.message, "error");
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  askDilemma() {
    const input = document.getElementById("dilemma-input");
    if (!input || !input.value.trim()) return;
    const question = input.value.trim();
    input.value = "";
    App.openCopilotWithPrompt(question);
  }
};
