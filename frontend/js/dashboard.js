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
  expenses: []
};

/**
 * Initialize Dashboard
 */
document.addEventListener('DOMContentLoaded', async () => {
  setupSidebar();
  setupFilterListeners();
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

    if (expenses.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-8 text-muted">
            <i class="fa-solid fa-folder-open text-2xl mb-2 block"></i>
            No matching expenses found for this filter.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = expenses.map(item => {
      const riskClass = item.riskLevel === 'High' ? 'badge-high' :
                        item.riskLevel === 'Medium' ? 'badge-medium' : 'badge-low';

      const statusClass = item.status === 'approved' ? 'status-approved' :
                          item.status === 'rejected' ? 'status-rejected' :
                          item.status === 'flagged' ? 'status-flagged' : 'status-pending';

      const reasonsTooltip = (item.reasons || []).join(' • ');

      return `
        <tr id="row-${item.id}" class="expense-row">
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
          <td class="text-center">
            <div class="action-buttons">
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