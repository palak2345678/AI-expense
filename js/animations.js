/**
 * AuditAI - Animations & Interactive Effects
 * Handles number count-ups, scroll reveals, circular gauge rendering,
 * and toast notification popups.
 */

/**
 * Animate numeric counter from 0 to target value
 */
function animateCountUp(element, target, duration = 1200, prefix = '', suffix = '') {
  if (!element) return;
  const start = 0;
  const isFloat = !Number.isInteger(target);
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Ease-out cubic formula
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = start + (target - start) * easeOut;

    if (isFloat) {
      element.textContent = `${prefix}${current.toFixed(1)}${suffix}`;
    } else {
      element.textContent = `${prefix}${Math.round(current).toLocaleString()}${suffix}`;
    }

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      if (isFloat) {
        element.textContent = `${prefix}${target.toFixed(1)}${suffix}`;
      } else {
        element.textContent = `${prefix}${Math.round(target).toLocaleString()}${suffix}`;
      }
    }
  }

  requestAnimationFrame(update);
}

/**
 * Reveal elements smoothly on scroll using IntersectionObserver
 */
function initScrollReveal() {
  const elements = document.querySelectorAll('.reveal');
  if (!elements.length) return;

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        obs.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.12,
    rootMargin: '0px 0px -40px 0px'
  });

  elements.forEach(el => observer.observe(el));
}

/**
 * Render & animate SVG Circular Gauge for Risk Score (0-100)
 */
function animateGauge(score, level) {
  const circle = document.getElementById('gauge-progress');
  const scoreText = document.getElementById('gauge-score-value');
  const levelBadge = document.getElementById('gauge-level-badge');
  
  if (!circle || !scoreText) return;

  // Circle radius is 54, circumference = 2 * PI * 54 = 339.292
  const circumference = 339.292;
  circle.style.strokeDasharray = `${circumference}`;

  // Color mapping based on risk level
  let strokeColor = '#10b981'; // Green for Low
  let bgGlow = 'rgba(16, 185, 129, 0.2)';
  let badgeClass = 'badge-low';

  if (score >= 60) {
    strokeColor = '#f43f5e'; // Red for High
    bgGlow = 'rgba(244, 63, 94, 0.25)';
    badgeClass = 'badge-high';
  } else if (score >= 30) {
    strokeColor = '#f59e0b'; // Amber for Medium
    bgGlow = 'rgba(245, 158, 11, 0.25)';
    badgeClass = 'badge-medium';
  }

  circle.style.stroke = strokeColor;
  circle.style.filter = `drop-shadow(0 0 10px ${strokeColor})`;

  if (levelBadge) {
    levelBadge.className = `risk-badge ${badgeClass}`;
    levelBadge.textContent = `${level} Risk (${score}/100)`;
  }

  // Animate stroke offset from full to target
  const offset = circumference - (score / 100) * circumference;
  circle.style.strokeDashoffset = `${circumference}`;

  // Trigger CSS transition
  setTimeout(() => {
    circle.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)';
    circle.style.strokeDashoffset = `${offset}`;
  }, 50);

  // Animate text number count
  animateCountUp(scoreText, score, 1000, '', '');
}

/**
 * Show temporary toast message
 */
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icon = type === 'success' ? 'fa-check-circle' :
               type === 'error' ? 'fa-exclamation-triangle' :
               type === 'warning' ? 'fa-shield-halved' : 'fa-info-circle';

  toast.innerHTML = `
    <i class="fa-solid ${icon}"></i>
    <div class="toast-content">${message}</div>
    <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
  `;

  container.appendChild(toast);

  // Auto remove after duration
  setTimeout(() => {
    toast.classList.add('fade-out');
    setTimeout(() => toast.remove(), 400);
  }, duration);
}

// Auto-initialize scroll reveal on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initScrollReveal();
});