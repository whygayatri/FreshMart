import pytest
from decimal import Decimal


def test_checkout_empty_cart_fails(test_customer):
    """Test that attempting to checkout with an empty cart returns 400 Bad Request."""
    client, user_data, csrf_token = test_customer
    headers = {"X-CSRF-Token": csrf_token}

    resp = client.post("/api/orders", json={}, headers=headers)
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_successful_checkout_and_stock_reduction(test_customer, sample_product, db_session):
    """Test full checkout flow: stock decrements, cart cleared, order snapshots preserved."""
    client, user_data, csrf_token = test_customer
    headers = {"X-CSRF-Token": csrf_token}

    initial_stock = sample_product.stock_quantity  # 15

    # 1. Add 3 items to cart
    client.post("/api/cart/items", json={"product_id": sample_product.id, "quantity": 3}, headers=headers)

    # 2. Checkout
    checkout_resp = client.post("/api/orders", json={}, headers=headers)
    assert checkout_resp.status_code == 201
    order = checkout_resp.json()
    order_id = order["id"]
    assert float(order["total_amount"]) == 360.00  # 120 * 3
    assert len(order["items"]) == 1
    assert order["items"][0]["product_name"] == sample_product.name
    assert float(order["items"][0]["unit_price"]) == 120.00
    assert order["items"][0]["quantity"] == 3

    # 3. Verify cart is now empty
    cart_resp = client.get("/api/cart")
    assert cart_resp.status_code == 200
    assert cart_resp.json()["total_items"] == 0

    # 4. Verify inventory stock was reduced in database
    db_session.refresh(sample_product)
    assert sample_product.stock_quantity == initial_stock - 3  # 12

    # 5. Verify order history
    orders_resp = client.get("/api/orders")
    assert orders_resp.status_code == 200
    orders_list = orders_resp.json()["orders"]
    assert len(orders_list) == 1
    assert orders_list[0]["id"] == order_id


def test_checkout_insufficient_stock_rollback(test_customer, sample_product, db_session):
    """Test that if stock drops before checkout, checkout aborts without reducing inventory."""
    client, user_data, csrf_token = test_customer
    headers = {"X-CSRF-Token": csrf_token}

    # Add 5 items to cart
    client.post("/api/cart/items", json={"product_id": sample_product.id, "quantity": 5}, headers=headers)

    # External event: stock drops to 2
    sample_product.stock_quantity = 2
    db_session.commit()

    # Checkout should fail with 400
    checkout_resp = client.post("/api/orders", json={}, headers=headers)
    assert checkout_resp.status_code == 400
    assert "insufficient stock" in checkout_resp.json()["detail"].lower()

    # Verify stock remained at 2
    db_session.refresh(sample_product)
    assert sample_product.stock_quantity == 2


def test_order_isolation_between_customers(client, sample_product):
    """Test that customers cannot view another customer's orders."""
    # User A places an order
    client.post("/api/auth/register", json={
        "full_name": "Customer One",
        "email": "cust1@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })
    csrf_a = client.cookies.get("grocery_csrf")
    client.post("/api/cart/items", json={"product_id": sample_product.id, "quantity": 1}, headers={"X-CSRF-Token": csrf_a})
    order_a_resp = client.post("/api/orders", json={}, headers={"X-CSRF-Token": csrf_a})
    order_a_id = order_a_resp.json()["id"]

    # Log out
    client.post("/api/auth/logout")

    # User B registers
    client.post("/api/auth/register", json={
        "full_name": "Customer Two",
        "email": "cust2@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })

    # User B list orders - should NOT contain User A's order
    b_orders_resp = client.get("/api/orders")
    assert b_orders_resp.status_code == 200
    b_order_ids = [o["id"] for o in b_orders_resp.json()["orders"]]
    assert order_a_id not in b_order_ids

    # User B requests User A's order directly -> 403 Forbidden
    b_detail_resp = client.get(f"/api/orders/{order_a_id}")
    assert b_detail_resp.status_code == 403


def test_order_snapshot_preserved_after_product_deletion(test_customer, sample_product, db_session):
    """Test that if a product is later deleted, past order details and receipt line items remain intact."""
    client, user_data, csrf_token = test_customer
    headers = {"X-CSRF-Token": csrf_token}

    # Place order
    client.post("/api/cart/items", json={"product_id": sample_product.id, "quantity": 2}, headers=headers)
    order_resp = client.post("/api/orders", json={}, headers=headers)
    order_id = order_resp.json()["id"]

    # Now delete the original product using product_service
    from app.services.product_service import delete_product
    deleted = delete_product(db_session, sample_product.id)
    assert deleted is True

    # Retrieve past order - line snapshot must remain intact!
    order_get = client.get(f"/api/orders/{order_id}")
    assert order_get.status_code == 200
    order_data = order_get.json()
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["product_name"] == "Organic Test Apples"
    assert float(order_data["items"][0]["unit_price"]) == 120.00
    assert order_data["items"][0]["product_id"] is None  # FK detached cleanly
