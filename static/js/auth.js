/**
 * FreshMart Grocery E-Commerce - Authentication JavaScript
 * Handles Customer Registration, Customer Login, Admin Login, and Logout flows.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Helper to get URL query parameter
  function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
  }

  // ==========================================================================
  // Customer Registration
  // ==========================================================================
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errorEl = document.getElementById('registerError');
      const submitBtn = registerForm.querySelector('button[type="submit"]');

      if (errorEl) errorEl.style.display = 'none';

      const fullName = document.getElementById('fullName').value.trim();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirmPassword').value;

      if (!fullName || !email || !password || !confirmPassword) {
        if (errorEl) {
          errorEl.textContent = 'Please fill out all registration fields.';
          errorEl.style.display = 'block';
        }
        return;
      }

      if (password !== confirmPassword) {
        if (errorEl) {
          errorEl.textContent = 'Passwords do not match.';
          errorEl.style.display = 'block';
        }
        return;
      }

      if (password.length < 6) {
        if (errorEl) {
          errorEl.textContent = 'Password must be at least 6 characters long.';
          errorEl.style.display = 'block';
        }
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Creating Account...';

      try {
        await apiFetch('/api/auth/register', {
          method: 'POST',
          body: {
            full_name: fullName,
            email: email,
            password: password,
            confirm_password: confirmPassword
          }
        });

        showToast('Registration successful! Welcome to FreshMart.', 'success');
        const nextUrl = getQueryParam('next') || '/';
        setTimeout(() => {
          window.location.href = nextUrl;
        }, 800);
      } catch (err) {
        if (errorEl) {
          errorEl.textContent = err.message || 'Registration failed. Please try again.';
          errorEl.style.display = 'block';
        }
        showToast(err.message || 'Registration failed.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Account';
      }
    });
  }

  // ==========================================================================
  // Customer Login
  // ==========================================================================
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errorEl = document.getElementById('loginError');
      const submitBtn = loginForm.querySelector('button[type="submit"]');

      if (errorEl) errorEl.style.display = 'none';

      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;

      if (!email || !password) {
        if (errorEl) {
          errorEl.textContent = 'Please enter your email and password.';
          errorEl.style.display = 'block';
        }
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Signing In...';

      try {
        await apiFetch('/api/auth/login', {
          method: 'POST',
          body: { email, password }
        });

        showToast('Login successful! Welcome back.', 'success');
        const nextUrl = getQueryParam('next') || '/';
        setTimeout(() => {
          window.location.href = nextUrl;
        }, 800);
      } catch (err) {
        if (errorEl) {
          errorEl.textContent = err.message || 'Invalid email or password.';
          errorEl.style.display = 'block';
        }
        showToast(err.message || 'Invalid email or password.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign In';
      }
    });
  }

  // ==========================================================================
  // Admin Login
  // ==========================================================================
  const adminLoginForm = document.getElementById('adminLoginForm');
  if (adminLoginForm) {
    adminLoginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errorEl = document.getElementById('adminLoginError');
      const submitBtn = adminLoginForm.querySelector('button[type="submit"]');

      if (errorEl) errorEl.style.display = 'none';

      const usernameOrEmail = document.getElementById('adminUsername').value.trim();
      const password = document.getElementById('adminPassword').value;

      if (!usernameOrEmail || !password) {
        if (errorEl) {
          errorEl.textContent = 'Please enter admin username and password.';
          errorEl.style.display = 'block';
        }
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Authenticating Admin...';

      try {
        await apiFetch('/api/auth/admin/login', {
          method: 'POST',
          body: {
            username_or_email: usernameOrEmail,
            password: password
          }
        });

        showToast('Admin authorized! Redirecting to Dashboard...', 'success');
        setTimeout(() => {
          window.location.href = '/admin/dashboard';
        }, 800);
      } catch (err) {
        if (errorEl) {
          errorEl.textContent = err.message || 'Invalid admin credentials.';
          errorEl.style.display = 'block';
        }
        showToast(err.message || 'Invalid administrator credentials.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign In to Admin Portal';
      }
    });
  }

  // ==========================================================================
  // Logout Functionality
  // ==========================================================================
  document.querySelectorAll('[data-action="logout"]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        await apiFetch('/api/auth/logout', { method: 'POST' });
        showToast('You have been logged out.', 'info');
        setTimeout(() => {
          window.location.href = '/';
        }, 600);
      } catch (err) {
        window.location.href = '/';
      }
    });
  });
});
