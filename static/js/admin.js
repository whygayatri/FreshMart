/**
 * FreshMart Grocery E-Commerce - Admin Management JavaScript
 * Handles Admin Product CRUD operations, table filters, modal forms, and metrics.
 */

document.addEventListener('DOMContentLoaded', () => {
  const productModal = document.getElementById('productModal');
  const productForm = document.getElementById('productForm');
  const modalTitle = document.getElementById('modalTitle');
  const addProductBtn = document.getElementById('addProductBtn');
  const closeModalBtns = document.querySelectorAll('.close-modal');
  const adminSearchInput = document.getElementById('adminProductSearch');
  const adminCategoryFilter = document.getElementById('adminCategoryFilter');
  const productsTableBody = document.getElementById('adminProductsTableBody');

  let editingProductId = null;

  // Open Add Product Modal
  if (addProductBtn) {
    addProductBtn.addEventListener('click', () => {
      editingProductId = null;
      if (modalTitle) modalTitle.textContent = 'Add New Grocery Product';
      if (productForm) productForm.reset();
      document.getElementById('productIdInput').value = '';
      openModal();
    });
  }

  // Close Modal handlers
  closeModalBtns.forEach(btn => {
    btn.addEventListener('click', closeModal);
  });

  if (productModal) {
    productModal.addEventListener('click', (e) => {
      if (e.target === productModal) closeModal();
    });
  }

  function openModal() {
    if (productModal) productModal.classList.add('active');
  }

  function closeModal() {
    if (productModal) productModal.classList.remove('active');
    editingProductId = null;
  }

  // Edit Product click delegation
  if (productsTableBody) {
    productsTableBody.addEventListener('click', async (e) => {
      const editBtn = e.target.closest('.btn-edit-product');
      const deleteBtn = e.target.closest('.btn-delete-product');

      if (editBtn) {
        const prodId = editBtn.dataset.id;
        await openEditModal(prodId);
      } else if (deleteBtn) {
        const prodId = deleteBtn.dataset.id;
        const prodName = deleteBtn.dataset.name;
        if (confirm(`Are you sure you want to delete product "${prodName}"? Historical order receipts will remain preserved.`)) {
          await deleteProduct(prodId);
        }
      }
    });
  }

  async function openEditModal(productId) {
    try {
      const prod = await apiFetch(`/api/products/${productId}`);
      editingProductId = prod.id;
      if (modalTitle) modalTitle.textContent = `Edit Product #${prod.id}`;

      document.getElementById('productIdInput').value = prod.id;
      document.getElementById('productNameInput').value = prod.name;
      document.getElementById('productPriceInput').value = parseFloat(prod.price).toFixed(2);
      document.getElementById('productCategoryInput').value = prod.category;
      document.getElementById('productStockInput').value = prod.stock_quantity;
      document.getElementById('productImageInput').value = prod.image_url || '';
      document.getElementById('productDescInput').value = prod.description || '';

      openModal();
    } catch (err) {
      showToast(err.message || 'Failed to load product details.', 'error');
    }
  }

  // Handle Product Form Submit (Create or Update)
  if (productForm) {
    productForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const saveBtn = document.getElementById('saveProductBtn');
      const errorEl = document.getElementById('productFormError');

      if (errorEl) errorEl.style.display = 'none';

      const name = document.getElementById('productNameInput').value.trim();
      const price = parseFloat(document.getElementById('productPriceInput').value);
      const category = document.getElementById('productCategoryInput').value;
      const stock = parseInt(document.getElementById('productStockInput').value, 10);
      const imageUrl = document.getElementById('productImageInput').value.trim();
      const description = document.getElementById('productDescInput').value.trim();

      if (!name || isNaN(price) || price <= 0 || !category || isNaN(stock) || stock < 0) {
        if (errorEl) {
          errorEl.textContent = 'Please provide valid product name, positive price, and non-negative stock.';
          errorEl.style.display = 'block';
        }
        return;
      }

      saveBtn.disabled = true;
      saveBtn.textContent = 'Saving...';

      const payload = {
        name,
        price,
        category,
        stock_quantity: stock,
        image_url: imageUrl || null,
        description: description || null
      };

      try {
        if (editingProductId) {
          // Update
          await apiFetch(`/api/products/${editingProductId}`, {
            method: 'PUT',
            body: payload
          });
          showToast('Product successfully updated!', 'success');
        } else {
          // Create
          await apiFetch('/api/products', {
            method: 'POST',
            body: payload
          });
          showToast('Product added to inventory!', 'success');
        }

        closeModal();
        // Refresh products list
        await reloadProductsTable();
        await reloadDashboardStats();
      } catch (err) {
        if (errorEl) {
          errorEl.textContent = err.message || 'Failed to save product.';
          errorEl.style.display = 'block';
        }
        showToast(err.message || 'Failed to save product.', 'error');
      } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Product';
      }
    });
  }

  // Delete Product
  async function deleteProduct(productId) {
    try {
      await apiFetch(`/api/products/${productId}`, { method: 'DELETE' });
      showToast('Product successfully removed.', 'info');
      await reloadProductsTable();
      await reloadDashboardStats();
    } catch (err) {
      showToast(err.message || 'Failed to delete product.', 'error');
    }
  }

  // Reload products table
  async function reloadProductsTable() {
    if (!productsTableBody) return;
    const search = adminSearchInput ? adminSearchInput.value.trim() : '';
    const category = adminCategoryFilter ? adminCategoryFilter.value : 'All';

    let url = `/api/products?limit=200`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (category && category !== 'All') url += `&category=${encodeURIComponent(category)}`;

    try {
      const data = await apiFetch(url);
      renderTableRows(data.products);
    } catch (err) {
      console.error('Failed to reload products:', err);
    }
  }

  function renderTableRows(products) {
    if (!productsTableBody) return;

    if (products.length === 0) {
      productsTableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center; padding: 2.5rem; color: var(--text-muted);">
            No grocery products found matching your search.
          </td>
        </tr>
      `;
      return;
    }

    productsTableBody.innerHTML = products.map(p => `
      <tr id="admin-row-${p.id}">
        <td><strong>#${p.id}</strong></td>
        <td>
          <img src="${p.image_url || '/static/images/placeholder.svg'}"
               alt="${p.name}"
               style="width: 44px; height: 44px; border-radius: var(--radius-sm); object-fit: cover;"
               onerror="this.src='/static/images/placeholder.svg';">
        </td>
        <td>
          <div style="font-weight: 700; color: var(--text-main);">${p.name}</div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">${p.description ? p.description.slice(0, 50) + '...' : ''}</div>
        </td>
        <td><span class="badge" style="background:#e0f2fe; color:#0369a1;">${p.category}</span></td>
        <td style="font-weight: 800; color: var(--primary-darker);">${formatINR(p.price)}</td>
        <td>
          <span class="badge ${p.stock_quantity > 10 ? 'badge-in-stock' : p.stock_quantity > 0 ? 'badge-low-stock' : 'badge-out-of-stock'}">
            ${p.stock_quantity} left
          </span>
        </td>
        <td>
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn btn-sm btn-outline btn-edit-product" data-id="${p.id}">
              ✏️ Edit
            </button>
            <button class="btn btn-sm btn-danger-outline btn-delete-product" data-id="${p.id}" data-name="${p.name}">
              🗑️ Delete
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  // Reload stats
  async function reloadDashboardStats() {
    try {
      const stats = await apiFetch('/api/admin/stats');
      const elProd = document.getElementById('statTotalProducts');
      const elCust = document.getElementById('statTotalCustomers');
      const elOrders = document.getElementById('statTotalOrders');
      const elRev = document.getElementById('statTotalRevenue');
      const elLow = document.getElementById('statLowStock');

      if (elProd) elProd.textContent = stats.total_products;
      if (elCust) elCust.textContent = stats.total_customers;
      if (elOrders) elOrders.textContent = stats.total_orders;
      if (elRev) elRev.textContent = formatINR(stats.total_revenue);
      if (elLow) elLow.textContent = stats.low_stock_count;
    } catch (err) {
      console.error('Failed to reload admin metrics:', err);
    }
  }

  // Client-side search and category filtering in table
  if (adminSearchInput) {
    let debounceTimer;
    adminSearchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(reloadProductsTable, 250);
    });
  }

  if (adminCategoryFilter) {
    adminCategoryFilter.addEventListener('change', reloadProductsTable);
  }
});
