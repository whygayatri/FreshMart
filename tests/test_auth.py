import pytest


def test_customer_registration_success(client):
    """Test successful customer registration with valid credentials."""
    payload = {
        "full_name": "Rohan Sharma",
        "email": "rohan@example.com",
        "password": "Secret@123",
        "confirm_password": "Secret@123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "rohan@example.com"
    assert data["full_name"] == "Rohan Sharma"
    assert data["role"] == "customer"
    assert "password" not in data
    assert "password_hash" not in data
    # Verify session cookie was set
    assert "grocery_session" in client.cookies


def test_customer_registration_password_mismatch(client):
    """Test that mismatched passwords fail validation with 422."""
    payload = {
        "full_name": "Rohan Sharma",
        "email": "rohan_diff@example.com",
        "password": "Secret@123",
        "confirm_password": "DifferentPassword@123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_customer_registration_duplicate_email(client):
    """Test that registering an already existing email returns 409 Conflict."""
    payload = {
        "full_name": "Anita Verma",
        "email": "anita@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    # Attempt to register again with same email
    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


def test_customer_login_success_and_logout(client):
    """Test customer login, me endpoint, and logout session invalidation."""
    # Register customer
    reg_payload = {
        "full_name": "Kavita Rao",
        "email": "kavita@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    client.post("/api/auth/register", json=reg_payload)

    # Log out
    client.post("/api/auth/logout")

    # Login
    login_payload = {
        "email": "kavita@example.com",
        "password": "Password@123"
    }
    login_resp = client.post("/api/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    assert login_resp.json()["email"] == "kavita@example.com"
    assert "grocery_session" in client.cookies

    # Verify /api/auth/me
    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["authenticated"] is True
    assert me_resp.json()["user"]["email"] == "kavita@example.com"

    # Logout
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200

    # Verify /api/auth/me is now unauthenticated
    me_after = client.get("/api/auth/me")
    assert me_after.status_code == 200
    assert me_after.json()["authenticated"] is False


def test_customer_login_invalid_password(client):
    """Test login with incorrect password returns 401."""
    reg_payload = {
        "full_name": "Suresh Raina",
        "email": "suresh@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    client.post("/api/auth/register", json=reg_payload)

    login_resp = client.post(
        "/api/auth/login",
        json={"email": "suresh@example.com", "password": "WrongPassword"}
    )
    assert login_resp.status_code == 401
    assert "Invalid email or password" in login_resp.json()["detail"]


def test_admin_login_success_and_failure(client):
    """Test admin authentication flow with correct and incorrect credentials."""
    # Success
    resp_ok = client.post(
        "/api/auth/admin/login",
        json={"username_or_email": "testadmin", "password": "Admin@12345"}
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["role"] == "admin"

    # Failure
    resp_fail = client.post(
        "/api/auth/admin/login",
        json={"username_or_email": "testadmin", "password": "IncorrectAdminPassword"}
    )
    assert resp_fail.status_code == 401


def test_customer_cannot_authenticate_at_admin_endpoint(client):
    """Test that customer credentials cannot gain admin privileges at admin endpoint."""
    reg_payload = {
        "full_name": "Regular User",
        "email": "regular@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    client.post("/api/auth/register", json=reg_payload)

    admin_login_resp = client.post(
        "/api/auth/admin/login",
        json={"username_or_email": "regular@example.com", "password": "Password@123"}
    )
    assert admin_login_resp.status_code == 401
