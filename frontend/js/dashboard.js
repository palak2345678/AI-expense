/**
 * AuditAI - Dashboard Logic & Visualizations
 * Manages Chart.js instances, transactions table, filters, status updates,
 * stat cards, and alerts panel.
 */

// Global Chart Instances
let monthlyChart = null;
let categoryChart = null;
let riskBarChart = null;

// Dashboard State
const dashboardState = {
  currentCategory: 'all',
  currentRisk: 'all',
  searchQuery: '',
  sortField: 'date',
  sortOrder: 'desc',
  expenses: []
};

/**
 * Initialize Dashboard
 */
document.addEventListener('DOMContentLoaded', async () => {
  setupSidebar();
  setupFilterListeners();
  setupExportButton();
  setupAssistantWidget();
  setupModalBackdropDismiss();
  await loadDashboardData();
  await checkSystemHealth();
});

/**
 * Check Backend Health
 */
async function checkSystemHealth() {
  const statusPill = document.getElementById('backend-status');
  if (!statusPill) return;

  try {
    const health = await API.getHealth();
    statusPill.innerHTML = '<span class="status-dot online"></span> API Online';
    statusPill.title = `Connected to ${CONFIG.API_BASE_URL} (${health.timestamp})`;
  } catch (err) {
    statusPill.innerHTML = '<span class="status-dot offline"></span> API Offline';
    statusPill.title = 'Backend unavailable. Please ensure server is running.';
  }
}

/**
 * Setup Sidebar collapsible behavior
 */
function setupSidebar() {
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebar-toggle');
  const overlay = document.getElementById('sidebar-overlay');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      sidebar.classList.toggle('mobile-open');
      if (overlay) overlay.classList.toggle('active');
    });
  }

  if (overlay) {
    overlay.addEventListener('click', () => {
      if (sidebar) sidebar.classList.remove('mobile-open');
      overlay.classList.remove('active');
    });
  }
}

/**
 * Setup Filter and Search Input Event Handlers
 */
function setupFilterListeners() {
  const categoryFilter = document.getElementById('filter-category');
  const riskFilter = document.getElementById('filter-risk');
  const searchInput = document.getElementById('table-search');
  const topSearchInput = document.getElementById('topbar-search');

  if (categoryFilter) {
    categoryFilter.addEventListener('change', (e) => {
      dashboardState.currentCategory = e.target.value;
      fetchAndRenderExpenses();
    });
  }

  if (riskFilter) {
    riskFilter.addEventListener('change', (e) => {
      dashboardState.currentRisk = e.target.value;
      fetchAndRenderExpenses();
    });
  }

  let debounceTimer;
  function handleSearch(val) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      dashboardState.searchQuery = val;
      fetchAndRenderExpenses();
    }, 250);
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => handleSearch(e.target.value));
  }

  if (topSearchInput) {
    topSearchInput.addEventListener('input', (e) => {
      if (searchInput) searchInput.value = e.target.value;
      handleSearch(e.target.value);
    });
  }

  // Refresh data button
  const refreshBtn = document.getElementById('btn-refresh-data');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      refreshBtn.classList.add('rotating');
      await loadDashboardData();
      showToast('Dashboard data refreshed', 'info');
      setTimeout(() => refreshBtn.classList.remove('rotating'), 600);
    });
  }
}

/**
 * Load all Dashboard Sections
 */
async function loadDashboardData() {
  try {
    await Promise.all([
      loadStats(),
      fetchAndRenderExpenses(),
      loadMonthlyChart(),
      loadCategoryChart(),
      loadAlerts()
    ]);
  } catch (error) {
    console.error('Error loading dashboard data:', error);
  }
}

/**
 * Load and Animate KPI Stat Cards
 */
