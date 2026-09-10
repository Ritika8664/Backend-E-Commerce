# ⚙️ Mini AI E-Commerce Backend Service (Assignment 2)

FastAPI backend service powering the Mini AI E-Commerce Application. Features **Google OAuth ID Token verification**, **JWT Authentication**, **Role-Based Access Control (RBAC)**, **PostgreSQL Database Management**, **Stripe Payment Gateway Integration**, and an **AI Customer Support Agent** built with **LangChain**.

---

## 📋 Required Deliverables Summary

| Deliverable | Details |
| :--- | :--- |
| **Total Time Taken** | **24 Hours** |
| **AI Tools Used** | **OpenAI Codex** |
| **One-Page System Design** | Detailed Mermaid Architecture Diagram (UI → API → DB → Auth → Stripe → AI) |
| **Database Schema** | Relational PostgreSQL ER Diagram & Constraints |
| **Basic API Documentation** | Comprehensive REST Endpoints Table |

---

## ⏱️ Total Time Taken
* **24 Hours** total development and architecture time.

## 🤖 AI Tools Used
* **OpenAI Codex**: Used as the primary AI coding assistant for designing the database models, Alembic migrations, FastAPI endpoints, Pydantic v2 schemas, Google OAuth authentication flow, Stripe webhook integration, and LangChain AI agent database tool-calling functions.

---

## 📐 One-Page System Design

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Frontend - React + TypeScript)"]
        ReactUI["React + TypeScript + Tailwind CSS + Shadcn UI"]
        GoogleAuthClient["Google OAuth SDK (@react-oauth/google)"]
    end

    subgraph API ["API Layer (FastAPI Backend)"]
        FastAPI["FastAPI App Server (Uvicorn)"]
        AuthModule["Google OAuth & JWT Service"]
        OrderModule["Order & Stock Engine"]
        PaymentModule["Stripe Payment Integration"]
        AIAgent["LangChain AI Support Agent"]
    end

    subgraph Data ["Data & Storage Layer"]
        Postgres[(PostgreSQL Database)]
        Alembic["Alembic Migrations"]
    end

    subgraph External ["External Services"]
        GoogleOAuth["Google Auth APIs"]
        StripeAPI["Stripe API & Webhooks"]
        LLMProvider["OpenAI / Gemini LLM"]
    end

    ReactUI -->|"HTTPS / REST API"| FastAPI
    GoogleAuthClient -->|"Obtains ID Token"| GoogleOAuth
    ReactUI -->|"Sends ID Token"| AuthModule
    AuthModule -->|"Verifies Token"| GoogleOAuth

    FastAPI -->|"ORM Queries"| Postgres
    OrderModule -->|"Stock Verification & Transactions"| Postgres
    
    PaymentModule -->|"Checkout Sessions & Webhooks"| StripeAPI
    ReactUI -->|"Redirects & Payment Verification"| PaymentModule

    ReactUI -->|"POST /ai/chat"| AIAgent
    AIAgent -->|"Tool Calls - Read-only Database SQL"| Postgres
    AIAgent -->|"Prompt & Context"| LLMProvider
```

---

## 🗄️ Database Schema

The PostgreSQL database enforces relational integrity, check constraints, non-negative pricing/stock (`price >= 0`, `stock >= 0`), and indexing on high-frequency query paths.

```mermaid
erDiagram
    USERS ||--o{ ORDERS : places
    PRODUCTS ||--o{ ORDER_ITEMS : contains
    ORDERS ||--|{ ORDER_ITEMS : includes

    USERS {
        uuid id PK
        string email UK
        string name
        string google_sub UK
        string role "CUSTOMER or ADMIN"
        timestamp created_at
    }

    PRODUCTS {
        uuid id PK
        string name
        text description
        numeric price
        integer stock
        string image_url
        boolean is_active
        timestamp created_at
    }

    ORDERS {
        uuid id PK
        uuid user_id FK
        string status "PENDING or PAID or FAILED or CANCELLED"
        numeric total_amount
        string payment_reference_id
        timestamp created_at
        timestamp updated_at
    }

    ORDER_ITEMS {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        integer quantity
        numeric unit_price
    }
```

### Schema Highlights:
* **`users`**: Customer and admin user records. Column `google_sub` indexes unique Google IDs.
* **`products`**: Inventory items with strict check constraints (`price >= 0`, `stock >= 0`).
* **`orders`**: Order tracking records (`pending`, `paid`, `failed`, `cancelled`). Indexed by `user_id`.
* **`order_items`**: Junction table recording unit prices at time of order creation.

---

## 🔌 Basic API Documentation

### 🔑 Authentication Endpoints (`/auth`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/google` | Public | Validates Google OAuth ID token, registers user if new, returns JWT token. |
| `POST` | `/auth/login` | Public | Standard login with email/password (testing/admin). |
| `GET` | `/auth/me` | Authenticated | Fetches profile info for current authenticated user. |

### 🛍️ Product Management (`/products` & `/admin/products`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/products` | Public | List all active products. |
| `GET` | `/products/{id}` | Public | Fetch single product details by ID. |
| `POST` | `/admin/products` | Admin | Create a new product. |
| `PUT` | `/admin/products/{id}` | Admin | Update existing product details & inventory stock. |
| `DELETE` | `/admin/products/{id}` | Admin | Delete a product. |

### 📦 Order Management (`/orders` & `/admin/orders`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/orders` | Authenticated | Validate item stock and create a pending order. |
| `GET` | `/orders/me` | Customer | Fetch current customer's order history. |
| `GET` | `/orders/{id}` | Customer | Fetch specific order (enforces user ownership). |
| `GET` | `/admin/orders` | Admin | Fetch all orders across all customers. |
| `PATCH` | `/admin/orders/{id}/status` | Admin | Update order status (`pending`, `paid`, `failed`, `cancelled`). |

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
