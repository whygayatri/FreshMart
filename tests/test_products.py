import pytest


def test_list_products_empty_and_seeded(client, sample_product):
    """Test retrieving products list and individual product detail."""
    resp = client.get("/api/products")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(p["id"] == sample_product.id for p in data["products"])

    # Test single product detail
    single_resp = client.get(f"/api/products/{sample_product.id}")
    assert single_resp.status_code == 200
    assert single_resp.json()["name"] == sample_product.name


def test_get_nonexistent_product_returns_404(client):
    """Test that requesting nonexistent product returns 404."""
    resp = client.get("/api/products/999999")
    assert resp.status_code == 404


def test_product_search_and_category_filter(client, db_session):
    """Test searching by name and filtering by category."""
    from app.models import Product
    from decimal import Decimal

    p1 = Product(name="Nagpur Fresh Oranges", price=Decimal("110.00"), category="Fruits", stock_quantity=10)
    p2 = Product(name="Fresh Spinach Palak", price=Decimal("30.00"), category="Vegetables", stock_quantity=20)
    db_session.add_all([p1, p2])
    db_session.commit()

    # Filter by category
    resp_fruits = client.get("/api/products?category=Fruits")
    assert resp_fruits.status_code == 200
    fruit_names = [p["name"] for p in resp_fruits.json()["products"]]
    assert "Nagpur Fresh Oranges" in fruit_names
    assert "Fresh Spinach Palak" not in fruit_names

    # Search by keyword
    resp_search = client.get("/api/products?search=spinach")
    assert resp_search.status_code == 200
    search_names = [p["name"] for p in resp_search.json()["products"]]
    assert "Fresh Spinach Palak" in search_names
    assert "Nagpur Fresh Oranges" not in search_names


def test_customer_cannot_create_or_modify_products(test_customer, sample_product):
    """Ensure customer account cannot create, update, or delete products."""
    client, _, csrf_token = test_customer
    headers = {"X-CSRF-Token": csrf_token}

    new_prod = {
        "name": "Unauthorized Mango",
        "price": 250.0,
        "category": "Fruits",
        "stock_quantity": 10
    }
    # Customer POST -> 403
    create_resp = client.post("/api/products", json=new_prod, headers=headers)
    assert create_resp.status_code == 403

    # Customer PUT -> 403
    update_resp = client.put(f"/api/products/{sample_product.id}", json={"price": 10.0}, headers=headers)
    assert update_resp.status_code == 403

    # Customer DELETE -> 403
    delete_resp = client.delete(f"/api/products/{sample_product.id}", headers=headers)
    assert delete_resp.status_code == 403


def test_admin_product_crud_flow(test_admin):
    """Test complete product CRUD operations by an authorized administrator."""
    client, csrf_token = test_admin
    headers = {"X-CSRF-Token": csrf_token}

    # 1. Create Product
    create_data = {
        "name": "Tata Tea Gold (500 g)",
        "price": 310.00,
        "category": "Beverages",
        "stock_quantity": 50,
        "image_url": "https://images.unsplash.com/photo-1594631252845-29fc4cc8cde9",
        "description": "Rich Assam tea granules"
    }
    create_resp = client.post("/api/products", json=create_data, headers=headers)
    assert create_resp.status_code == 201
    prod = create_resp.json()
    prod_id = prod["id"]
    assert prod["name"] == "Tata Tea Gold (500 g)"
    assert float(prod["price"]) == 310.00
    assert prod["stock_quantity"] == 50

    # 2. Update Product
    update_data = {
        "price": 325.00,
        "stock_quantity": 45
    }
    update_resp = client.put(f"/api/products/{prod_id}", json=update_data, headers=headers)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert float(updated["price"]) == 325.00
    assert updated["stock_quantity"] == 45

    # 3. Read Updated Product
    read_resp = client.get(f"/api/products/{prod_id}")
    assert read_resp.status_code == 200
    assert float(read_resp.json()["price"]) == 325.00

    # 4. Delete Product
    del_resp = client.delete(f"/api/products/{prod_id}", headers=headers)
    assert del_resp.status_code == 200

    # Verify deleted
    get_after = client.get(f"/api/products/{prod_id}")
    assert get_after.status_code == 404


def test_product_input_validations(test_admin):
    """Test product validation rules: empty name, negative price, invalid category."""
    client, csrf_token = test_admin
    headers = {"X-CSRF-Token": csrf_token}

    # Empty name
    resp1 = client.post("/api/products", json={
        "name": "   ",
        "price": 100.0,
        "category": "Dairy",
        "stock_quantity": 5
    }, headers=headers)
    assert resp1.status_code == 422

    # Negative price
    resp2 = client.post("/api/products", json={
        "name": "Milk",
        "price": -50.0,
        "category": "Dairy",
        "stock_quantity": 5
    }, headers=headers)
    assert resp2.status_code == 422

    # Invalid category
    resp3 = client.post("/api/products", json={
        "name": "Unknown Item",
        "price": 100.0,
        "category": "AutomotiveParts",
        "stock_quantity": 5
    }, headers=headers)
    assert resp3.status_code == 422