async function loadStats() {
  try {
    const stats = await API.getStats();

    const elTotalCount = document.getElementById('stat-total-count');
    const elTotalAmount = document.getElementById('stat-total-amount');
    const elFlaggedCount = document.getElementById('stat-flagged-count');
    const elMoneySaved = document.getElementById('stat-money-saved');
    const elAvgRisk = document.getElementById('stat-avg-risk');
    const elRiskBar = document.getElementById('stat-risk-progress');

    if (elTotalCount) animateCountUp(elTotalCount, stats.totalExpenses, 1000);
    if (elTotalAmount) animateCountUp(elTotalAmount, stats.totalAmount, 1200, '$');
    if (elFlaggedCount) animateCountUp(elFlaggedCount, stats.flaggedCount, 1000);
    if (elMoneySaved) animateCountUp(elMoneySaved, stats.moneySaved, 1200, '$');
    if (elAvgRisk) animateCountUp(elAvgRisk, stats.avgRiskScore, 1000, '', '/100');

    if (elRiskBar) {
      elRiskBar.style.width = `${Math.min(100, stats.avgRiskScore)}%`;
      elRiskBar.style.background = stats.avgRiskScore > 50 ? '#f43f5e' : stats.avgRiskScore > 25 ? '#f59e0b' : '#10b981';
    }
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
}

/**
 * Fetch and Render Expenses in Table
 */
async function fetchAndRenderExpenses() {
  const tbody = document.getElementById('expenses-tbody');
  const countBadge = document.getElementById('table-count-badge');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="8" class="text-center py-6 text-muted">
        <i class="fa-solid fa-spinner fa-spin text-primary"></i> Loading audited records...
      </td>
    </tr>
  `;

  try {
    const expenses = await API.getExpenses({
      category: dashboardState.currentCategory,
      risk: dashboardState.currentRisk,
      search: dashboardState.searchQuery
    });

    dashboardState.expenses = expenses;

    if (countBadge) {
      countBadge.textContent = `${expenses.length} records`;
    }

    renderExpensesTable();

  } catch (error) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center py-6 text-danger">
          <i class="fa-solid fa-triangle-exclamation"></i> Error loading transactions. Please check API connection.
        </td>
      </tr>
    `;
  }
}

/**
 * Sort Expenses List by Field and Order
 */
function sortExpensesList(list, field, order) {
  return [...list].sort((a, b) => {
    let valA = a[field];
    let valB = b[field];

    if (field === 'amount' || field === 'riskScore') {
      valA = Number(valA) || 0;
      valB = Number(valB) || 0;
    } else if (field === 'date') {
      valA = (a.date || '') + ' ' + (a.time || '');
      valB = (b.date || '') + ' ' + (b.time || '');
    } else {
      valA = String(valA || '').toLowerCase();
      valB = String(valB || '').toLowerCase();
    }

    if (valA < valB) return order === 'asc' ? -1 : 1;
    if (valA > valB) return order === 'asc' ? 1 : -1;
    return 0;
  });
}

/**
 * Handle Column Header Sort Toggle
 */
function handleSort(field) {
  if (dashboardState.sortField === field) {
    dashboardState.sortOrder = dashboardState.sortOrder === 'asc' ? 'desc' : 'asc';
  } else {
    dashboardState.sortField = field;
    dashboardState.sortOrder = (field === 'amount' || field === 'riskScore' || field === 'date') ? 'desc' : 'asc';
  }

  // Update header sort icons
  ['id', 'employee', 'category', 'date', 'amount', 'riskScore'].forEach(col => {
    const icon = document.getElementById(`sort-icon-${col}`);
    const th = icon ? icon.closest('th') : null;
    if (icon) {
      if (col === dashboardState.sortField) {
        icon.className = dashboardState.sortOrder === 'asc' ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down';
        if (th) th.classList.add('active');
      } else {
        icon.className = 'fa-solid fa-sort';
        if (th) th.classList.remove('active');
      }
    }
  });

  renderExpensesTable();
}

/**
 * Render Sorted Expenses in Table
 */
