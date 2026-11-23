# ⚡ REST & GraphQL API Test Automation Framework

[![CI Status](https://github.com/Sarthakkapadne/rest-graphql-api-test-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/Sarthakkapadne/rest-graphql-api-test-framework/actions)
[![Tests Passing](https://img.shields.io/badge/tests-77%20passed-brightgreen.svg)](https://github.com/Sarthakkapadne/rest-graphql-api-test-framework)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![Strawberry GraphQL](https://img.shields.io/badge/GraphQL-Strawberry-red.svg)](https://strawberry.rocks/)
[![Jira Severity](https://img.shields.io/badge/Jira-P1--P4%20Triage-purple.svg)](https://www.atlassian.com/software/jira)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An enterprise-grade, data-driven API Test Automation Framework covering **REST** and **GraphQL** protocols with **77+ parameterized test scenarios** (positive, negative, boundary, and JSON Schema contract validation). Built-in custom **Jira-style defect classification (P1–P4 severity)** with auto-generated interactive HTML test reports, bundled target API server, and automated **GitHub Actions CI/CD**.

---

## 🏛️ System Architecture

```
rest-graphql-api-test-framework/
├── server/                   # Bundled Full-Stack Target API Service
│   ├── app.py                # FastAPI app mounting REST router & Strawberry GraphQL
│   ├── auth.py               # JWT access/refresh token signing & RBAC dependencies
│   ├── db.py                 # Thread-safe in-memory database with seed records
│   ├── models.py             # Pydantic schemas (User, Product, Order, Token)
│   ├── rest_routes.py        # REST endpoints (/auth, /products, /orders, /health)
│   └── graphql_schema.py     # GraphQL Queries (me, product, order) & Mutations
├── clients/                  # Robust Test Clients
│   ├── rest_client.py        # Session handling, auto JWT bearer injection, timing
│   └── graphql_client.py     # Query/Mutation execution, error parsing, payload typing
├── schemas/                  # JSON Schemas for Strict Contract Testing
│   ├── auth_response_schema.json
│   ├── product_schema.json
│   ├── paginated_products_schema.json
│   └── order_schema.json
├── plugins/                  # Custom Jira Severity Reporting Plugin
│   └── jira_defect_plugin.py # P1-P4 defect collector & HTML dashboard generator
├── tests/                    # 77 Parameterized Test Scenarios
│   ├── test_auth_rest.py     # 15 authentication & security tests
│   ├── test_products_rest.py # 28 catalog CRUD, filter, sort & SQLi/XSS tests
│   ├── test_orders_rest.py   # 15 checkout, price math & IDOR isolation tests
│   └── test_graphql_api.py   # 19 GraphQL introspection, query & mutation tests
├── reports/                  # Generated HTML reports & Allure raw results
├── conftest.py               # Background server lifecycle fixture & auth clients
├── pytest.ini                # Pytest markers and configuration
├── run_tests.py              # CLI test runner and server launcher
└── .github/workflows/ci.yml  # GitHub Actions CI workflow
```

---

## 🎯 Jira Defect Severity Classification (P1–P4)

The framework enforces industry-standard defect triage categorization across all test scenarios:

| Severity Tier | Scope & Impact | Total Tests | Pass Rate |
| :--- | :--- | :--- | :--- |
| **🔴 P1 - Blocker** | Security breaches, JWT token revocation, ACID transaction drop, IDOR vulnerability, SQLi/XSS injection | 19 | **100.0%** (19/19) |
| **🟡 P2 - Critical** | Core CRUD operations, order price/tax calculation, duplicate user conflict, GraphQL mutation integrity | 18 | **100.0%** (18/18) |
| **🟣 P3 - Major** | Search querying, category filters, pagination offsets, boundary limits, GraphQL query parameters | 28 | **100.0%** (28/28) |
| **🔵 P4 - Minor** | Input field length validation, malformed payload error schema, query syntax error messaging | 12 | **100.0%** (12/12) |
| **Total** | **Comprehensive Full-Stack Coverage** | **77** | **100.0%** |

---

## 🧪 Detailed Test Matrix (77 Scenarios)

### 1. REST Authentication & Security (`tests/test_auth_rest.py`)
- **TC-REST-01**: Valid login returns access & refresh tokens conforming to JSON Schema `[P1]`.
- **TC-REST-02**: Invalid password returns `401 Unauthorized` `[P1]`.
- **TC-REST-03**: Non-existent user login returns `401 Unauthorized` `[P1]`.
- **TC-REST-04**: New user registration with profile creation `[P2]`.
- **TC-REST-05**: Duplicate username registration triggers `409 Conflict` `[P2]`.
- **TC-REST-06**: Duplicate email registration triggers `409 Conflict` `[P2]`.
- **TC-REST-07 [Parametrized x3]**: Empty credentials validation (empty username, empty password, both empty) `[P3]`.
- **TC-REST-08**: Protected `/auth/me` endpoint returns authenticated profile `[P1]`.
- **TC-REST-09**: Protected route without Authorization header rejected `[P1]`.
- **TC-REST-10**: Malformed Bearer token format rejected `[P1]`.
- **TC-REST-11**: Expired JWT signature rejected `[P1]`.
- **TC-REST-12**: Refresh token rotation issues new access token `[P2]`.
- **TC-REST-13**: Logout invalidates active token (revocation check) `[P1]`.

### 2. REST Products API (`tests/test_products_rest.py`)
- **TC-REST-14**: List products default pagination & JSON schema validation `[P2]`.
- **TC-REST-15**: Get single product by valid ID `[P2]`.
- **TC-REST-16**: Get non-existent product returns `404 Not Found` `[P3]`.
- **TC-REST-17 [Parametrized x4]**: Boundary pagination limits (`limit=1`, `limit=2`, `limit=3`, `limit=10`) `[P3]`.
- **TC-REST-18 [Parametrized x4]**: Invalid pagination bounds (`limit=0`, `limit=101`, `limit=-5`, `offset=-1`) `[P4]`.
- **TC-REST-19 [Parametrized x3]**: Category filtering across `electronics`, `apparel`, `books` `[P3]`.
- **TC-REST-20 [Parametrized x3]**: Search query matching & empty search results `[P3]`.
- **TC-REST-21**: Price range filtering (`min_price` and `max_price`) `[P3]`.
- **TC-REST-22 [Parametrized x3]**: Sorting by price ASC/DESC and title ASC `[P3]`.
- **TC-REST-23**: Admin creates new product with `201 Created` `[P2]`.
- **TC-REST-24**: Standard user forbidden from product creation (`403 Forbidden` RBAC check) `[P1]`.
- **TC-REST-25 [Parametrized x3]**: Product payload validation (negative price, empty title, invalid category) `[P4]`.
- **TC-REST-26**: Admin updates product price and stock `[P2]`.
- **TC-REST-27**: Admin deletes product and verifies 404 deletion `[P2]`.
- **TC-REST-28**: SQL injection string safely handled without syntax explosion `[P1]`.
- **TC-REST-29**: XSS `<script>` tag sanitized and escaped in product title `[P1]`.

### 3. REST Orders API (`tests/test_orders_rest.py`)
- **TC-REST-30**: Create single-item order with price arithmetic validation (subtotal + 8% tax = total) `[P1]`.
- **TC-REST-31**: Create multi-item order with line-item pricing `[P1]`.
- **TC-REST-32**: Insufficient inventory triggers `400 Bad Request` `[P2]`.
- **TC-REST-33**: Non-existent product ID in order triggers `404 Not Found` `[P3]`.
- **TC-REST-34 [Parametrized x2]**: Boundary order quantities (`quantity=1`, `quantity=10`) `[P3]`.
- **TC-REST-35 [Parametrized x3]**: Invalid order quantities (`quantity=0`, `quantity=-1`, `quantity=101`) `[P4]`.
- **TC-REST-36**: Retrieve authenticated user order history `[P2]`.
- **TC-REST-37**: Retrieve order details by ID `[P2]`.
- **TC-REST-38**: IDOR vulnerability prevention (User cannot access another user's order) `[P1]`.
- **TC-REST-39**: Order status lifecycle transition (`PENDING` -> `CANCELLED`) `[P2]`.

### 4. GraphQL API (`tests/test_graphql_api.py`)
- **TC-GQL-01**: Schema introspection query (`__schema`) validates types `[P3]`.
- **TC-GQL-02**: Query single product by ID returns fields `[P2]`.
- **TC-GQL-03**: Query non-existent product returns null `[P3]`.
- **TC-GQL-04 [Parametrized x2]**: Query products with `limit` and `offset` variables `[P3]`.
- **TC-GQL-05 [Parametrized x2]**: Query products with category filter `[P3]`.
- **TC-GQL-06**: Query products with search keyword `[P3]`.
- **TC-GQL-07**: Query current user profile (`me`) with valid JWT `[P1]`.
- **TC-GQL-08**: Query `me` with invalid token returns null `[P2]`.
- **TC-GQL-09**: Mutation `login` with valid credentials returns access token `[P1]`.
- **TC-GQL-10**: Mutation `login` with invalid credentials returns GraphQL error `[P1]`.
- **TC-GQL-11**: Mutation `createProduct` with Admin JWT `[P2]`.
- **TC-GQL-12**: Mutation `createProduct` with user token rejected `[P1]`.
- **TC-GQL-13**: Mutation `createOrder` completes order with tax math `[P1]`.
- **TC-GQL-14**: Mutation `createOrder` with excessive quantity triggers error `[P2]`.
- **TC-GQL-15**: Mutation `cancelOrder` transitions status `[P2]`.
- **TC-GQL-16**: Malformed GraphQL syntax error handling `[P4]`.
- **TC-GQL-17**: Query requesting non-existent field rejected by schema validator `[P4]`.

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
git clone https://github.com/Sarthakkapadne/rest-graphql-api-test-framework.git
cd rest-graphql-api-test-framework

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Run Test Automation Suite
The tests will **automatically spin up the target API server** in the background:
```bash
# Run all 77 test cases with Jira & HTML reports
python run_tests.py

# Run only REST tests
python run_tests.py --protocol=rest

# Run only GraphQL tests
python run_tests.py --protocol=graphql

# Run only P1 Blocker tests
python run_tests.py --severity=P1
```

### 3. Start Target API Server Manually (Optional)
```bash
python run_tests.py --mode=server
```
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- GraphiQL Playground: [http://127.0.0.1:8000/graphql](http://127.0.0.1:8000/graphql)
- ReDoc Reference: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 4. View Test Reports
- **Jira Defect Severity Report**: Open `reports/jira_defect_report.html` in your browser.
- **Pytest HTML Report**: Open `reports/report.html`.
- **Markdown Summary**: View `reports/jira_defect_summary.md`.

---

## 🔄 CI/CD Pipeline
Configured via `.github/workflows/ci.yml`:
1. Executes on every PR and commit to `main`.
2. Starts target API service headlessly.
3. Executes 77 test cases covering REST, GraphQL, schemas, and security.
4. Generates and uploads Jira severity breakdown and HTML reports as downloadable artifacts.

---

## 👨‍💻 Author
**Sarthak Kapadne**  
QA Engineer & Test Automation Specialist  
- GitHub: [@Sarthakkapadne](https://github.com/Sarthakkapadne)  
- LinkedIn: [sarthak-kapadne](https://linkedin.com/in/sarthak-kapadne)  
- Email: [sarthakkapadne6086@gmail.com](mailto:sarthakkapadne6086@gmail.com)
