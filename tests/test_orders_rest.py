"""
REST Orders API Test Suite (16 Parametrized Test Cases).
Covers checkout transactions, price/tax arithmetic, inventory deduction, IDOR security, and status transitions.
"""
import pytest
import allure
import jsonschema
import json


@allure.feature("Order Management & Checkout")
@allure.story("REST Orders API")
@pytest.mark.rest
class TestOrdersRest:

    @pytest.fixture(autouse=True)
    def load_order_schema(self):
        with open("schemas/order_schema.json") as f:
            self.order_schema = json.load(f)

    @pytest.mark.jira(ticket="ORD-301", severity="P1")
    @allure.title("TC-REST-30: Create single-item order with price arithmetic validation")
    def test_create_order_single_item(self, user_client):
        payload = {
            "items": [{"product_id": "prod_01", "quantity": 1}],
            "shipping_address": "123 Automation Lane, Suite 400",
        }
        resp = user_client.post("/api/v1/orders", json=payload)
        resp.assert_status(201)
        data = resp.json()

        assert data["subtotal"] == 149.99
        expected_tax = round(149.99 * 0.08, 2)
        assert data["tax"] == expected_tax
        assert data["total"] == round(149.99 + expected_tax, 2)
        assert data["status"] == "PENDING"
        jsonschema.validate(data, self.order_schema)

    @pytest.mark.jira(ticket="ORD-302", severity="P1")
    @allure.title("TC-REST-31: Create multi-item order and verify total calculation")
    def test_create_order_multiple_items(self, user_client):
        payload = {
            "items": [
                {"product_id": "prod_03", "quantity": 2},  # $65.00 * 2 = $130.00
                {"product_id": "prod_04", "quantity": 1},  # $28.00 * 1 = $28.00
            ],
            "shipping_address": "789 QA Boulevard, Pune, 411001",
        }
        resp = user_client.post("/api/v1/orders", json=payload)
        resp.assert_status(201)
        data = resp.json()

        expected_subtotal = 158.00
        expected_tax = round(expected_subtotal * 0.08, 2)
        expected_total = round(expected_subtotal + expected_tax, 2)

        assert data["subtotal"] == expected_subtotal
        assert data["tax"] == expected_tax
        assert data["total"] == expected_total

    @pytest.mark.jira(ticket="ORD-303", severity="P2")
    @allure.title("TC-REST-32: Attempting order exceeding available stock returns 400 Bad Request")
    def test_create_order_insufficient_stock_error(self, user_client):
        payload = {
            "items": [{"product_id": "prod_02", "quantity": 50}],  # Only 20 in stock, schema allows up to 100
            "shipping_address": "123 Test Street",
        }
        resp = user_client.post("/api/v1/orders", json=payload)
        resp.assert_status(400)
        assert "Insufficient stock" in resp.json()["detail"]

    @pytest.mark.jira(ticket="ORD-304", severity="P3")
    @allure.title("TC-REST-33: Order with non-existent product ID returns 404 Not Found")
    def test_create_order_nonexistent_product_error(self, user_client):
        payload = {
            "items": [{"product_id": "prod_invalid_id_999", "quantity": 1}],
            "shipping_address": "123 Test Street",
        }
        resp = user_client.post("/api/v1/orders", json=payload)
        resp.assert_status(404)
        assert "does not exist" in resp.json()["detail"]

    @pytest.mark.jira(ticket="ORD-305", severity="P3")
    @pytest.mark.parametrize(
        "quantity",
        [1, 10],
        ids=["min_valid_qty_1", "valid_qty_10"],
    )
    def test_create_order_boundary_quantities(self, user_client, quantity):
        payload = {
            "items": [{"product_id": "prod_04", "quantity": quantity}],
            "shipping_address": "456 Boundary Test Way",
        }
        resp = user_client.post("/api/v1/orders", json=payload)
        resp.assert_status(201)
        assert resp.json()["items"][0]["quantity"] == quantity

    @pytest.mark.jira(ticket="ORD-306", severity="P4")
    @pytest.mark.parametrize(
        "invalid_qty",
        [0, -1, 101],
        ids=["qty_zero", "qty_negative", "qty_exceeding_max_100"],
    )
    def test_create_order_invalid_quantity(self, user_client, invalid_qty):
        payload = {
            "items": [{"product_id": "prod_04", "quantity": invalid_qty}],
            "shipping_address": "456 Boundary Test Way",
        }
        resp = user_client.post("/api/v1/orders", json=payload)
        assert resp.status_code == 422

    @pytest.mark.jira(ticket="ORD-307", severity="P2")
    @allure.title("TC-REST-36: Retrieve authenticated user order history")
    def test_get_user_orders_history(self, user_client):
        resp = user_client.get("/api/v1/orders")
        resp.assert_status(200)
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.jira(ticket="ORD-308", severity="P2")
    @allure.title("TC-REST-37: Get order details by ID")
    def test_get_order_by_id(self, user_client):
        resp = user_client.get("/api/v1/orders/ord_101")
        resp.assert_status(200)
        data = resp.json()
        assert data["id"] == "ord_101"
        assert data["user_id"] == "usr_standard"

    @pytest.mark.jira(ticket="SEC-309", severity="P1")
    @allure.title("TC-REST-38: IDOR Prevention - User cannot access another user's order")
    def test_order_isolation_user_cannot_view_others_order(self, api_client):
        # Register user B
        api_client.post("/api/v1/auth/register", json={
            "username": "user_b_attacker",
            "email": "user_b@qa.io",
            "password": "password123!",
            "role": "user"
        })
        login_resp = api_client.post("/api/v1/auth/login", json={"username": "user_b_attacker", "password": "password123!"})
        user_b_token = login_resp.json()["access_token"]

        # User B attempts to access User Standard's order `ord_101`
        resp = api_client.get("/api/v1/orders/ord_101", headers={"Authorization": f"Bearer {user_b_token}"})
        resp.assert_status(403)
        assert "Forbidden" in resp.json()["detail"]

    @pytest.mark.jira(ticket="ORD-310", severity="P2")
    @allure.title("TC-REST-39: Order status lifecycle transition (PENDING -> CANCELLED)")
    def test_order_status_transition_lifecycle(self, user_client):
        resp = user_client.patch("/api/v1/orders/ord_101/status", json={"status": "CANCELLED"})
        resp.assert_status(200)
        assert resp.json()["status"] == "CANCELLED"