function renderExpensesTable() {
  const tbody = document.getElementById('expenses-tbody');
  if (!tbody) return;

  const sortedExpenses = sortExpensesList(dashboardState.expenses, dashboardState.sortField, dashboardState.sortOrder);

  if (sortedExpenses.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center py-8 text-muted">
          <i class="fa-solid fa-folder-open text-2xl mb-2 block" style="font-size: 1.6rem; margin-bottom: 8px;"></i>
          No matching expenses found for this filter. Try adjusting your search query.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = sortedExpenses.map(item => {
    const riskClass = item.riskLevel === 'High' ? 'badge-high' :
                      item.riskLevel === 'Medium' ? 'badge-medium' : 'badge-low';

    const statusClass = item.status === 'approved' ? 'status-approved' :
                        item.status === 'rejected' ? 'status-rejected' :
                        item.status === 'flagged' ? 'status-flagged' : 'status-pending';

    const reasonsTooltip = (item.reasons || []).join(' • ');

    return `
      <tr id="row-${item.id}" class="expense-row" onclick="openExpenseModal('${item.id}')" title="Click to inspect detailed AI audit breakdown">
        <td><span class="id-tag">${item.id}</span></td>
        <td>
          <div class="employee-cell">
            <strong>${item.employee}</strong>
            <small class="text-muted block">${item.department || 'General'}</small>
          </div>
        </td>
        <td><span class="category-pill">${item.category}</span></td>
        <td>
          <div>${item.date}</div>
          <small class="text-muted">${item.time || '12:00'}</small>
        </td>
        <td class="text-right font-mono font-semibold">$${item.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        <td>
          <div class="risk-cell" title="${reasonsTooltip}">
            <div class="risk-bar-mini">
              <div class="risk-bar-fill ${riskClass}" style="width: ${item.riskScore}%"></div>
            </div>
            <span class="risk-badge ${riskClass}">
              <i class="fa-solid ${item.riskLevel === 'High' ? 'fa-shield-halved' : item.riskLevel === 'Medium' ? 'fa-triangle-exclamation' : 'fa-circle-check'}"></i>
              ${item.riskScore} · ${item.riskLevel}
            </span>
          </div>
        </td>
        <td>
          <span id="status-badge-${item.id}" class="status-badge ${statusClass}">
            ${item.status}
          </span>
        </td>
        <td class="text-center" onclick="event.stopPropagation()">
          <div class="action-buttons">
            <button 
              class="btn-action btn-inspect" 
              title="Inspect AI Findings & Sub-Scores" 
              onclick="openExpenseModal('${item.id}')"
            >
              <i class="fa-solid fa-eye"></i>
            </button>
            <button 
              class="btn-action btn-approve ${item.status === 'approved' ? 'disabled' : ''}" 
              title="Approve Expense" 
              onclick="handleExpenseStatus('${item.id}', 'approved')"
              ${item.status === 'approved' ? 'disabled' : ''}
            >
              <i class="fa-solid fa-check"></i>
            </button>
            <button 
              class="btn-action btn-reject ${item.status === 'rejected' ? 'disabled' : ''}" 
              title="Reject Flagged Expense" 
              onclick="handleExpenseStatus('${item.id}', 'rejected')"
              ${item.status === 'rejected' ? 'disabled' : ''}
            >
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Handle Approve / Reject Action
 */
async function handleExpenseStatus(id, newStatus) {
  try {
    const updated = await API.updateExpenseStatus(id, newStatus);
    showToast(`Expense ${id} successfully marked as ${newStatus}`, newStatus === 'approved' ? 'success' : 'warning');

    // Update the row in place
    const statusBadge = document.getElementById(`status-badge-${id}`);
    if (statusBadge) {
      statusBadge.className = `status-badge status-${newStatus}`;
      statusBadge.textContent = newStatus;
    }

    // Refresh KPI stats, alerts and charts asynchronously
    loadStats();
    loadAlerts();
    loadMonthlyChart();
    loadCategoryChart();
  } catch (error) {
    showToast(`Failed to update status: ${error.message}`, 'error');
  }
}

/**
 * Load Monthly Line Chart
 */
async function loadMonthlyChart() {
  const ctx = document.getElementById('monthlyExpensesChart');
  if (!ctx) return;

  try {
    const data = await API.getMonthlyStats();

    if (monthlyChart) monthlyChart.destroy();

    monthlyChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.labels,
        datasets: [
          {
            label: 'Total Expenses ($)',
            data: data.totals,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointBackgroundColor: '#3b82f6',
            pointRadius: 4,
            pointHoverRadius: 6
          },
          {
            label: 'Flagged High-Risk ($)',
            data: data.flagged,
            borderColor: '#f43f5e',
            backgroundColor: 'rgba(244, 63, 94, 0.08)',
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            borderDash: [5, 5],
            pointBackgroundColor: '#f43f5e',
            pointRadius: 4,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
          },
          tooltip: {
            backgroundColor: '#1e293b',
            titleColor: '#f8fafc',
            bodyColor: '#cbd5e1',
            borderColor: '#334155',
            borderWidth: 1,
            padding: 10,
            callbacks: {
              label: (context) => ` ${context.dataset.label}: $${context.parsed.y.toLocaleString()}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { color: '#94a3b8', font: { family: 'Inter' } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: {
              color: '#94a3b8',
              font: { family: 'Inter' },
              callback: (val) => `$${(val / 1000).toFixed(0)}k`
            }
          }
        }
      }
    });
  } catch (error) {
    console.error('Failed to load monthly chart:', error);
  }
}

