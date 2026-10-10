/**
 * FreshMart Grocery E-Commerce - Cart & Checkout JavaScript
 * Handles cart quantity updates, item deletions, and transactional checkout placement.
 */

document.addEventListener('DOMContentLoaded', () => {

  // ==========================================================================
  // Shopping Cart Operations (/cart)
  // ==========================================================================
  const cartTableBody = document.getElementById('cartTableBody');
  const cartSummarySubtotal = document.getElementById('cartSubtotal');
  const cartSummaryTotal = document.getElementById('cartTotal');
  const cartLayout = document.getElementById('cartLayout');
  const emptyCartState = document.getElementById('emptyCartState');

  function renderCartState(cart) {
    updateCartBadge(cart.total_items);

    if (cart.total_items === 0) {
      if (cartLayout) cartLayout.style.display = 'none';
      if (emptyCartState) emptyCartState.style.display = 'block';
      return;
    }

    if (cartSummarySubtotal) cartSummarySubtotal.textContent = formatINR(cart.total_amount);
    if (cartSummaryTotal) cartSummaryTotal.textContent = formatINR(cart.total_amount);
  }

  // Handle Cart item +/- quantity and removal
  if (cartTableBody) {
    cartTableBody.addEventListener('click', async (e) => {
      const btn = e.target.closest('button');
      if (!btn) return;

      const action = btn.dataset.action;
      const itemId = btn.dataset.itemId;
      const row = document.getElementById(`cart-row-${itemId}`);

      if (!action || !itemId || !row) return;

      const qtyInput = row.querySelector('.qty-val');
      let currentQty = parseInt(qtyInput ? qtyInput.textContent : '1');

      if (action === 'increase') {
        const newQty = currentQty + 1;
        btn.disabled = true;
        try {
          const updatedCart = await apiFetch(`/api/cart/items/${itemId}`, {
            method: 'PATCH',
            body: { quantity: newQty }
          });
          qtyInput.textContent = newQty;
          // Update item subtotal
          const updatedItem = updatedCart.items.find(i => i.id == itemId);
          if (updatedItem) {
            const subtotalEl = row.querySelector('.item-subtotal');
            if (subtotalEl) subtotalEl.textContent = formatINR(updatedItem.line_subtotal);
          }
          renderCartState(updatedCart);
        } catch (err) {
          showToast(err.message || 'Could not update quantity.', 'error');
        } finally {
          btn.disabled = false;
        }
      } else if (action === 'decrease') {
        if (currentQty <= 1) {
          // Confirm remove
          if (confirm('Do you want to remove this grocery item from your cart?')) {
            await removeItem(itemId, row);
          }
          return;
        }

        const newQty = currentQty - 1;
        btn.disabled = true;
        try {
          const updatedCart = await apiFetch(`/api/cart/items/${itemId}`, {
            method: 'PATCH',
            body: { quantity: newQty }
          });
          qtyInput.textContent = newQty;
          const updatedItem = updatedCart.items.find(i => i.id == itemId);
          if (updatedItem) {
            const subtotalEl = row.querySelector('.item-subtotal');
            if (subtotalEl) subtotalEl.textContent = formatINR(updatedItem.line_subtotal);
          }
          renderCartState(updatedCart);
        } catch (err) {
          showToast(err.message || 'Could not update quantity.', 'error');
        } finally {
          btn.disabled = false;
        }
      } else if (action === 'remove') {
        if (confirm('Are you sure you want to remove this item?')) {
          await removeItem(itemId, row);
        }
      }
    });
  }

  async function removeItem(itemId, rowElement) {
    try {
      await apiFetch(`/api/cart/items/${itemId}`, { method: 'DELETE' });
      rowElement.remove();
      showToast('Item removed from cart.', 'info');

      // Fetch fresh cart summary
      const freshCart = await apiFetch('/api/cart');
      renderCartState(freshCart);
    } catch (err) {
      showToast(err.message || 'Failed to remove item.', 'error');
    }
  }

  // ==========================================================================
  // Checkout Processing (/checkout)
  // ==========================================================================
  const checkoutForm = document.getElementById('checkoutForm');
  if (checkoutForm) {
    checkoutForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('placeOrderBtn');
      const errorEl = document.getElementById('checkoutError');

      if (errorEl) errorEl.style.display = 'none';

      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Placing Order & Decrementing Inventory...';

      const shippingName = document.getElementById('shippingName')?.value || '';
      const shippingAddress = document.getElementById('shippingAddress')?.value || '';
      const shippingPhone = document.getElementById('shippingPhone')?.value || '';

      try {
        const order = await apiFetch('/api/orders', {
          method: 'POST',
          body: {
            shipping_name: shippingName,
            shipping_address: shippingAddress,
            shipping_phone: shippingPhone
          }
        });

        // Update badge to 0
        updateCartBadge(0);
        showToast('Order successfully confirmed!', 'success');

        // Redirect to order confirmation page
        setTimeout(() => {
          window.location.href = `/order-confirmation?order_id=${order.id}`;
        }, 600);
      } catch (err) {
        if (errorEl) {
          errorEl.textContent = err.message || 'Failed to place order.';
          errorEl.style.display = 'block';
        }
        showToast(err.message || 'Failed to process checkout.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Place Order & Pay on Delivery';
      }
    });
  }
});
