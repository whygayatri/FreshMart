# FreshMart - Complete Grocery E-Commerce Website (FastAPI)

A modern, full-stack grocery e-commerce web application built from scratch using **Python + FastAPI**, **SQLAlchemy**, **SQLite**, **HTML5**, **CSS3**, and **vanilla JavaScript**.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Quick Start & Installation (Windows & macOS/Linux)](#quick-start--installation)
- [Demonstration Credentials](#demonstration-credentials)
- [API Documentation & Endpoints](#api-documentation--endpoints)
- [Security Architecture](#security-architecture)
- [Automated Testing](#automated-testing)
- [Known Limitations & Future Enhancements](#known-limitations--future-enhancements)

---

## 🌟 Overview

FreshMart is an online grocery store application that allows customers to browse groceries across multiple categories, search products, add items to a persistent cart, and place orders with real-time stock management. Store managers can log in through a dedicated administrative portal to manage inventory and monitor business analytics.

All business operations—authentication, product catalog management, shopping cart updates, stock verification, and order processing—run entirely on the FastAPI backend and persist in SQLite.

---

## 🛠️ Architecture & Tech Stack

| Component | Technology | Rationale & Usage |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** | High-performance Python async framework with automatic OpenAPI docs |
| **ASGI Server** | **Uvicorn** | Fast ASGI web server for development and production |
| **Database** | **SQLite** | Lightweight, file-based relational database (`grocery.db`) |
| **ORM** | **SQLAlchemy 2.0** | Object-Relational Mapping with parameterized SQL queries |
| **Data Validation** | **Pydantic v2** | Strong typing, input sanitation, and output schemas |
| **HTML Templates** | **Jinja2** | Server-side template rendering integrated with FastAPI |
| **Frontend** | **HTML5 + CSS3 + Vanilla JS** | Zero frontend build step; responsive green-and-white theme |
| **Password Hashing** | **Argon2 (`argon2-cffi`)** | State-of-the-art cryptographic password hashing |
| **Session Auth** | **HttpOnly Cookies** | Secure, server-side session cookies with CSRF double-submit protection |
| **Currency Calculations** | **Python `Decimal`** | Fixed-precision decimal calculations (in INR ₹) |
| **Testing** | **Pytest + FastAPI TestClient** | Automated integration and unit test suite |

---

## ✨ Key Features

### 🛒 Customer Storefront
- **Fresh Green & White Theme:** Modern, responsive design suitable for mobile, tablet, and desktop.
- **Dynamic Catalog:** Browse 7 sample grocery categories (*Fruits, Vegetables, Dairy, Grains, Snacks, Beverages, Household Essentials*).
- **Search & Filter:** Search by product name or description, filter by category chips, and sort by price or name.
- **Stock Badges:** Real-time stock status (*In Stock*, *Only X Left*, *Out of Stock*).
- **Image Fallbacks:** Automatic SVG placeholder if an image fails to load.

### 👤 Customer Authentication
- **Dedicated Pages:** Separate registration (`/register`) and login (`/login`) pages.
- **Account Validation:** Full name, valid email format, minimum 6-character passwords, password matching confirmation.
- **Secure Sessions:** Sessions stored in SQLite and bound to HttpOnly cookies.
- **Data Isolation:** Customers can only inspect and modify their own carts and order histories.

### 🧺 Persistent Shopping Cart
- **Database Persistence:** Carts survive server restarts and browser reloads.
- **Quantity Controls:** Increment/decrement quantities and remove items.
- **Stock Guard:** Backend prevents customers from adding more items than available in inventory.
- **Automatic Subtotals:** Calculates item line totals and cart totals strictly on the backend.

### 📦 Transactional Checkout & Orders
- **Atomic Operations:** Uses database transactions to check stock, decrement inventory, create order records, and clear the cart.
- **Price & Item Snapshots:** Stores unit price, product name, and quantity snapshots in `OrderItem` so historical receipts remain unchanged even if the original product is edited or deleted.
- **Order History:** Dedicated order history page (`/orders`) and receipt confirmation (`/order-confirmation`).

### 🛡️ Admin Dashboard & Inventory Management
- **Dedicated Admin Login:** Isolated login portal at `/admin/login`.
- **Business Analytics:** Real-time summary cards for Total Products, Registered Customers, Total Orders, Gross Revenue (₹), and Low Stock alerts.
- **Full CRUD Management:** Create, Read, Update, and Delete grocery items.
- **Safe Deletion:** Deleting a product safely unlinks it from active carts and preserves historical order receipts.

---

## 📂 Project Structure

```
ecommerce/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization, lifespan, middleware
│   ├── config.py            # Pydantic Settings and environment configuration
│   ├── database.py          # SQLite connection and session generator (get_db)
│   ├── models.py            # SQLAlchemy models (User, Product, CartItem, Order, OrderItem, UserSession)
│   ├── schemas.py           # Pydantic request and response schemas
│   ├── security.py          # Argon2 hashing, token generation, cookie helpers
│   ├── dependencies.py      # Dependency injection for customer/admin auth and CSRF
│   ├── seed.py              # Idempotent database seeder (sample products + admin)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py         # Jinja2 HTML storefront & admin page routes
│   │   ├── auth.py          # Customer and admin authentication REST endpoints
│   │   ├── products.py      # Product listing and admin CRUD REST endpoints
│   │   ├── cart.py          # Shopping cart management REST endpoints
│   │   ├── orders.py        # Checkout and order history REST endpoints
│   │   └── admin.py         # Admin dashboard metrics REST endpoints
│   └── services/
│       ├── auth_service.py  # User registration, login verification, session DB ops
│       ├── product_service.py # Product queries, creation, update, safe deletion
│       ├── cart_service.py  # Cart item calculation, additions, stock checks
│       └── order_service.py # Transactional checkout and analytics calculation
├── templates/
│   ├── base.html            # Core layout with sticky header, nav, footer, toasts
│   ├── index.html           # Storefront homepage with hero banner and catalog
│   ├── login.html           # Customer login form
│   ├── register.html        # Customer registration form
│   ├── cart.html            # Shopping cart management view
│   ├── checkout.html        # Checkout delivery details and confirmation
│   ├── orders.html          # Customer past order history
│   ├── order_confirmation.html # Order receipt & celebration view
│   ├── admin_login.html     # Dedicated admin login portal
│   └── admin_dashboard.html # Admin product inventory management table and modals
├── static/
│   ├── css/
│   │   └── style.css        # Responsive green-and-white stylesheet
│   ├── js/
│   │   ├── main.js          # Fetch wrapper, CSRF handling, toast alerts, cart badges
│   │   ├── auth.js          # Login, registration, and logout handling
│   │   ├── cart.js          # Cart item manipulation and checkout submission
│   │   └── admin.js         # Admin product CRUD modals, filters, and stats
│   └── images/
│       └── placeholder.svg  # Fallback image SVG
├── tests/
│   ├── conftest.py          # Isolated in-memory SQLite fixtures and test clients
│   ├── test_auth.py         # Authentication and role verification tests
│   ├── test_products.py     # Product CRUD and search/filtering tests
│   ├── test_cart.py         # Shopping cart tests and user isolation
│   ├── test_orders.py       # Transactional checkout and stock tests
│   └── test_pages.py        # Jinja2 HTML template rendering tests
├── .env.example             # Documented environment variables template
├── .gitignore               # Git ignore rules
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- **Git**

### 2. Clone and Enter Project Directory
```bash
git clone <repository-url>
cd ecommerce
```

### 3. Create a Virtual Environment

#### On Windows (Command Prompt or PowerShell):
```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy the template configuration file:

#### On Windows:
```cmd
copy .env.example .env
```

#### On macOS / Linux:
```bash
cp .env.example .env
```

### 6. Initialize & Seed Database
Initialize SQLite tables and populate the catalog with 30+ sample Indian grocery items:
```bash
python -m app.seed
```
*(Note: Seeding is idempotent and runs automatically on application startup as well).*

### 7. Run the Application
Start the ASGI development server:
```bash
uvicorn app.main:app --reload
```

- **Website Storefront:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Docs:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Admin Portal:** [http://127.0.0.1:8000/admin/login](http://127.0.0.1:8000/admin/login)

---

## 🔑 Demonstration Credentials

| Role | Login URL | Identifier / Username | Password |
| :--- | :--- | :--- | :--- |
| **Administrator** | `/admin/login` | `admin` *(or `admin@freshmart.local`)* | `Admin@12345` |
| **Customer** | `/register` or `/login` | Register a new account or use any registered email | Minimum 6 chars |

> **Security Note:** In production, change `ADMIN_PASSWORD` and `SECRET_KEY` in your `.env` file and set `COOKIE_SECURE=true`.

---

## 📡 API Documentation & Endpoints

All endpoints validate inputs via Pydantic schemas and return appropriate HTTP status codes (200, 201, 400, 401, 403, 404, 409, 422).

### Authentication Endpoints (`/api/auth`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register customer account | No |
| `POST` | `/api/auth/login` | Authenticate customer | No |
| `POST` | `/api/auth/admin/login` | Authenticate administrator | No |
| `POST` | `/api/auth/logout` | Invalidate session & clear cookies | Yes |
| `GET` | `/api/auth/me` | Retrieve current user profile & CSRF token | Optional |

### Product Endpoints (`/api/products`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/products` | List & filter products (`search`, `category`, `sort_by`, `page`, `limit`) | No |
| `GET` | `/api/products/{product_id}` | Retrieve single product details | No |
| `POST` | `/api/products` | Create product | **Admin only** |
| `PUT` | `/api/products/{product_id}` | Update product details | **Admin only** |
| `DELETE`| `/api/products/{product_id}`| Safely delete product | **Admin only** |

### Shopping Cart Endpoints (`/api/cart`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/cart` | Get authenticated customer's cart | Customer |
| `POST` | `/api/cart/items` | Add product to cart (increments if exists) | Customer |
| `PATCH`| `/api/cart/items/{item_id}`| Update cart item quantity | Customer |
| `DELETE`| `/api/cart/items/{item_id}`| Remove item from cart | Customer |

### Order Endpoints (`/api/orders`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/orders` | Checkout cart in transaction & decrement stock | Customer |
| `GET` | `/api/orders` | Customer order history | Customer |
| `GET` | `/api/orders/{order_id}` | Retrieve specific order receipt | Customer / Admin |

### Admin Endpoints (`/api/admin`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/stats` | Aggregated store metrics (products, customers, orders, revenue, low stock) | **Admin only** |
| `GET` | `/api/admin/orders` | List all orders across all customers | **Admin only** |

---

## 🔒 Security Architecture

1. **Password Hashing:** Passwords hashed with `Argon2` using `argon2-cffi`. Hashes and salt secrets are never sent in responses.
2. **HttpOnly Session Cookies:** Session tokens are stored in SQLite and conveyed via `HttpOnly`, `SameSite=Lax` cookies, blocking client-side JavaScript access.
3. **Double-Submit CSRF Protection:** State-changing requests (POST, PUT, PATCH, DELETE) require a matching `X-CSRF-Token` header.
4. **Server-Side Authorization:** Every admin operation strictly verifies `user.role == 'admin'` on the backend.
5. **Customer Data Isolation:** Customers are strictly restricted to querying and mutating their own carts and orders.
6. **SQL Injection Prevention:** Parameterized SQL queries enforced through SQLAlchemy ORM.
7. **Security Headers:** Response headers include `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.

---

## 🧪 Automated Testing

The project includes an automated test suite using **pytest** and FastAPI's **TestClient** with an isolated in-memory SQLite database.

### Run All Tests:
```bash
pytest
```

### Verbose Test Output:
```bash
pytest -v
```

### Test Coverage Highlights:
- ✅ Customer registration with duplicate email rejection (409)
- ✅ Customer & Admin login success / failure handling (401)
- ✅ Session invalidation on logout
- ✅ Role-based access control (customers rejected on admin operations with 403)
- ✅ Product CRUD operations, validation, category filtering, keyword searching
- ✅ Cart management, quantity increment on duplicate addition, stock limit checks
- ✅ Cart isolation between different customers
- ✅ Transactional checkout with atomic stock decrement
- ✅ Order snapshot persistence even if original products are edited or deleted
- ✅ Jinja2 HTML storefront & admin template rendering and unauthorized redirects

---

## 📝 Known Limitations & Future Enhancements

- **Payment Gateway:** A real payment provider (e.g. Razorpay, Stripe) is not integrated; checkout operates on a realistic Cash/UPI-on-delivery flow suitable for learning and demonstration.
- **Email Notifications:** Order confirmation emails are simulated via in-app receipts rather than an SMTP mail server.