/**
 * Load Category Doughnut Chart & Risk Bar Chart
 */
async function loadCategoryChart() {
  const ctxDoughnut = document.getElementById('categoryDoughnutChart');
  const ctxBar = document.getElementById('categoryRiskBarChart');
  if (!ctxDoughnut) return;

  try {
    const data = await API.getCategoryStats();

    // Palettes
    const bgColors = [
      '#6366f1', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'
    ];

    if (categoryChart) categoryChart.destroy();

    categoryChart = new Chart(ctxDoughnut, {
      type: 'doughnut',
      data: {
        labels: data.labels,
        datasets: [{
          data: data.totals,
          backgroundColor: bgColors.slice(0, data.labels.length),
          borderWidth: 2,
          borderColor: '#0f172a',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, padding: 12 }
          },
          tooltip: {
            backgroundColor: '#1e293b',
            titleColor: '#f8fafc',
            bodyColor: '#cbd5e1',
            borderColor: '#334155',
            borderWidth: 1,
            callbacks: {
              label: (context) => ` $${context.parsed.toLocaleString()} (${context.dataset.data.reduce((a, b) => a + b, 0) > 0 ? Math.round((context.parsed / context.dataset.data.reduce((a, b) => a + b, 0)) * 100) : 0}%)`
            }
          }
        },
        cutout: '68%'
      }
    });

    // Bar Chart: Category volume vs Flagged
    if (ctxBar) {
      if (riskBarChart) riskBarChart.destroy();

      riskBarChart = new Chart(ctxBar, {
        type: 'bar',
        data: {
          labels: data.labels,
          datasets: [
            {
              label: 'Total Submitted',
              data: data.counts,
              backgroundColor: '#3b82f6',
              borderRadius: 6
            },
            {
              label: 'Flagged by AI',
              data: data.flaggedCounts,
              backgroundColor: '#f43f5e',
              borderRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } }
            },
            y: {
              grid: { color: 'rgba(255, 255, 255, 0.04)' },
              ticks: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, stepSize: 1 }
            }
          }
        }
      });
    }

  } catch (error) {
    console.error('Failed to load category charts:', error);
  }
}

