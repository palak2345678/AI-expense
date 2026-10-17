/**
 * AuditAI - Live Expense Audit & Risk Engine Integration
 * Handles new expense submission, AI heuristic analysis loader,
 * circular risk gauge visualization, and instant dashboard synchronization.
 */

document.addEventListener('DOMContentLoaded', () => {
  setupAuditForm();
  setupQuickPresets();
  setDefaultDateTime();
});

/**
 * Set default date to today and time to now
 */
function setDefaultDateTime() {
  const dateInput = document.getElementById('audit-date');
  const timeInput = document.getElementById('audit-time');
  const now = new Date();

  if (dateInput && !dateInput.value) {
    dateInput.value = now.toISOString().split('T')[0];
  }

  if (timeInput && !timeInput.value) {
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    timeInput.value = `${hours}:${minutes}`;
  }
}

/**
 * Setup Quick-Fill Presets for Live Testing & Presentations
 */
function setupQuickPresets() {
  const presetButtons = document.querySelectorAll('.btn-preset');
  if (!presetButtons.length) return;

  const presets = {
    clean: {
      employee: 'Sarah Jenkins',
      department: 'Engineering',
      category: 'Meals & Entertainment',
      amount: 145.50,
      description: 'Team sprint celebration lunch with itemized receipt',
      date: '2026-10-14',
      time: '12:30'
    },
    duplicate: {
      employee: 'Alex Rivera',
      department: 'Sales',
      category: 'Meals & Entertainment',
      amount: 3200,
      description: 'VIP Client Dinner & Lounge reservation',
      date: '2026-10-15',
      time: '14:00'
    },
    highval: {
      employee: 'Marcus Vance',
      department: 'Executive',
      category: 'Equipment',
      amount: 16500,
      description: 'Executive portable workstation setup & audio monitors',
      date: '2026-10-18', // Sunday
      time: '23:45'
    },
    oddtime: {
      employee: 'David Chen',
      department: 'Consulting',
      category: 'Consulting',
      amount: 5000,
      description: 'Emergency offshore architectural consulting advisory',
      date: '2026-10-17', // Saturday
      time: '02:15'
    }
  };

  presetButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const presetKey = btn.dataset.preset;
      const data = presets[presetKey];
      if (!data) return;

      document.getElementById('audit-employee').value = data.employee;
      document.getElementById('audit-department').value = data.department;
      document.getElementById('audit-category').value = data.category;
      document.getElementById('audit-amount').value = data.amount;
      document.getElementById('audit-description').value = data.description;
      document.getElementById('audit-date').value = data.date;
      document.getElementById('audit-time').value = data.time;

      const rcptCheckbox = document.getElementById('audit-has-receipt');
      const rcptHashInput = document.getElementById('audit-receipt-hash');
      if (rcptCheckbox) {
        rcptCheckbox.checked = presetKey !== 'highval';
      }
      if (rcptHashInput) {
        rcptHashInput.value = presetKey === 'duplicate' ? 'HASH-9999-DUPLICATE' :
                              presetKey === 'clean' ? 'RCPT-CLEAN-1049' :
                              presetKey === 'highval' ? 'NO_RECEIPT' : 'RCPT-OFFSHORE-921';
      }

      showToast(`Loaded ${presetKey.toUpperCase()} test scenario`, 'info', 2500);
    });
  });
}

/**
 * Setup Audit Form submission
 */
function setupAuditForm() {
  const form = document.getElementById('expense-audit-form');
  const resultCard = document.getElementById('audit-result-card');
  const emptyState = document.getElementById('audit-empty-state');
  const submitBtn = document.getElementById('btn-submit-audit');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Extract form fields
    const employee = document.getElementById('audit-employee').value.trim();
    const department = document.getElementById('audit-department').value;
    const category = document.getElementById('audit-category').value;
    const amount = parseFloat(document.getElementById('audit-amount').value);
    const date = document.getElementById('audit-date').value;
    const time = document.getElementById('audit-time').value;
    const description = document.getElementById('audit-description').value.trim();
    const hasReceipt = document.getElementById('audit-has-receipt') ? document.getElementById('audit-has-receipt').checked : true;
    const receiptHash = document.getElementById('audit-receipt-hash') ? document.getElementById('audit-receipt-hash').value.trim() : '';

    if (!employee || isNaN(amount) || amount <= 0 || !category || !description) {
      showToast('Please fill out all required fields with a valid amount.', 'error');
      return;
    }

    // UI Feedback: "AI Analyzing..." state
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `
        <i class="fa-solid fa-brain fa-spin"></i>
        <span>Soft Computing & ML Audit Engine Running...</span>
      `;
    }

    // Temporary simulated processing pulse
    if (resultCard) {
      resultCard.classList.add('analyzing');
    }

    try {
      // Send to Backend Risk Engine API
      const evaluatedExpense = await API.createExpense({
        employee,
        department,
        category,
        amount,
        date,
        time,
        description,
        has_receipt: hasReceipt,
        receipt_hash: receiptHash
      });

      // Display Results Card
      if (emptyState) emptyState.style.display = 'none';
      if (resultCard) {
        resultCard.style.display = 'block';
        resultCard.classList.remove('analyzing');
      }

      // Populate Result Card
      renderAuditResult(evaluatedExpense);

      showToast(`Expense audited: Risk Score ${evaluatedExpense.riskScore}/100 (${evaluatedExpense.riskLevel})`, 
        evaluatedExpense.riskLevel === 'High' ? 'error' : evaluatedExpense.riskLevel === 'Medium' ? 'warning' : 'success'
      );

      // Refresh Dashboard stats, table, and charts automatically without page reload
      if (typeof loadDashboardData === 'function') {
        loadDashboardData();
      }

      // Reset form fields lightly (retain date/time for convenience)
      document.getElementById('audit-amount').value = '';
      document.getElementById('audit-description').value = '';

    } catch (error) {
      showToast(`Audit failed: ${error.message}`, 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `
          <i class="fa-solid fa-wand-magic-sparkles"></i>
          <span>Run AI Fraud Audit</span>
        `;
      }
    }
  });
}

