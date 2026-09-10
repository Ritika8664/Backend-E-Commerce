# ⚙️ Mini AI E-Commerce Backend Service (Assignment 2)

FastAPI backend service powering the Mini AI E-Commerce Application. Features **Google OAuth ID Token verification**, **JWT Authentication**, **Role-Based Access Control (RBAC)**, **PostgreSQL Database Management**, **Stripe Payment Gateway Integration**, and an **AI Customer Support Agent** built with **LangChain**.

---

## 📋 Deliverables Overview

| Attribute | Specification |
| :--- | :--- |
| **Assignment** | Technical Interview Assignment 2 – Mini AI E-Commerce Application |
| **Total Development Time** | **24 Hours** |
| **Primary AI Coding Assistant** | **OpenAI Codex** |
| **Backend Framework** | FastAPI (Python 3.11+) |
| **Database** | PostgreSQL + SQLAlchemy 2.0 ORM + Alembic Migrations |

---

## 🤖 AI Tools & Development Usage

### **AI Assistant Used:** **OpenAI Codex**

### **How OpenAI Codex Was Utilized:**
* **Database Models & Alembic:** Designed SQLAlchemy ORM schema with foreign key constraints, indexes, and non-negative check constraints (`price >= 0`, `stock >= 0`).
* **Authentication & RBAC:** Implemented Google OAuth ID token verification via `google-auth` library, JWT session generation (`python-jose`), and FastAPI dependency injection for role checks (`get_current_user`, `get_current_admin`).
* **LangChain AI Support Agent:** Built read-only Python function tools (`search_products`, `get_product_price`, `get_order_status`) bound to PostgreSQL database models to answer customer support inquiries accurately without hallucinations.
* **Stripe Payment Flows:** Integrated Stripe Checkout session creation, payment verification, and webhook event handling.

---

## 🛠️ Backend Tech Stack

* **Framework:** Python 3.11+ / FastAPI
* **Database:** PostgreSQL (SQLAlchemy 2.0 ORM + Alembic migrations)
* **Auth & Security:** `google-auth` (Google OAuth ID Token Verification), `python-jose` (JWT), `passlib` / `bcrypt`
* **AI Support Agent:** `langchain`, `langgraph`, `langchain-google-genai`
* **Payments:** `stripe` (Stripe Checkout & Webhooks)
* **Server:** Uvicorn ASGI Server

---

## 🔌 API Endpoints Reference

### 🔑 Authentication (`/auth`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/google` | Public | Validates Google ID token, registers new user if needed, returns JWT. |
| `POST` | `/auth/login` | Public | Standard login with email/password (testing/admin). |
| `GET` | `/auth/me` | Authenticated | Fetches profile info for current user. |

### 🛍️ Product Management (`/products` & `/admin/products`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/products` | Public | List active product catalog. |
| `GET` | `/products/{id}` | Public | Fetch product details by ID. |
| `POST` | `/admin/products` | Admin | Create a new product. |
| `PUT` | `/admin/products/{id}` | Admin | Update existing product details & inventory stock. |
| `DELETE` | `/admin/products/{id}` | Admin | Delete a product. |

### 📦 Order Management (`/orders` & `/admin/orders`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/orders` | Authenticated | Validate stock and create a new pending order. |
| `GET` | `/orders/me` | Customer | Fetch current customer's order history. |
| `GET` | `/orders/{id}` | Customer | Fetch specific order (enforces user ownership). |
| `GET` | `/admin/orders` | Admin | Fetch all orders across all customers. |
| `PATCH` | `/admin/orders/{id}/status` | Admin | Update order fulfillment status (`pending`, `paid`, `failed`, `cancelled`). |

### 💳 Stripe Payments (`/payments` & `/webhooks`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/payments/create-checkout-session` | Authenticated | Create a Stripe checkout session for a pending order. |
| `POST` | `/payments/verify` | Authenticated | Verify payment completion status. |
| `POST` | `/webhooks/stripe` | Public (Verified) | Webhook handler to auto-update order status upon Stripe payment confirmation. |

### 🤖 AI Support Agent (`/ai`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/ai/chat` | Authenticated | Interacts with LangChain agent to query prices, product availability, or order status. |

---

## 🔐 Security & RBAC Enforcement

* **Backend RBAC Enforcer (`app/deps.py`):**
  * `get_current_user`: Decodes incoming JWT Bearer header and extracts user identity.
  * `get_current_admin`: Validates that `user.role == "admin"`. Rejects non-admin requests with `HTTP 403 Forbidden`.
  * **Ownership Isolation:** Customers can only query order records matching their own `user.id`.

---

## 🤖 AI Support Agent Architecture

The AI support agent (`app/ai/agent.py`) operates with strict database guardrails:
1. **Tool-Calling Only:** Executes read-only Python functions (`search_products`, `get_product_price`, `get_order_status`).
2. **User Context Injection:** Automatically passes `user_id` to database tools so customers can only inquire about **their own** orders.
3. **Read-Only Guards:** Agent has zero access to data mutation functions (cannot change prices, stock, or order status).

---

## 🚀 Setup & Local Execution Guide

### **Prerequisites**
* Python 3.11+
* PostgreSQL Database running locally or via Cloud (Neon / Supabase)

### **Installation**

```bash
# Navigate to backend folder
cd Backend-E-Commerce

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Environment Configuration (`.env`)**
Create a `.env` file in `Backend-E-Commerce/`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecommerce_db
SECRET_KEY=your_jwt_super_secret_key
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_API_KEY=your_gemini_api_key
FRONTEND_ORIGIN=http://localhost:5173
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret
```

### **Database Migrations & Running Uvicorn**

```bash
# Run database migrations
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

FastAPI Interactive Swagger Docs: `http://localhost:8000/docs`
