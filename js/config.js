/**
 * AuditAI - Configuration File
 * 
 * Automatically switches between local development (http://localhost:5001)
 * and production Render backend URL.
 * Update RENDER_BACKEND_URL with your actual Render deployment URL.
 */

const CONFIG = {
  // Live Render deployment URL
  RENDER_BACKEND_URL: 'https://ai-expense-1.onrender.com',

  // Dynamic API Base URL resolver
  get API_BASE_URL() {
    // If running directly on Render or locally, use origin
    if (window.location.hostname.includes('onrender.com') ||
        window.location.hostname.includes('vercel.app') === false && window.location.protocol.startsWith('http')) {
      return window.location.origin;
    }
    const isLocal = window.location.hostname === 'localhost' ||
                    window.location.hostname === '127.0.0.1' ||
                    window.location.protocol === 'file:';
    
    return isLocal ? 'http://localhost:5001' : this.RENDER_BACKEND_URL;
  }
};