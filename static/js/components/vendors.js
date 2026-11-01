/**
 * PlanGenius AI - Vendor Hub & Checklist Component
 */

const VendorsComponent = {
  activeStatusFilter: "all",
  activeCategoryFilter: "all",

  render(event) {
    const container = document.getElementById("tab-vendors");
    if (!container) return;

    const vendors = event.vendors || [];
    const curr = event.currency || "$";

    const bookedCount = vendors.filter(v => v.status === "booked" || v.status === "deposit_paid" || v.status === "completed").length;

    // Categories
    const categories = Array.from(new Set(vendors.map(v => v.category || "General")));

    // Filtered
    const filtered = vendors.filter(v => {
      const matchStatus = this.activeStatusFilter === "all" || v.status === this.activeStatusFilter;
      const matchCat = this.activeCategoryFilter === "all" || (v.category || "General") === this.activeCategoryFilter;
      return matchStatus && matchCat;
    });

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">${getIcon('users')} Vendor Hub & Checklist</h2>
            <p class="card-description">Manage vendor contracts, contact details, quotes, and generate AI inquiry emails.</p>
          </div>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <button class="btn btn-primary btn-sm" onclick="VendorsComponent.openAddModal()">
              ${getIcon('plus')} Add Vendor
            </button>
            <button class="btn btn-secondary btn-sm" onclick="App.openCopilotWithPrompt('What are key questions to ask when vetting event vendors?')">
              ${getIcon('sparkles')} AI Vendor Advisor
            </button>
          </div>
        </div>

        <!-- Filter bar -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem;">
          <div style="display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;">
            <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600;">Status:</span>
            <button class="prompt-pill ${this.activeStatusFilter === 'all' ? 'active' : ''}" onclick="VendorsComponent.setStatusFilter('all')">All (${vendors.length})</button>
            <button class="prompt-pill ${this.activeStatusFilter === 'booked' ? 'active' : ''}" onclick="VendorsComponent.setStatusFilter('booked')">Booked (${bookedCount})</button>
            <button class="prompt-pill ${this.activeStatusFilter === 'quoted' ? 'active' : ''}" onclick="VendorsComponent.setStatusFilter('quoted')">Quoted</button>
            <button class="prompt-pill ${this.activeStatusFilter === 'to_research' ? 'active' : ''}" onclick="VendorsComponent.setStatusFilter('to_research')">To Research</button>
          </div>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 0.8rem; color: var(--text-muted);">Category:</span>
            <select class="form-control" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;" onchange="VendorsComponent.setCategoryFilter(this.value)">
              <option value="all">All Categories</option>
              ${categories.map(c => `<option value="${c}" ${this.activeCategoryFilter === c ? 'selected' : ''}>${c}</option>`).join("")}
            </select>
          </div>
        </div>

        <!-- Vendor Cards Grid -->
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 1rem;">
          ${filtered.length === 0 ? `
            <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted); background: var(--bg-secondary); border-radius: var(--radius-md);">
              No vendors match the selected filter. Click "+ Add Vendor" to add one!
            </div>
          ` : filtered.map(v => `
            <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1.25rem; display: flex; flex-direction: column; justify-content: space-between; gap: 1rem;">
              <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem; gap: 0.5rem;">
                  <span class="badge-subtype">${v.category || 'General'}</span>
                  <select class="form-control" style="padding: 0.15rem 0.45rem; font-size: 0.75rem; width: auto;" onchange="VendorsComponent.updateStatus('${v.id}', this.value)">
                    <option value="to_research" ${v.status === 'to_research' ? 'selected' : ''}>🔍 To Research</option>
                    <option value="contacted" ${v.status === 'contacted' ? 'selected' : ''}>💬 Contacted</option>
                    <option value="quoted" ${v.status === 'quoted' ? 'selected' : ''}>📄 Quoted</option>
                    <option value="booked" ${v.status === 'booked' ? 'selected' : ''}>🤝 Booked</option>
                    <option value="deposit_paid" ${v.status === 'deposit_paid' ? 'selected' : ''}>💳 Deposit Paid</option>
                    <option value="completed" ${v.status === 'completed' ? 'selected' : ''}>✅ Completed</option>
                  </select>
                </div>

                <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.35rem;">
                  ${v.name}
                </h3>

                <div style="font-size: 0.85rem; color: var(--text-sub); display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem;">
                  ${v.contact ? `<div style="display: flex; align-items: center; gap: 0.4rem;">${getIcon('mail')} <a href="mailto:${v.contact}" style="color: #A5B4FC; text-decoration: none;">${v.contact}</a></div>` : ''}
                  ${v.phone ? `<div style="display: flex; align-items: center; gap: 0.4rem;">${getIcon('clock')} <span>${v.phone}</span></div>` : ''}
                </div>

                <div style="background: rgba(15, 23, 42, 0.4); padding: 0.6rem 0.8rem; border-radius: var(--radius-sm); font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                  <strong>Contract / Notes:</strong> ${v.notes || 'No contract notes yet.'}
                </div>
              </div>

              <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 0.75rem; border-top: 1px solid var(--border-color);">
                <div>
                  <span style="font-size: 0.75rem; color: var(--text-muted);">Quoted:</span>
                  <span style="font-weight: 700; color: var(--text-main); margin-left: 0.25rem;">${curr}${(Number(v.quoted) || 0).toLocaleString()}</span>
                </div>
                <div style="display: flex; gap: 0.35rem;">
                  <button class="btn btn-sparkle btn-sm" title="Generate AI inquiry email to this vendor" onclick="VendorsComponent.draftAiEmail('${v.id}')">
                    ${getIcon('sparkles')} Draft AI Email
                  </button>
                  <button class="btn btn-secondary btn-sm btn-icon-only" title="Delete" style="color: #EF4444;" onclick="VendorsComponent.deleteVendor('${v.id}')">
                    ${getIcon('trash')}
                  </button>
                </div>
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  },

  setStatusFilter(status) {
    this.activeStatusFilter = status;
    this.render(App.currentEvent);
  },

  setCategoryFilter(cat) {
    this.activeCategoryFilter = cat;
    this.render(App.currentEvent);
  },

  async updateStatus(id, newStatus) {
    if (!App.currentEvent) return;
    const v = (App.currentEvent.vendors || []).find(it => it.id === id);
    if (v) {
      v.status = newStatus;
      await App.saveCurrentEvent(false);
      showToast("Vendor status updated", "info");
    }
  },

  async draftAiEmail(vendorId) {
    if (!App.currentEvent) return;
    const v = (App.currentEvent.vendors || []).find(it => it.id === vendorId);
    if (!v) return;

    try {
      showToast("Drafting personalized inquiry email with AI...", "info");
      const res = await API.draftVendorEmail(v, App.currentEvent);
      if (res.success && res.email) {
        document.getElementById("email-modal-vendor-name").innerText = v.name;
        document.getElementById("email-modal-textarea").value = res.email;
        document.getElementById("modal-vendor-email").classList.add("active");
      }
    } catch (err) {
      showToast("Failed to draft email: " + err.message, "error");
    }
  },

  closeEmailModal() {
    document.getElementById("modal-vendor-email")?.classList.remove("active");
  },

  copyEmailDraft() {
    const text = document.getElementById("email-modal-textarea")?.value || "";
    navigator.clipboard.writeText(text).then(() => {
      showToast("Inquiry email copied to clipboard!", "success");
    });
  },

  openAddModal() {
    document.getElementById("vendor-form")?.reset();
    document.getElementById("vendor-id").value = "";
    document.getElementById("modal-vendor-title").innerText = "Add New Vendor";
    document.getElementById("modal-vendor")?.classList.add("active");
  },

  closeModal() {
    document.getElementById("modal-vendor")?.classList.remove("active");
  },

  async saveVendorFromModal() {
    if (!App.currentEvent) return;
    const id = document.getElementById("vendor-id")?.value;
    const name = document.getElementById("vendor-name")?.value.trim();
    const category = document.getElementById("vendor-category")?.value.trim() || "General";
    const contact = document.getElementById("vendor-contact")?.value.trim();
    const phone = document.getElementById("vendor-phone")?.value.trim();
    const status = document.getElementById("vendor-status")?.value || "to_research";
    const quoted = parseFloat(document.getElementById("vendor-quoted")?.value) || 0;
    const notes = document.getElementById("vendor-notes")?.value.trim();

    if (!name) {
      showToast("Please enter a vendor name", "error");
      return;
    }

    if (!App.currentEvent.vendors) App.currentEvent.vendors = [];

    if (id) {
      const idx = App.currentEvent.vendors.findIndex(v => v.id === id);
      if (idx !== -1) {
        App.currentEvent.vendors[idx] = { id, name, category, contact, phone, status, quoted, notes };
      }
    } else {
      const newId = "v_" + Date.now().toString(36);
      App.currentEvent.vendors.push({ id: newId, name, category, contact, phone, status, quoted, notes });
    }

    this.closeModal();
    await App.saveCurrentEvent(true);
    showToast("Vendor saved successfully", "success");
  },

  async deleteVendor(id) {
    if (!App.currentEvent) return;
    if (!confirm("Are you sure you want to remove this vendor?")) return;
    App.currentEvent.vendors = (App.currentEvent.vendors || []).filter(v => v.id !== id);
    await App.saveCurrentEvent(true);
    showToast("Vendor removed", "info");
  }
};
