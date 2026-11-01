/**
 * PlanGenius AI - Timeline & Day-Of Run of Show Component
 */

const TimelineComponent = {
  viewMode: "roadmap", // "roadmap" or "runofshow"

  render(event) {
    const container = document.getElementById("tab-timeline");
    if (!container) return;

    const milestones = event.timelineMilestones || [];
    const runOfShow = event.runOfShow || [];

    const completedMilestones = milestones.filter(m => m.completed).length;
    const progressPct = milestones.length ? Math.round((completedMilestones / milestones.length) * 100) : 0;

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">${getIcon('clock')} Timeline & Day-Of Run of Show</h2>
            <p class="card-description">Coordinate phased preparation milestones and hour-by-hour event day execution.</p>
          </div>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <div style="background: var(--bg-surface); padding: 0.2rem; border-radius: var(--radius-md); display: flex;">
              <button class="btn btn-sm ${this.viewMode === 'roadmap' ? 'btn-primary' : 'btn-secondary'}" onclick="TimelineComponent.switchView('roadmap')">
                ${getIcon('calendar')} Milestone Roadmap (${completedMilestones}/${milestones.length})
              </button>
              <button class="btn btn-sm ${this.viewMode === 'runofshow' ? 'btn-primary' : 'btn-secondary'}" onclick="TimelineComponent.switchView('runofshow')">
                ${getIcon('clock')} Day-Of Run of Show (${runOfShow.length})
              </button>
            </div>
            <button type="button" class="btn btn-secondary btn-sm" onclick="TimelineComponent.exportICS()" title="Sync with Apple Calendar, Google Calendar, or Outlook">
              ${getIcon('download')} Sync to Calendar (.ics)
            </button>
          </div>
        </div>

        ${this.viewMode === 'roadmap' ? this.renderRoadmap(milestones, progressPct) : this.renderRunOfShow(runOfShow)}
      </div>
    `;
  },

  exportICS() {
    if (App.currentEvent) {
      API.exportICS(App.currentEvent);
    }
  },

  switchView(mode) {
    this.viewMode = mode;
    this.render(App.currentEvent);
  },

  renderRoadmap(milestones, progressPct) {
    // Group milestones by phase
    const groups = {};
    milestones.forEach(m => {
      const phase = m.phase || "Preparation";
      if (!groups[phase]) groups[phase] = [];
      groups[phase].push(m);
    });

    return `
      <!-- Progress Bar Banner -->
      <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; font-size: 0.85rem;">
          <span style="font-weight: 600;">Overall Milestone Completion</span>
          <span style="color: #A5B4FC; font-weight: 700;">${progressPct}% Completed</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar-fill fill-primary" style="width: ${progressPct}%;"></div>
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
        <button class="btn btn-primary btn-sm" onclick="TimelineComponent.openAddMilestoneModal()">
          ${getIcon('plus')} Add Milestone Task
        </button>
      </div>

      <div class="roadmap-phases">
        ${Object.entries(groups).map(([phaseName, list]) => `
          <div class="timeline-phase">
            <div class="timeline-phase-title">
              ${getIcon('calendar')} ${phaseName}
            </div>
            ${list.map(item => `
              <div class="timeline-item ${item.completed ? 'completed' : ''}">
                <div class="timeline-item-left">
                  <input type="checkbox" class="timeline-checkbox" ${item.completed ? 'checked' : ''} onchange="TimelineComponent.toggleMilestone('${item.id}', this.checked)">
                  <span class="timeline-task-title">${item.task}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                  <span class="timeline-due-date">${item.dueDate ? 'Due: ' + item.dueDate : ''}</span>
                  <button class="btn btn-secondary btn-sm btn-icon-only" style="color: #EF4444;" onclick="TimelineComponent.deleteMilestone('${item.id}')">${getIcon('trash')}</button>
                </div>
              </div>
            `).join("")}
          </div>
        `).join("")}
      </div>
    `;
  },

  renderRunOfShow(runOfShow) {
    return `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
        <p style="font-size: 0.85rem; color: var(--text-muted);">Hour-by-hour master schedule for wedding coordinators, MCs, stage leads, and vendors on event day.</p>
        <button class="btn btn-primary btn-sm" onclick="TimelineComponent.openAddRunOfShowModal()">
          ${getIcon('plus')} Add Schedule Block
        </button>
      </div>

      <div style="display: flex; flex-direction: column; gap: 0.75rem;">
        ${runOfShow.length === 0 ? `
          <div style="text-align: center; padding: 3rem; color: var(--text-muted); background: var(--bg-secondary); border-radius: var(--radius-md);">
            No schedule blocks created yet. Click "+ Add Schedule Block" to build your run of show!
          </div>
        ` : runOfShow.map((item, idx) => `
          <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1rem 1.25rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 1.25rem; flex: 1; min-width: 280px;">
              <span class="countdown-chip" style="min-width: 105px; justify-content: center; font-size: 0.8rem; background: rgba(99, 102, 241, 0.15);">
                ${item.time}
              </span>
              <div>
                <h4 style="font-size: 0.95rem; font-weight: 600; color: var(--text-main); margin-bottom: 0.25rem;">
                  ${item.activity}
                </h4>
                <div style="display: flex; gap: 1rem; font-size: 0.775rem; color: var(--text-muted); flex-wrap: wrap;">
                  <span><strong>Lead:</strong> ${item.responsible || 'Coordinator'}</span>
                  <span><strong>Location:</strong> ${item.location || 'Main Venue'}</span>
                </div>
              </div>
            </div>
            <div style="display: flex; align-items: center; gap: 0.4rem;">
              <button class="btn btn-secondary btn-sm btn-icon-only" style="color: #EF4444;" onclick="TimelineComponent.deleteRunOfShowItem('${item.id}')">${getIcon('trash')}</button>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  },

  async toggleMilestone(milestoneId, isChecked) {
    if (!App.currentEvent) return;
    const m = (App.currentEvent.timelineMilestones || []).find(it => it.id === milestoneId);
    if (m) {
      m.completed = isChecked;
      await App.saveCurrentEvent(false);
      this.render(App.currentEvent);
      if (isChecked) {
        showToast("Milestone marked complete! 🎉", "success");
      }
    }
  },

  openAddMilestoneModal() {
    document.getElementById("milestone-form")?.reset();
    document.getElementById("modal-milestone")?.classList.add("active");
  },

  closeMilestoneModal() {
    document.getElementById("modal-milestone")?.classList.remove("active");
  },

  async saveMilestoneFromModal() {
    if (!App.currentEvent) return;
    const phase = document.getElementById("milestone-phase")?.value.trim() || "Upcoming";
    const task = document.getElementById("milestone-task")?.value.trim();
    const dueDate = document.getElementById("milestone-date")?.value || "";

    if (!task) {
      showToast("Please enter a milestone description", "error");
      return;
    }

    if (!App.currentEvent.timelineMilestones) App.currentEvent.timelineMilestones = [];
    App.currentEvent.timelineMilestones.push({
      id: "m_" + Date.now().toString(36),
      phase,
      task,
      completed: false,
      dueDate
    });

    this.closeMilestoneModal();
    await App.saveCurrentEvent(true);
    showToast("Milestone task added", "success");
  },

  async deleteMilestone(id) {
    if (!App.currentEvent) return;
    App.currentEvent.timelineMilestones = (App.currentEvent.timelineMilestones || []).filter(m => m.id !== id);
    await App.saveCurrentEvent(true);
    showToast("Milestone deleted", "info");
  },

  openAddRunOfShowModal() {
    document.getElementById("runofshow-form")?.reset();
    document.getElementById("modal-runofshow")?.classList.add("active");
  },

  closeRunOfShowModal() {
    document.getElementById("modal-runofshow")?.classList.remove("active");
  },

  async saveRunOfShowFromModal() {
    if (!App.currentEvent) return;
    const time = document.getElementById("ros-time")?.value.trim();
    const activity = document.getElementById("ros-activity")?.value.trim();
    const responsible = document.getElementById("ros-responsible")?.value.trim() || "Lead Coordinator";
    const location = document.getElementById("ros-location")?.value.trim() || "Main Venue";

    if (!time || !activity) {
      showToast("Please enter both time and activity", "error");
      return;
    }

    if (!App.currentEvent.runOfShow) App.currentEvent.runOfShow = [];
    App.currentEvent.runOfShow.push({
      id: "r_" + Date.now().toString(36),
      time,
      activity,
      responsible,
      location
    });

    this.closeRunOfShowModal();
    await App.saveCurrentEvent(true);
    showToast("Schedule block added", "success");
  },

  async deleteRunOfShowItem(id) {
    if (!App.currentEvent) return;
    App.currentEvent.runOfShow = (App.currentEvent.runOfShow || []).filter(r => r.id !== id);
    await App.saveCurrentEvent(true);
    showToast("Schedule block deleted", "info");
  }
};
