/**
 * FreshMart Grocery E-Commerce - Main JavaScript
 * Handles global utilities, CSRF, Toast notifications, Cart counter, and API fetch wrapper.
 */

// Global state
window.FreshMart = window.FreshMart || {};

/**
 * Retrieves the active CSRF token from the meta tag or cookie.
 */
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta && meta.content) {
    return meta.content;
  }
  // Fallback to cookie
  const match = document.cookie.match(new RegExp('(^| )grocery_csrf=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : '';
}

/**
 * Formats a numerical value as Indian Rupee (₹).
 */
function formatINR(amount) {
  const num = parseFloat(amount) || 0;
  return '₹' + num.toFixed(2);
}

/**
 * Displays an animated floating toast notification.
 * @param {string} message - Message text
 * @param {'success'|'error'|'warning'|'info'} type - Toast theme
 */
function showToast(message, type = 'success') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type === 'error' ? 'toast-error' : type === 'warning' ? 'toast-warning' : ''}`;

  const icon = type === 'error' ? '⚠️' : type === 'warning' ? '⚡' : '✅';
  toast.innerHTML = `<span>${icon}</span><span style="flex:1;">${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

/**
 * Centralized fetch wrapper that automatically handles:
 * - JSON serialization
 * - CSRF headers on state-changing requests
 * - Credential cookies
 * - Standardized error extraction
 */
async function apiFetch(url, options = {}) {
  const opts = { ...options };
  opts.credentials = 'same-origin';
  opts.headers = { ...opts.headers };

  const method = (opts.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      opts.headers['X-CSRF-Token'] = csrfToken;
    }
  }

  if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }

  try {
    const response = await fetch(url, opts);
    let data = null;

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      let errorMsg = 'An unexpected error occurred.';
      if (data && typeof data === 'object') {
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            errorMsg = data.detail.map(e => e.msg || e.message).join(', ');
          } else {
            errorMsg = data.detail;
          }
        } else if (data.message) {
          errorMsg = data.message;
        }
      }
      const err = new Error(errorMsg);
      err.status = response.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (error) {
    throw error;
  }
}

/**
 * Updates the navbar cart badge across the site.
 */
function updateCartBadge(count) {
  const badges = document.querySelectorAll('.cart-badge');
  badges.forEach(badge => {
    badge.textContent = count;
    badge.style.display = count > 0 ? 'inline-block' : 'none';
  });
}

/**
 * Adds an item to the shopping cart.
 */
async function handleAddToCart(productId, btnElement) {
  if (!productId) return;

  const originalText = btnElement ? btnElement.innerHTML : '';
  if (btnElement) {
    btnElement.disabled = true;
    btnElement.innerHTML = 'Adding...';
  }

  try {
    const data = await apiFetch('/api/cart/items', {
      method: 'POST',
      body: { product_id: parseInt(productId), quantity: 1 }
    });

    updateCartBadge(data.total_items);
    showToast('Added to your grocery cart!', 'success');
  } catch (error) {
    if (error.status === 401) {
      showToast('Please log in to add items to your cart.', 'warning');
      setTimeout(() => {
        window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
      }, 1200);
    } else {
      showToast(error.message || 'Failed to add item to cart.', 'error');
    }
  } finally {
    if (btnElement) {
      btnElement.disabled = false;
      btnElement.innerHTML = originalText;
    }
  }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
  // Sync current user status if needed
  apiFetch('/api/auth/me')
    .then(status => {
      if (status.authenticated && status.csrf_token) {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) meta.content = status.csrf_token;
      }
    })
    .catch(() => {});
});