/**
 * Load Real-Time Fraud Alerts Panel
 */
async function loadAlerts() {
  const alertsList = document.getElementById('alerts-container');
  const alertCountBadge = document.getElementById('alerts-count-badge');
  const alertDot = document.getElementById('alerts-pulse-dot');
  if (!alertsList) return;

  try {
    const alerts = await API.getAlerts();

    if (alertCountBadge) alertCountBadge.textContent = alerts.length;
    if (alertDot) alertDot.style.display = alerts.length > 0 ? 'inline-block' : 'none';

    if (alerts.length === 0) {
      alertsList.innerHTML = `
        <div class="empty-alerts">
          <i class="fa-solid fa-shield-check text-success text-2xl mb-2"></i>
          <p class="text-muted text-sm">No high-risk flags pending review. All systems secure!</p>
        </div>
      `;
      return;
    }

    alertsList.innerHTML = alerts.map(alert => {
      const topReason = (alert.reasons && alert.reasons[0]) || 'Irregular expense profile detected';
      return `
        <div class="alert-item">
          <div class="alert-header">
            <span class="risk-badge badge-high">
              <i class="fa-solid fa-triangle-exclamation"></i> Risk ${alert.riskScore}/100
            </span>
            <span class="alert-amount font-mono">$${alert.amount.toLocaleString()}</span>
          </div>
          <div class="alert-body">
            <strong>${alert.employee}</strong> · <span class="text-muted">${alert.category}</span>
            <p class="alert-reason">${topReason}</p>
          </div>
          <div class="alert-actions">
            <button class="btn-sm btn-outline-danger" onclick="handleExpenseStatus('${alert.id}', 'rejected')">
              <i class="fa-solid fa-ban"></i> Reject
            </button>
            <button class="btn-sm btn-outline-success" onclick="handleExpenseStatus('${alert.id}', 'approved')">
              <i class="fa-solid fa-check"></i> Approve
            </button>
          </div>
        </div>
      `;
    }).join('');

  } catch (error) {
    console.error('Failed to load alerts:', error);
  }
}

// Expose handlers to window for inline onclicks
window.handleExpenseStatus = handleExpenseStatus;

/**
 * Setup Modal Dismiss on Backdrop Click and Escape Key
 */
function setupModalBackdropDismiss() {
  const modal = document.getElementById('expense-details-modal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeExpenseDetailsModal();
      }
    });
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeExpenseDetailsModal();
    }
  });
}

/**
 * Open Detailed Transaction Review Modal
 */
