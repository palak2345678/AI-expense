/**
 * AuditAI - API Service Layer
 * Centralizes all fetch calls with loading indicators, error handling,
 * and cold-start detection for Render free-tier hosting.
 */

const API = {
  /**
   * Core HTTP request handler
   */
  async request(endpoint, options = {}) {
    const url = `${CONFIG.API_BASE_URL}${endpoint}`;
    
    // Default headers
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    // Show loading spinner if global spinner exists
    const spinner = document.getElementById('global-loader');
    if (spinner) spinner.classList.add('active');

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      const contentType = response.headers.get('content-type');
      let data = null;
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorMsg = (data && data.message) || (data && data.error) || `Request failed (${response.status})`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (error) {
      console.error(`API Error on ${endpoint}:`, error);

      // Display friendly error modal or toast
      if (typeof showToast === 'function') {
        const isColdStart = error.message.includes('Failed to fetch') || error.message.includes('NetworkError');
        const userNotice = isColdStart
          ? 'Backend is waking up (Render free tier takes ~30s on cold start). Please retry in a moment.'
          : error.message;
        showToast(userNotice, 'error');
      }

      throw error;
    } finally {
      if (spinner) spinner.classList.remove('active');
    }
  },

  /**
   * Health Check
   */
  async getHealth() {
    return this.request('/health');
  },

  /**
   * Fetch expenses list with optional filters
   */
  async getExpenses({ category = 'all', risk = 'all', search = '' } = {}) {
    const params = new URLSearchParams();
    if (category && category !== 'all') params.append('category', category);
    if (risk && risk !== 'all') params.append('risk', risk);
    if (search && search.trim() !== '') params.append('search', search.trim());

    const qs = params.toString() ? `?${params.toString()}` : '';
    return this.request(`/api/expenses${qs}`);
  },

  /**
   * Fetch aggregate stats (total, flagged, avg risk, savings)
   */
  async getStats() {
    return this.request('/api/stats');
  },

  /**
   * Fetch monthly spending and flagged losses for Line Chart
   */
  async getMonthlyStats() {
    return this.request('/api/stats/monthly');
  },

  /**
   * Fetch category breakdown for Doughnut Chart
   */
  async getCategoryStats() {
    return this.request('/api/stats/categories');
  },

  /**
   * Fetch high-risk alerts
   */
  async getAlerts() {
    return this.request('/api/alerts');
  },

  /**
   * Submit new expense for real-time AI risk evaluation
   */
  async createExpense(expenseData) {
    return this.request('/api/expenses', {
      method: 'POST',
      body: JSON.stringify(expenseData)
    });
  },

  /**
   * Update expense approval status (approved / rejected / flagged)
   */
  async updateExpenseStatus(id, status) {
    return this.request(`/api/expenses/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
  }
};