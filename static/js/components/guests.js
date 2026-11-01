/**
 * PlanGenius AI - Guest Estimator & Table/Shift Allocator Component
 */

const GuestsComponent = {
  render(event) {
    const container = document.getElementById("tab-guests");
    if (!container) return;

    const total = event.guestCount || 100;
    const isCommunity = event.eventType === "community";

    const attending = Math.round(total * 0.78);
    const declined = Math.round(total * 0.12);
    const pending = total - attending - declined;

    // Table calculation for weddings/birthdays: usually 8 or 10 per table
    const tableSize = 8;
    const estimatedTables = Math.ceil(attending / tableSize);

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">${getIcon('users')} ${isCommunity ? 'Attendance & Volunteer Estimator' : 'Guest & Table Seating Estimator'}</h2>
            <p class="card-description">Model RSVP projections, dietary requirements, and ${isCommunity ? 'volunteer shifts' : 'table capacity'}.</p>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="App.openCopilotWithPrompt('What is the typical RSVP drop-off rate and how should I buffer my catering count?')">
            ${getIcon('sparkles')} RSVP Best Practices
          </button>
        </div>

        <!-- RSVP KPI Breakdown -->
        <div class="kpi-grid" style="margin-top: 0; padding-top: 0; border-top: none; margin-bottom: 1.5rem;">
          <div class="kpi-card">
            <span class="kpi-label">Target Capacity</span>
            <span class="kpi-value">${total}</span>
            <span class="kpi-sub">Total planned attendees</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">Expected Attending</span>
            <span class="kpi-value" style="color: #10B981;">~${attending}</span>
            <span class="kpi-sub">78% typical acceptance model</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">Expected Regrets</span>
            <span class="kpi-value" style="color: #EF4444;">~${declined}</span>
            <span class="kpi-sub">12% estimated declines</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">${isCommunity ? 'Volunteers Needed' : 'Estimated Tables'}</span>
            <span class="kpi-value" style="color: #60A5FA;">${isCommunity ? Math.max(12, Math.round(total * 0.08)) : estimatedTables}</span>
            <span class="kpi-sub">${isCommunity ? 'Coordinators & staff' : `${tableSize} guests per round table`}</span>
          </div>
        </div>

        <!-- Breakdown Details -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.25rem;">
          <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1.25rem;">
            <h3 style="font-size: 0.95rem; font-weight: 600; color: var(--text-main); margin-bottom: 0.75rem;">
              Dietary & Meal Allocations
            </h3>
            <div style="display: flex; flex-direction: column; gap: 0.6rem; font-size: 0.85rem;">
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-muted);">Standard Entrees:</span>
                <span style="font-weight: 600;">~${Math.round(attending * 0.70)} guests</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-muted);">Vegetarian / Plant-based:</span>
                <span style="font-weight: 600;">~${Math.round(attending * 0.20)} guests</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-muted);">Gluten-Free / Allergy Specific:</span>
                <span style="font-weight: 600;">~${Math.round(attending * 0.10)} guests</span>
              </div>
            </div>
            <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color); font-size: 0.8rem; color: var(--text-muted);">
              <strong>Planner Tip:</strong> Final catering numbers are typically due 14 to 21 days prior to event day.
            </div>
          </div>

          <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1.25rem;">
            <h3 style="font-size: 0.95rem; font-weight: 600; color: var(--text-main); margin-bottom: 0.75rem;">
              ${isCommunity ? 'Volunteer Shift Roster' : 'Table Layout Overview'}
            </h3>
            <p style="font-size: 0.85rem; color: var(--text-sub); line-height: 1.45; margin-bottom: 0.75rem;">
              ${isCommunity 
                ? 'Recommended shifts: Shift 1 (Load-in & Setup 7:30am-11am), Shift 2 (Festival Operations & Guest Greeters 11am-3pm), Shift 3 (Afternoon Activities & Teardown 3pm-7pm).' 
                : `Plan for approximately ${estimatedTables} round banquet tables with 1 sweetheart / head table. Ensure 60 inches of clearance between tables for catering staff accessibility.`}
            </p>
            <button class="btn btn-secondary btn-sm" onclick="App.openCopilotWithPrompt('${isCommunity ? 'Help me draft volunteer role descriptions for our community event' : 'Give me tips on organizing an effortless wedding seating chart'}')">
              ${getIcon('sparkles')} Get Layout Advice
            </button>
          </div>
        </div>
      </div>
    `;
  }
};