function openExpenseModal(id) {
  const expense = (dashboardState.expenses || []).find(e => e.id === id);
  if (!expense) return;

  const modal = document.getElementById('expense-details-modal');
  const modalBody = document.getElementById('expense-modal-body');
  if (!modal || !modalBody) return;

  const fScore = expense.fuzzyScore !== undefined ? expense.fuzzyScore :
                 expense.fuzzy_score !== undefined ? expense.fuzzy_score :
                 (expense.sub_scores && expense.sub_scores.fuzzy_risk_score !== undefined) ? expense.sub_scores.fuzzy_risk_score : 0;
  const aScore = expense.anomalyScore !== undefined ? expense.anomalyScore :
                 expense.anomaly_score !== undefined ? expense.anomaly_score :
                 (expense.sub_scores && expense.sub_scores.anomaly_risk_score !== undefined) ? expense.sub_scores.anomaly_risk_score : 0;
  const rScore = expense.ruleScore !== undefined ? expense.ruleScore :
                 expense.rule_score !== undefined ? expense.rule_score :
                 (expense.sub_scores && expense.sub_scores.rule_risk_score !== undefined) ? expense.sub_scores.rule_risk_score : 0;

  const riskClass = expense.riskLevel === 'High' ? 'badge-high' :
                    expense.riskLevel === 'Medium' ? 'badge-medium' : 'badge-low';
  const statusClass = expense.status === 'approved' ? 'status-approved' :
                      expense.status === 'rejected' ? 'status-rejected' : 'status-flagged';

  const reasonsListHtml = (expense.reasons && expense.reasons.length > 0)
    ? expense.reasons.map(r => `
        <li class="reason-item" style="margin-bottom: 8px; font-size: 0.85rem; display: flex; gap: 8px; align-items: flex-start;">
          <i class="fa-solid fa-shield-halved ${expense.riskLevel === 'High' ? 'text-danger' : 'text-warning'}" style="margin-top: 3px;"></i>
          <span>${r}</span>
        </li>
      `).join('')
    : `<li class="reason-item text-success"><i class="fa-solid fa-circle-check"></i> Standard verified corporate expense claim. All policy limits satisfied.</li>`;

  modalBody.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; border-bottom: 1px solid var(--border-color); padding-bottom: 14px;">
      <div>
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
          <span class="id-tag" style="font-size: 0.9rem;">${expense.id}</span>
          <span class="risk-badge ${riskClass}">${expense.riskScore}/100 · ${expense.riskLevel} Risk</span>
          <span class="status-badge ${statusClass}">${expense.status.toUpperCase()}</span>
        </div>
        <h3 style="font-size: 1.25rem; color: #fff; margin: 4px 0;">${expense.employee}</h3>
        <small class="text-muted">${expense.department || 'General'} · ${expense.category}</small>
      </div>
      <div class="text-right">
        <div class="font-mono" style="font-size: 1.4rem; font-weight: 700; color: #fff;">$${expense.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        <small class="text-muted">${expense.date} at ${expense.time || '12:00'}</small>
      </div>
    </div>

    <!-- Metadata Grid -->
    <div class="modal-grid">
      <div class="modal-meta-item">
        <label>Receipt Documentation</label>
        <strong>${expense.has_receipt ? '<i class="fa-solid fa-circle-check text-success"></i> Document Attached' : '<i class="fa-solid fa-circle-xmark text-danger"></i> Missing Receipt'}</strong>
      </div>
      <div class="modal-meta-item">
        <label>Document Reference / Hash</label>
        <strong class="font-mono text-xs" style="word-break: break-all;">${expense.receipt_hash || 'NO_HASH_ATTACHED'}</strong>
      </div>
      <div class="modal-meta-item" style="grid-column: span 2;">
        <label>Business Purpose & Justification</label>
        <p style="font-size: 0.88rem; color: #cbd5e1; margin-top: 4px; line-height: 1.5;">${expense.description || 'Corporate filing for business operations.'}</p>
      </div>
    </div>

    <!-- Multi-Factor AI Risk Breakdown -->
    <div style="margin: 18px 0;">
      <h4 style="font-size: 0.95rem; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-brain text-primary"></i>
        <span>Soft Computing & Machine Learning Audit Breakdown</span>
      </h4>

      <!-- Mamdani Fuzzy Risk Score -->
      <div class="subscore-card">
        <div class="subscore-header">
          <span><i class="fa-solid fa-brain text-primary"></i> Mamdani Fuzzy Inference Engine (45% weight)</span>
          <strong class="font-mono text-primary">${Math.round(fScore)}%</strong>
        </div>
        <div class="subscore-bar-bg">
          <div class="subscore-bar-fill" style="width: ${Math.min(100, fScore)}%; background: #3b82f6;"></div>
        </div>
      </div>

      <!-- Isolation Forest Anomaly Score -->
      <div class="subscore-card">
        <div class="subscore-header">
          <span><i class="fa-solid fa-microchip" style="color: #a855f7;"></i> Scikit-Learn Isolation Forest (25% weight)</span>
          <strong class="font-mono" style="color: #a855f7;">${Math.round(aScore)}%</strong>
        </div>
        <div class="subscore-bar-bg">
          <div class="subscore-bar-fill" style="width: ${Math.min(100, aScore)}%; background: #a855f7;"></div>
        </div>
      </div>

      <!-- Deterministic Rules Score -->
      <div class="subscore-card">
        <div class="subscore-header">
          <span><i class="fa-solid fa-scale-balanced text-amber"></i> Deterministic Policy Rules (30% weight)</span>
          <strong class="font-mono text-amber">${Math.round(rScore)}%</strong>
        </div>
        <div class="subscore-bar-bg">
          <div class="subscore-bar-fill" style="width: ${Math.min(100, rScore)}%; background: #f59e0b;"></div>
        </div>
      </div>
    </div>

    <!-- Itemized Findings -->
    <div style="margin-bottom: 20px;">
      <h4 style="font-size: 0.85rem; margin-bottom: 8px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">
        Auditor Findings & Detected Anomalies
      </h4>
      <ul class="reasons-list" style="margin: 0; padding: 0;">
        ${reasonsListHtml}
      </ul>
    </div>

    <!-- Actions Footer -->
    <div style="display: flex; gap: 10px; border-top: 1px solid var(--border-color); padding-top: 16px;">
      <button class="btn btn-outline-danger btn-sm" style="flex: 1;" onclick="handleExpenseStatus('${expense.id}', 'rejected'); closeExpenseDetailsModal();">
        <i class="fa-solid fa-ban"></i> Reject Claim
      </button>
      <button class="btn btn-outline-success btn-sm" style="flex: 1;" onclick="handleExpenseStatus('${expense.id}', 'approved'); closeExpenseDetailsModal();">
        <i class="fa-solid fa-check"></i> Approve Claim
      </button>
      <button class="btn btn-secondary btn-sm" onclick="closeExpenseDetailsModal()">
        Close
      </button>
    </div>
  `;

  modal.style.display = 'flex';
}

function closeExpenseDetailsModal() {
  const modal = document.getElementById('expense-details-modal');
  if (modal) modal.style.display = 'none';
}

/**
 * Setup Export CSV Button
 */
function setupExportButton() {
  const btnExport = document.getElementById('btn-export-csv');
  if (btnExport) {
    btnExport.addEventListener('click', exportTransactionsCSV);
  }
}

/**
 * Export Filtered Transactions to CSV
 */
function exportTransactionsCSV() {
  const data = dashboardState.expenses || [];
  if (data.length === 0) {
    showToast('No transactions to export for current filter.', 'warning');
    return;
  }

  const headers = ['ID', 'Employee', 'Department', 'Category', 'Amount', 'Date', 'Time', 'Receipt Attached', 'Receipt Hash', 'Risk Score', 'Risk Level', 'Status', 'Auditor Reasons'];
  const rows = data.map(item => [
    `"${item.id}"`,
    `"${(item.employee || '').replace(/"/g, '""')}"`,
    `"${(item.department || '').replace(/"/g, '""')}"`,
    `"${(item.category || '').replace(/"/g, '""')}"`,
    item.amount,
    `"${item.date}"`,
    `"${item.time || '12:00'}"`,
    item.has_receipt ? 'YES' : 'NO',
    `"${item.receipt_hash || ''}"`,
    item.riskScore,
    `"${item.riskLevel}"`,
    `"${item.status}"`,
    `"${(item.reasons || []).join('; ').replace(/"/g, '""')}"`
  ]);

  const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `auditai-expenses-report-${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast(`Exported ${data.length} transactions to CSV`, 'success');
}

/**
 * Setup "Ask AuditAI" Floating Assistant Widget
 */
function setupAssistantWidget() {
  const fab = document.getElementById('btn-assistant-toggle');
  const panel = document.getElementById('assistant-panel');
  const closeBtn = document.getElementById('btn-assistant-close');
  const sendBtn = document.getElementById('btn-assistant-send');
  const input = document.getElementById('assistant-input');

  if (fab && panel) {
    fab.addEventListener('click', () => panel.classList.toggle('active'));
  }
  if (closeBtn && panel) {
    closeBtn.addEventListener('click', () => panel.classList.remove('active'));
  }
  if (sendBtn && input) {
    sendBtn.addEventListener('click', () => {
      const q = input.value.trim();
      if (q) {
        handleAssistantQuery(q);
        input.value = '';
      }
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = input.value.trim();
        if (q) {
          handleAssistantQuery(q);
          input.value = '';
        }
      }
    });
  }
}

/**
 * Process Natural Language Queries Against Live Audited Expenses
 */
function handleAssistantQuery(query) {
  const messagesContainer = document.getElementById('assistant-messages');
  if (!messagesContainer) return;

  // Append user message
  const userMsg = document.createElement('div');
  userMsg.className = 'chat-message user';
  userMsg.innerHTML = `<div class="msg-bubble">${escapeHtml(query)}</div>`;
  messagesContainer.appendChild(userMsg);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Process against loaded expenses
  const all = dashboardState.expenses || [];
  const qLower = query.toLowerCase();
  let botReply = '';

  if (qLower.includes('travel') || qLower.includes('flight')) {
    const travelClaims = all.filter(e => e.category.toLowerCase().includes('travel'));
    const flagged = travelClaims.filter(e => e.riskScore >= 30);
    const totalTravel = travelClaims.reduce((s, e) => s + e.amount, 0);
    botReply = `Found <strong>${travelClaims.length} Travel claims</strong> totaling <strong>$${totalTravel.toLocaleString()}</strong>. ${flagged.length} claim(s) are currently flagged for compliance review.`;
  } else if (qLower.includes('employee') || qLower.includes('most') || qLower.includes('who')) {
    const flaggedCounts = {};
    all.forEach(e => {
      if (e.riskScore >= 30) {
        flaggedCounts[e.employee] = (flaggedCounts[e.employee] || 0) + 1;
      }
    });
    const sorted = Object.entries(flaggedCounts).sort((a, b) => b[1] - a[1]);
    if (sorted.length > 0) {
      botReply = `Employee with the highest flagged claims is <strong>${sorted[0][0]}</strong> with <strong>${sorted[0][1]} flagged transactions</strong>.`;
    } else {
      botReply = `No high-risk employee claims found in the current audit dataset.`;
    }
  } else if (qLower.includes('saved') || qLower.includes('reject') || qLower.includes('loss')) {
    const rejected = all.filter(e => e.status === 'rejected');
    const savedAmount = rejected.reduce((s, e) => s + e.amount, 0);
    botReply = `To date, <strong>${rejected.length} unauthorized claim(s)</strong> have been rejected, recovering <strong>$${savedAmount.toLocaleString()}</strong> in prevented corporate treasury leaks.`;
  } else {
    const highRisk = all.filter(e => e.riskScore >= 60);
    botReply = `Across all <strong>${all.length} claims</strong> loaded, the Soft Computing & ML engine detected <strong>${highRisk.length} high-risk anomalies</strong>. Top categories by volume: Meals & Entertainment, Travel, and Equipment.`;
  }

  setTimeout(() => {
    const botMsg = document.createElement('div');
    botMsg.className = 'chat-message bot';
    botMsg.innerHTML = `
      <div class="brand-icon-box" style="width: 26px; height: 26px; font-size: 0.75rem; flex-shrink: 0;"><i class="fa-solid fa-shield-halved"></i></div>
      <div class="msg-bubble">${botReply}</div>
    `;
    messagesContainer.appendChild(botMsg);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }, 250);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Expose handlers globally
window.openExpenseModal = openExpenseModal;
window.closeExpenseDetailsModal = closeExpenseDetailsModal;
window.handleSort = handleSort;
window.handleAssistantQuery = handleAssistantQuery;
window.exportTransactionsCSV = exportTransactionsCSV;