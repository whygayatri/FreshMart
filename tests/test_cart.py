import pytest


def test_unauthenticated_cart_access_rejected(client):
    """Ensure unauthenticated access to /api/cart returns 401."""
    resp = client.get("/api/cart")
    assert resp.status_code == 401


def test_add_to_cart_and_duplicate_increment(test_customer, sample_product):
    """Test adding item to cart and verifying duplicate additions increment quantity."""
    client, user_data, csrf_token = test_customer
    headers = {"X-CSRF-Token": csrf_token}

    # Add 2 items
    payload = {"product_id": sample_product.id, "quantity": 2}
    add_resp = client.post("/api/cart/items", json=payload, headers=headers)
    assert add_resp.status_code == 201
    cart = add_resp.json()
    assert cart["total_items"] == 2
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2
    assert float(cart["total_amount"]) == 240.00  # 120.00 * 2

    # Add 3 more of the same item
    add_resp2 = client.post("/api/cart/items", json={"product_id": sample_product.id, "quantity": 3}, headers=headers)
    assert add_resp2.status_code == 201
    cart2 = add_resp2.json()
    assert cart2["total_items"] == 5
    assert len(cart2["items"]) == 1  # No duplicate row!
    assert cart2["items"][0]["quantity"] == 5
    assert float(cart2["total_amount"]) == 600.00


def test_add_to_cart_exceeding_stock_rejected(test_customer, sample_product):
    """Test that requesting more quantity than available stock returns 400 Bad Request."""
    client, user_data, csrf_token = test_customer
    headers = {"X-CSRF-Token": csrf_token}

    # sample_product has stock_quantity = 15
    payload = {"product_id": sample_product.id, "quantity": 20}
    resp = client.post("/api/cart/items", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "stock" in resp.json()["detail"].lower()


def test_update_and_remove_cart_item(test_customer, sample_product):
    """Test updating cart quantity and removing item from cart."""
    client, user_data, csrf_token = test_customer
    headers = {"X-CSRF-Token": csrf_token}

    # Add 2 items
    add_resp = client.post("/api/cart/items", json={"product_id": sample_product.id, "quantity": 2}, headers=headers)
    assert add_resp.status_code == 201
    item_id = add_resp.json()["items"][0]["id"]

    # Update to 4 items
    patch_resp = client.patch(f"/api/cart/items/{item_id}", json={"quantity": 4}, headers=headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["total_items"] == 4
    assert float(patch_resp.json()["total_amount"]) == 480.00

    # Delete item from cart
    del_resp = client.delete(f"/api/cart/items/{item_id}", headers=headers)
    assert del_resp.status_code == 200

    # Verify cart is empty
    cart_resp = client.get("/api/cart")
    assert cart_resp.status_code == 200
    assert cart_resp.json()["total_items"] == 0
    assert len(cart_resp.json()["items"]) == 0


def test_prevent_access_to_other_users_cart(client, sample_product):
    """Test that user B cannot tamper with or modify user A's cart items."""
    # Register Customer A
    client.post("/api/auth/register", json={
        "full_name": "User A",
        "email": "usera@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })
    csrf_a = client.cookies.get("grocery_csrf")
    add_resp = client.post(
        "/api/cart/items",
        json={"product_id": sample_product.id, "quantity": 2},
        headers={"X-CSRF-Token": csrf_a}
    )
    item_a_id = add_resp.json()["items"][0]["id"]

    # Log out Customer A
    client.post("/api/auth/logout")

    # Register Customer B
    client.post("/api/auth/register", json={
        "full_name": "User B",
        "email": "userb@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })
    csrf_b = client.cookies.get("grocery_csrf")

    # Customer B tries to update User A's item -> 403 Forbidden
    patch_resp = client.patch(
        f"/api/cart/items/{item_a_id}",
        json={"quantity": 10},
        headers={"X-CSRF-Token": csrf_b}
    )
    assert patch_resp.status_code == 403

    # Customer B tries to delete User A's item -> 403 Forbidden
    del_resp = client.delete(
        f"/api/cart/items/{item_a_id}",
        headers={"X-CSRF-Token": csrf_b}
    )
    assert del_resp.status_code == 403
