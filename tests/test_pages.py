import pytest


def test_home_page_renders_successfully(client, sample_product):
    """Test that the homepage renders 200 OK with HTML content."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "FreshMart" in resp.text
    assert sample_product.name in resp.text
    assert "text/html" in resp.headers["content-type"]


def test_login_and_register_pages_render(client):
    """Test customer login and register HTML pages."""
    resp_login = client.get("/login")
    assert resp_login.status_code == 200
    assert "Sign In" in resp_login.text

    resp_reg = client.get("/register")
    assert resp_reg.status_code == 200
    assert "Create Account" in resp_reg.text


def test_admin_login_page_renders(client):
    """Test dedicated admin login page."""
    resp = client.get("/admin/login")
    assert resp.status_code == 200
    assert "Admin Portal" in resp.text


def test_protected_pages_redirect_unauthenticated_users(client):
    """Test that unauthenticated visitors are redirected to /login or /admin/login."""
    # Cart page
    cart_resp = client.get("/cart", follow_redirects=False)
    assert cart_resp.status_code == 302
    assert "/login" in cart_resp.headers["location"]

    # Checkout page
    checkout_resp = client.get("/checkout", follow_redirects=False)
    assert checkout_resp.status_code == 302
    assert "/login" in checkout_resp.headers["location"]

    # Orders page
    orders_resp = client.get("/orders", follow_redirects=False)
    assert orders_resp.status_code == 302
    assert "/login" in orders_resp.headers["location"]

    # Admin dashboard
    admin_dash_resp = client.get("/admin/dashboard", follow_redirects=False)
    assert admin_dash_resp.status_code == 302
    assert "/admin/login" in admin_dash_resp.headers["location"]


def test_customer_cart_and_orders_pages_render_when_authenticated(test_customer, sample_product):
    """Test cart, orders, and confirmation pages render for authenticated customer."""
    client, user_data, csrf_token = test_customer

    # Add item to cart
    client.post("/api/cart/items", json={"product_id": sample_product.id, "quantity": 1}, headers={"X-CSRF-Token": csrf_token})

    # Cart page
    cart_resp = client.get("/cart")
    assert cart_resp.status_code == 200
    assert "Your Grocery Cart" in cart_resp.text
    assert sample_product.name in cart_resp.text

    # Checkout page
    checkout_resp = client.get("/checkout")
    assert checkout_resp.status_code == 200
    assert "Checkout & Delivery" in checkout_resp.text

    # Place order
    order_resp = client.post("/api/orders", json={}, headers={"X-CSRF-Token": csrf_token})
    order_id = order_resp.json()["id"]

    # Order confirmation page
    conf_resp = client.get(f"/order-confirmation?order_id={order_id}")
    assert conf_resp.status_code == 200
    assert f"Order Confirmed #{order_id}" in conf_resp.text

    # Orders page
    orders_resp = client.get("/orders")
    assert orders_resp.status_code == 200
    assert "My Order History" in orders_resp.text


def test_admin_dashboard_renders_for_admin(test_admin):
    """Test admin dashboard renders 200 OK with inventory table when logged in as admin."""
    client, csrf_token = test_admin
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 200
    assert "Inventory Management Dashboard" in resp.text
    assert "Add New Product" in resp.text
