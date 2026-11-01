/**
 * PlanGenius AI - Budget Management Component
 */

const BudgetComponent = {
  activeCategoryFilter: "all",

  render(event) {
    const container = document.getElementById("tab-budget");
    if (!container) return;

    const items = event.budgetItems || [];
    const curr = event.currency || "$";
    const totalBudget = Number(event.totalBudget) || 0;

    const totalAllocated = items.reduce((acc, it) => acc + (Number(it.estimated) || 0), 0);
    const totalSpent = items.reduce((acc, it) => acc + (Number(it.actual) || 0), 0);
    const remaining = totalBudget - totalSpent;
    const isOver = totalSpent > totalBudget;

    // Category breakdown
    const categories = {};
    items.forEach(it => {
      const cat = it.category || "General";
      if (!categories[cat]) categories[cat] = { estimated: 0, actual: 0, count: 0 };
      categories[cat].estimated += Number(it.estimated) || 0;
      categories[cat].actual += Number(it.actual) || 0;
      categories[cat].count += 1;
    });

    const filteredItems = this.activeCategoryFilter === "all"
      ? items
      : items.filter(it => (it.category || "General") === this.activeCategoryFilter);

    container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">${getIcon('dollar')} Smart Budget Tracker</h2>
            <p class="card-description">Track itemized estimates against actual deposits and vendor payments.</p>
          </div>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <button class="btn btn-primary btn-sm" onclick="BudgetComponent.openAddModal()">
              ${getIcon('plus')} Add Line Item
            </button>
            <button class="btn btn-secondary btn-sm" onclick="App.openCopilotWithPrompt('How can I optimize and reduce this budget without sacrificing quality?')">
              ${getIcon('sparkles')} AI Budget Advisor
            </button>
          </div>
        </div>

        <!-- Budget KPI Row -->
        <div class="kpi-grid" style="margin-top: 0; padding-top: 0; border-top: none; margin-bottom: 1.5rem;">
          <div class="kpi-card">
            <span class="kpi-label">Target Budget</span>
            <span class="kpi-value">${curr}${totalBudget.toLocaleString()}</span>
            <span class="kpi-sub">Total ceiling set for event</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">Total Allocated</span>
            <span class="kpi-value">${curr}${totalAllocated.toLocaleString()}</span>
            <span class="kpi-sub">${Math.round((totalAllocated / (totalBudget || 1)) * 100)}% of target planned</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">Total Paid & Deposited</span>
            <span class="kpi-value" style="color: ${isOver ? '#EF4444' : '#10B981'};">${curr}${totalSpent.toLocaleString()}</span>
            <span class="kpi-sub">${Math.round((totalSpent / (totalBudget || 1)) * 100)}% paid to vendors</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-label">Remaining Balance</span>
            <span class="kpi-value" style="color: ${remaining < 0 ? '#EF4444' : '#60A5FA'};">${curr}${remaining.toLocaleString()}</span>
            <span class="kpi-sub">${isOver ? '⚠️ Over budget!' : 'Available to spend'}</span>
          </div>
        </div>

        <!-- Category Progress Breakdown -->
        <div style="margin-bottom: 1.75rem;">
          <h3 style="font-size: 0.95rem; font-weight: 600; color: var(--text-sub); margin-bottom: 0.75rem;">Category Allocation & Progress</h3>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.85rem;">
            ${Object.entries(categories).map(([catName, data]) => {
              const pct = totalBudget ? Math.min(100, Math.round((data.actual / (data.estimated || totalBudget)) * 100)) : 0;
              return `
                <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 0.75rem 1rem;">
                  <div style="display: flex; justify-content: space-between; font-size: 0.825rem; font-weight: 600; margin-bottom: 0.35rem;">
                    <span>${catName}</span>
                    <span style="color: var(--text-muted);">${curr}${data.actual.toLocaleString()} / ${curr}${data.estimated.toLocaleString()}</span>
                  </div>
                  <div class="progress-bar-container">
                    <div class="progress-bar-fill fill-primary" style="width: ${pct}%;"></div>
                  </div>
                </div>
              `;
            }).join("")}
          </div>
        </div>

        <!-- Filter bar -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600;">Filter:</span>
            <button class="prompt-pill ${this.activeCategoryFilter === 'all' ? 'active' : ''}" onclick="BudgetComponent.setCategoryFilter('all')">All Items (${items.length})</button>
            ${Object.keys(categories).map(cat => `
              <button class="prompt-pill ${this.activeCategoryFilter === cat ? 'active' : ''}" onclick="BudgetComponent.setCategoryFilter('${cat}')">${cat} (${categories[cat].count})</button>
            `).join("")}
          </div>
          <span style="font-size: 0.8rem; color: var(--text-muted);">Showing ${filteredItems.length} expenses</span>
        </div>

        <!-- Line items table -->
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Expense Item</th>
                <th>Estimated</th>
                <th>Actual Paid</th>
                <th>Status</th>
                <th>Notes</th>
                <th style="text-align: right;">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filteredItems.length === 0 ? `
                <tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">No expenses match this category.</td></tr>
              ` : filteredItems.map(item => `
                <tr>
                  <td><span class="badge-subtype">${item.category || 'General'}</span></td>
                  <td class="cell-name">${item.name}</td>
                  <td class="cell-amount">${curr}${(Number(item.estimated) || 0).toLocaleString()}</td>
                  <td class="cell-amount" style="color: ${(Number(item.actual) || 0) > (Number(item.estimated) || 0) ? '#EF4444' : 'inherit'};">
                    ${curr}${(Number(item.actual) || 0).toLocaleString()}
                  </td>
                  <td>
                    <select class="form-control" style="padding: 0.2rem 0.4rem; font-size: 0.775rem; width: auto;" onchange="BudgetComponent.updateItemStatus('${item.id}', this.value)">
                      <option value="pending" ${item.status === 'pending' ? 'selected' : ''}>⏳ Pending</option>
                      <option value="deposit_paid" ${item.status === 'deposit_paid' ? 'selected' : ''}>💳 Deposit Paid</option>
                      <option value="paid" ${item.status === 'paid' ? 'selected' : ''}>✅ Paid in Full</option>
                    </select>
                  </td>
                  <td style="max-width: 250px; font-size: 0.8rem; color: var(--text-muted);">${item.notes || '-'}</td>
                  <td style="text-align: right; white-space: nowrap;">
                    <button class="btn btn-secondary btn-sm btn-icon-only" title="Edit" onclick="BudgetComponent.openEditModal('${item.id}')">${getIcon('edit')}</button>
                    <button class="btn btn-secondary btn-sm btn-icon-only" title="Delete" style="color: #EF4444;" onclick="BudgetComponent.deleteItem('${item.id}')">${getIcon('trash')}</button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  setCategoryFilter(cat) {
    this.activeCategoryFilter = cat;
    this.render(App.currentEvent);
  },

  async updateItemStatus(itemId, newStatus) {
    if (!App.currentEvent) return;
    const item = (App.currentEvent.budgetItems || []).find(it => it.id === itemId);
    if (item) {
      item.status = newStatus;
      await App.saveCurrentEvent(false);
      showToast("Budget item status updated", "info");
    }
  },

  openAddModal() {
    const modal = document.getElementById("modal-expense");
    if (!modal) return;
    document.getElementById("expense-form").reset();
    document.getElementById("expense-id").value = "";
    document.getElementById("modal-expense-title").innerText = "Add Budget Line Item";
    modal.classList.add("active");
  },

  openEditModal(itemId) {
    if (!App.currentEvent) return;
    const item = (App.currentEvent.budgetItems || []).find(it => it.id === itemId);
    if (!item) return;

    document.getElementById("expense-id").value = item.id;
    document.getElementById("expense-category").value = item.category || "Venue & Rentals";
    document.getElementById("expense-name").value = item.name || "";
    document.getElementById("expense-estimated").value = item.estimated || 0;
    document.getElementById("expense-actual").value = item.actual || 0;
    document.getElementById("expense-status").value = item.status || "pending";
    document.getElementById("expense-notes").value = item.notes || "";

    document.getElementById("modal-expense-title").innerText = "Edit Budget Line Item";
    document.getElementById("modal-expense").classList.add("active");
  },

  closeModal() {
    const modal = document.getElementById("modal-expense");
    if (modal) modal.classList.remove("active");
  },

  async saveExpenseFromModal() {
    if (!App.currentEvent) return;
    const id = document.getElementById("expense-id").value;
    const category = document.getElementById("expense-category").value.trim();
    const name = document.getElementById("expense-name").value.trim();
    const estimated = parseFloat(document.getElementById("expense-estimated").value) || 0;
    const actual = parseFloat(document.getElementById("expense-actual").value) || 0;
    const status = document.getElementById("expense-status").value;
    const notes = document.getElementById("expense-notes").value.trim();

    if (!name) {
      showToast("Please enter an expense name", "error");
      return;
    }

    if (!App.currentEvent.budgetItems) App.currentEvent.budgetItems = [];

    if (id) {
      const idx = App.currentEvent.budgetItems.findIndex(it => it.id === id);
      if (idx !== -1) {
        App.currentEvent.budgetItems[idx] = { id, category, name, estimated, actual, status, notes };
      }
    } else {
      const newId = "b_" + Date.now().toString(36);
      App.currentEvent.budgetItems.push({ id: newId, category, name, estimated, actual, status, notes });
    }

    this.closeModal();
    await App.saveCurrentEvent(true);
    showToast("Expense saved successfully", "success");
  },

  async deleteItem(itemId) {
    if (!App.currentEvent) return;
    if (!confirm("Are you sure you want to remove this expense line item?")) return;
    App.currentEvent.budgetItems = (App.currentEvent.budgetItems || []).filter(it => it.id !== itemId);
    await App.saveCurrentEvent(true);
    showToast("Expense removed", "info");
  }
};
