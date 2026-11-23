"""
REST Products API Test Suite (28 Parametrized Test Cases).
Covers catalog CRUD, pagination boundaries, filtering, sorting, schema validation, and security sanitization.
"""
import pytest
import allure
import jsonschema
import json


@allure.feature("Product Catalog Management")
@allure.story("REST Products API")
@pytest.mark.rest
class TestProductsRest:

    @pytest.fixture(autouse=True)
    def load_schemas(self):
        with open("schemas/product_schema.json") as f:
            self.product_schema = json.load(f)
        with open("schemas/paginated_products_schema.json") as f:
            self.paginated_schema = json.load(f)

    @pytest.mark.jira(ticket="PROD-201", severity="P2")
    @allure.title("TC-REST-14: List products returns default paginated list")
    def test_list_products_default_pagination(self, api_client):
        resp = api_client.get("/api/v1/products")
        resp.assert_status(200)
        data = resp.json()
        assert data["total"] >= 6
        assert len(data["items"]) <= 20
        jsonschema.validate(data, self.paginated_schema)

    @pytest.mark.jira(ticket="PROD-202", severity="P2")
    @allure.title("TC-REST-15: Get single product by valid ID")
    def test_get_single_product_by_id(self, api_client):
        resp = api_client.get("/api/v1/products/prod_01")
        resp.assert_status(200)
        data = resp.json()
        assert data["id"] == "prod_01"
        assert data["title"] == "Ergonomic Mechanical Keyboard"
        assert data["price"] == 149.99
        jsonschema.validate(data, self.product_schema)

    @pytest.mark.jira(ticket="PROD-203", severity="P3")
    @allure.title("TC-REST-16: Get non-existent product returns 404 Not Found")
    def test_get_nonexistent_product_returns_404(self, api_client):
        resp = api_client.get("/api/v1/products/prod_nonexistent_999")
        resp.assert_status(404)
        assert "not found" in resp.json()["detail"].lower()

    @pytest.mark.jira(ticket="PROD-204", severity="P3")
    @pytest.mark.parametrize(
        "limit,offset,expected_count",
        [
            (1, 0, 1),
            (2, 0, 2),
            (3, 2, 3),
            (10, 5, 1),
        ],
        ids=["limit_1_offset_0", "limit_2_offset_0", "limit_3_offset_2", "limit_10_offset_5"],
    )
    def test_products_pagination_boundaries(self, api_client, limit, offset, expected_count):
        resp = api_client.get("/api/v1/products", params={"limit": limit, "offset": offset})
        resp.assert_status(200)
        data = resp.json()
        assert len(data["items"]) == expected_count
        assert data["limit"] == limit
        assert data["offset"] == offset

    @pytest.mark.jira(ticket="PROD-205", severity="P4")
    @pytest.mark.parametrize(
        "limit,offset",
        [
            (0, 0),     # limit below minimum 1
            (101, 0),   # limit above maximum 100
            (-5, 0),    # negative limit
            (10, -1),   # negative offset
        ],
        ids=["limit_0", "limit_101", "limit_negative", "offset_negative"],
    )
    def test_products_invalid_pagination_parameters(self, api_client, limit, offset):
        resp = api_client.get("/api/v1/products", params={"limit": limit, "offset": offset})
        assert resp.status_code == 422  # Unprocessable Entity (FastAPI validation)

    @pytest.mark.jira(ticket="PROD-206", severity="P3")
    @pytest.mark.parametrize(
        "category,expected_items",
        [
            ("electronics", ["Ergonomic Mechanical Keyboard", "Ultra-Wide Gaming Monitor 34-inch", "Noise-Cancelling Wireless Headphones"]),
            ("apparel", ["Organic Cotton Developer Hoodie"]),
            ("books", ["Software Architecture Patterns Book"]),
        ],
        ids=["category_electronics", "category_apparel", "category_books"],
    )
    def test_products_category_filter(self, api_client, category, expected_items):
        resp = api_client.get("/api/v1/products", params={"category": category})
        resp.assert_status(200)
        titles = [item["title"] for item in resp.json()["items"]]
        for exp in expected_items:
            assert exp in titles

    @pytest.mark.jira(ticket="PROD-207", severity="P3")
    @pytest.mark.parametrize(
        "query,expected_min_count",
        [
            ("keyboard", 1),
            ("headphones", 1),
            ("nonexistent_search_query_xyz", 0),
        ],
        ids=["query_keyboard", "query_headphones", "query_no_results"],
    )
    def test_products_search_query(self, api_client, query, expected_min_count):
        resp = api_client.get("/api/v1/products", params={"q": query})
        resp.assert_status(200)
        data = resp.json()
        assert len(data["items"]) >= expected_min_count

    @pytest.mark.jira(ticket="PROD-208", severity="P3")
    def test_products_price_range_filtering(self, api_client):
        resp = api_client.get("/api/v1/products", params={"min_price": 50.0, "max_price": 200.0})
        resp.assert_status(200)
        for item in resp.json()["items"]:
            assert 50.0 <= item["price"] <= 200.0

    @pytest.mark.jira(ticket="PROD-209", severity="P3")
    @pytest.mark.parametrize(
        "sort_by,sort_order",
        [
            ("price", "asc"),
            ("price", "desc"),
            ("title", "asc"),
        ],
        ids=["sort_price_asc", "sort_price_desc", "sort_title_asc"],
    )
    def test_products_sorting(self, api_client, sort_by, sort_order):
        resp = api_client.get("/api/v1/products", params={"sort_by": sort_by, "sort_order": sort_order})
        resp.assert_status(200)
        items = resp.json()["items"]
        values = [it[sort_by] for it in items]
        if sort_order == "asc":
            assert values == sorted(values)
        else:
            assert values == sorted(values, reverse=True)

    @pytest.mark.jira(ticket="PROD-210", severity="P2")
    @allure.title("TC-REST-23: Admin user creates new product successfully")
    def test_create_product_admin_success(self, admin_client):
        payload = {
            "title": "USB-C Multiport Hub",
            "description": "8-in-1 4K HDMI, Gigabit Ethernet, 100W PD Pass-through.",
            "price": 49.99,
            "category": "electronics",
            "stock": 50,
        }
        resp = admin_client.post("/api/v1/products", json=payload)
        resp.assert_status(201)
        data = resp.json()
        assert data["title"] == payload["title"]
        assert data["price"] == payload["price"]
        assert "id" in data

    @pytest.mark.jira(ticket="SEC-211", severity="P1")
    @allure.title("TC-REST-24: Standard user cannot create product (RBAC 403 Forbidden)")
    def test_create_product_forbidden_standard_user(self, user_client):
        payload = {
            "title": "Unauthorized Product Injection",
            "description": "Attempting privilege escalation.",
            "price": 10.0,
            "category": "accessories",
            "stock": 1,
        }
        resp = user_client.post("/api/v1/products", json=payload)
        resp.assert_status(403)
        assert "Admin privilege required" in resp.json()["detail"]

    @pytest.mark.jira(ticket="PROD-212", severity="P4")
    @pytest.mark.parametrize(
        "invalid_field,payload",
        [
            ("negative_price", {"title": "Bad", "description": "d", "price": -10.0, "category": "electronics", "stock": 10}),
            ("empty_title", {"title": "", "description": "d", "price": 15.0, "category": "electronics", "stock": 10}),
            ("invalid_category", {"title": "Bad Cat", "description": "d", "price": 15.0, "category": "unknown_cat", "stock": 10}),
        ],
        ids=["negative_price", "empty_title", "invalid_category"],
    )
    def test_create_product_validation_errors(self, admin_client, invalid_field, payload):
        resp = admin_client.post("/api/v1/products", json=payload)
        assert resp.status_code == 422

    @pytest.mark.jira(ticket="PROD-213", severity="P2")
    @allure.title("TC-REST-26: Admin updates product details")
    def test_update_product_admin_success(self, admin_client):
        resp = admin_client.put("/api/v1/products/prod_01", json={"price": 139.99, "stock": 40})
        resp.assert_status(200)
        data = resp.json()
        assert data["price"] == 139.99
        assert data["stock"] == 40

    @pytest.mark.jira(ticket="PROD-214", severity="P2")
    @allure.title("TC-REST-27: Admin deletes product")
    def test_delete_product_admin_success(self, admin_client):
        # Create temporary product to delete
        create_resp = admin_client.post(
            "/api/v1/products",
            json={"title": "Item To Delete", "description": "Temporary", "price": 12.0, "category": "books", "stock": 5},
        )
        prod_id = create_resp.json()["id"]

        del_resp = admin_client.delete(f"/api/v1/products/{prod_id}")
        del_resp.assert_status(200)

        # Confirm 404 on subsequent get
        get_resp = admin_client.get(f"/api/v1/products/{prod_id}")
        get_resp.assert_status(404)

    @pytest.mark.jira(ticket="SEC-215", severity="P1")
    @allure.title("TC-REST-28: SQL Injection query payload safely sanitized without error")
    def test_sql_injection_payload_safe_handling(self, api_client):
        sqli_query = "' OR '1'='1' -- ; DROP TABLE users;"
        resp = api_client.get("/api/v1/products", params={"q": sqli_query})
        resp.assert_status(200)
        assert isinstance(resp.json()["items"], list)

    @pytest.mark.jira(ticket="SEC-216", severity="P1")
    @allure.title("TC-REST-29: XSS script payload sanitized upon product creation")
    def test_xss_script_payload_sanitization(self, admin_client):
        xss_title = "<script>alert('pwned')</script>Smart Hub"
        resp = admin_client.post(
            "/api/v1/products",
            json={"title": xss_title, "description": "Test XSS sanitization", "price": 89.99, "category": "electronics", "stock": 10},
        )
        resp.assert_status(201)
        data = resp.json()
        # Must be HTML escaped
        assert "<script>" not in data["title"]
        assert "&lt;script&gt;" in data["title"]