/**
 * Render Evaluated Result with Animated SVG Gauge & Reasons List
 */
function renderAuditResult(expense) {
  // Animate Circular Gauge
  animateGauge(expense.riskScore, expense.riskLevel);

  // Set ID and summary
  const summaryEl = document.getElementById('result-summary-text');
  if (summaryEl) {
    summaryEl.innerHTML = `
      <strong>${expense.id}</strong> · <span class="font-mono">$${expense.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
      <div class="text-xs text-muted mt-1">${expense.employee} (${expense.department}) — ${expense.category}</div>
    `;
  }

  // Set status pill
  const statusEl = document.getElementById('result-status-pill');
  if (statusEl) {
    const statusClass = expense.status === 'flagged' ? 'status-flagged' :
                        expense.status === 'approved' ? 'status-approved' : 'status-pending';
    statusEl.className = `status-badge ${statusClass}`;
    statusEl.textContent = `Status: ${expense.status.toUpperCase()}`;
  }

  // Populate itemized reasons
  const reasonsList = document.getElementById('result-reasons-list');
  if (reasonsList) {
    let html = '';
    
    // Soft Computing & ML Sub-scores strip
    if (expense.fuzzyScore !== undefined || expense.fuzzy_score !== undefined || (expense.sub_scores && expense.sub_scores.fuzzy_risk_score !== undefined)) {
      const fScore = expense.fuzzyScore || expense.fuzzy_score || (expense.sub_scores && expense.sub_scores.fuzzy_risk_score) || 0;
      const aScore = expense.anomalyScore || expense.anomaly_score || (expense.sub_scores && expense.sub_scores.anomaly_risk_score) || 0;
      const rScore = expense.ruleScore || expense.rule_score || (expense.sub_scores && expense.sub_scores.rule_risk_score) || 0;

      html += `
        <li class="reason-item" style="background: rgba(255, 255, 255, 0.04); border-radius: 6px; padding: 6px 10px; margin-bottom: 8px;">
          <div style="display: flex; gap: 8px; flex-wrap: wrap; font-size: 0.78rem;">
            <span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #93c5fd; padding: 2px 6px; border-radius: 4px;">
              <i class="fa-solid fa-brain"></i> Fuzzy Logic: ${Math.round(fScore)}%
            </span>
            <span class="badge" style="background: rgba(168, 85, 247, 0.2); color: #d8b4fe; padding: 2px 6px; border-radius: 4px;">
              <i class="fa-solid fa-microchip"></i> ML Anomaly: ${Math.round(aScore)}%
            </span>
            <span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fcd34d; padding: 2px 6px; border-radius: 4px;">
              <i class="fa-solid fa-scale-balanced"></i> Audit Rules: ${Math.round(rScore)}%
            </span>
          </div>
        </li>
      `;
    }

    if (expense.nextAction || expense.next_action) {
      const action = expense.nextAction || expense.next_action;
      html += `
        <li class="reason-item" style="border-left: 3px solid #10b981; padding-left: 8px; margin-bottom: 8px;">
          <i class="fa-solid fa-gavel text-success"></i>
          <strong>Recommendation:</strong> <span style="color: #6ee7b7;">${action}</span>
        </li>
      `;
    }

    if (!expense.reasons || expense.reasons.length === 0) {
      html += `<li class="reason-item text-success"><i class="fa-solid fa-circle-check"></i> Standard verified corporate expenditure.</li>`;
    } else {
      html += expense.reasons.map(reason => {
        const isCritical = reason.includes('CRITICAL') || reason.includes('Duplicate') || reason.includes('Exceeded') || reason.includes('High transaction');
        const iconClass = isCritical ? 'fa-solid fa-triangle-exclamation text-danger' : 'fa-solid fa-circle-info text-warning';
        return `
          <li class="reason-item">
            <i class="${iconClass}"></i>
            <span>${reason}</span>
          </li>
        `;
      }).join('');
    }
    reasonsList.innerHTML = html;
  }

  // Quick Action Buttons inside result card
  const btnApprove = document.getElementById('btn-result-approve');
  const btnReject = document.getElementById('btn-result-reject');

  if (btnApprove) {
    btnApprove.onclick = () => handleExpenseStatus(expense.id, 'approved');
  }
  if (btnReject) {
    btnReject.onclick = () => handleExpenseStatus(expense.id, 'rejected');
  }
}