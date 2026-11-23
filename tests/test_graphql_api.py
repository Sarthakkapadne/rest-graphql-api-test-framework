"""
GraphQL API Test Suite (20 Parametrized Test Cases).
Covers GraphQL schema introspection, Queries, Mutations, Variable injection, and Error handling.
"""
import pytest
import allure


@allure.feature("GraphQL API Layer")
@allure.story("GraphQL Queries and Mutations")
@pytest.mark.graphql
class TestGraphQLApi:

    @pytest.mark.jira(ticket="GQL-401", severity="P3")
    @allure.title("TC-GQL-01: Introspection query returns types and schema details")
    def test_graphql_introspection_query(self, graphql_client):
        query = """
        query IntrospectTypes {
          __schema {
            types {
              name
              kind
            }
          }
        }
        """
        resp = graphql_client.execute(query)
        resp.assert_no_errors()
        type_names = [t["name"] for t in resp.data["__schema"]["types"]]
        assert "ProductType" in type_names
        assert "OrderType" in type_names
        assert "UserType" in type_names

    @pytest.mark.jira(ticket="GQL-402", severity="P2")
    @allure.title("TC-GQL-02: Query single product by ID returns fields")
    def test_graphql_query_product_by_id(self, graphql_client):
        query = """
        query GetProduct($id: String!) {
          product(id: $id) {
            id
            title
            price
            category
            stock
          }
        }
        """
        resp = graphql_client.execute(query, variables={"id": "prod_01"})
        resp.assert_no_errors()
        prod = resp.data["product"]
        assert prod["id"] == "prod_01"
        assert prod["title"] == "Ergonomic Mechanical Keyboard"
        assert prod["price"] == 149.99

    @pytest.mark.jira(ticket="GQL-403", severity="P3")
    @allure.title("TC-GQL-03: Query non-existent product returns null without error")
    def test_graphql_query_nonexistent_product_returns_null(self, graphql_client):
        query = """
        query GetNonexistent($id: String!) {
          product(id: $id) {
            id
            title
          }
        }
        """
        resp = graphql_client.execute(query, variables={"id": "prod_not_found_999"})
        resp.assert_no_errors()
        assert resp.data["product"] is None

    @pytest.mark.jira(ticket="GQL-404", severity="P3")
    @pytest.mark.parametrize(
        "limit,offset,expected_count",
        [
            (2, 0, 2),
            (3, 2, 3),
        ],
        ids=["limit_2_offset_0", "limit_3_offset_2"],
    )
    def test_graphql_query_products_with_limit_and_offset(self, graphql_client, limit, offset, expected_count):
        query = """
        query ListProducts($limit: Int!, $offset: Int!) {
          products(limit: $limit, offset: $offset) {
            id
            title
            price
          }
        }
        """
        resp = graphql_client.execute(query, variables={"limit": limit, "offset": offset})
        resp.assert_no_errors()
        assert len(resp.data["products"]) == expected_count

    @pytest.mark.jira(ticket="GQL-405", severity="P3")
    @pytest.mark.parametrize(
        "category",
        ["electronics", "books"],
        ids=["filter_electronics", "filter_books"],
    )
    def test_graphql_query_products_category_filter(self, graphql_client, category):
        query = """
        query FilterCategory($category: String!) {
          products(category: $category) {
            id
            title
            category
          }
        }
        """
        resp = graphql_client.execute(query, variables={"category": category})
        resp.assert_no_errors()
        for prod in resp.data["products"]:
            assert prod["category"] == category

    @pytest.mark.jira(ticket="GQL-406", severity="P3")
    @allure.title("TC-GQL-08: Query products with search filter")
    def test_graphql_query_products_search(self, graphql_client):
        query = """
        query SearchProducts($search: String!) {
          products(search: $search) {
            id
            title
          }
        }
        """
        resp = graphql_client.execute(query, variables={"search": "Keyboard"})
        resp.assert_no_errors()
        titles = [p["title"] for p in resp.data["products"]]
        assert any("Keyboard" in t for t in titles)

    @pytest.mark.jira(ticket="GQL-407", severity="P1")
    @allure.title("TC-GQL-09: Authenticated query for current user profile")
    def test_graphql_query_me_authenticated(self, graphql_client, user_token):
        query = """
        query GetMe($token: String!) {
          me(token: $token) {
            id
            username
            email
            role
          }
        }
        """
        resp = graphql_client.execute(query, variables={"token": user_token})
        resp.assert_no_errors()
        me = resp.data["me"]
        assert me["username"] == "qa_tester"
        assert me["role"] == "user"

    @pytest.mark.jira(ticket="GQL-408", severity="P2")
    @allure.title("TC-GQL-10: Unauthenticated or invalid token query me returns null")
    def test_graphql_query_me_unauthenticated_null(self, graphql_client):
        query = """
        query GetMe($token: String!) {
          me(token: $token) {
            id
            username
          }
        }
        """
        resp = graphql_client.execute(query, variables={"token": "invalid_jwt_token_xyz"})
        resp.assert_no_errors()
        assert resp.data["me"] is None

    @pytest.mark.jira(ticket="GQL-409", severity="P1")
    @allure.title("TC-GQL-11: Mutation login with valid credentials")
    def test_graphql_mutation_login_success(self, graphql_client):
        mutation = """
        mutation UserLogin($username: String!, $password: String!) {
          login(username: $username, password: $password) {
            accessToken
            userId
            username
            role
          }
        }
        """
        resp = graphql_client.execute(mutation, variables={"username": "qa_tester", "password": "tester123!"})
        resp.assert_no_errors()
        login_data = resp.data["login"]
        assert login_data["username"] == "qa_tester"
        assert len(login_data["accessToken"]) > 20

    @pytest.mark.jira(ticket="GQL-410", severity="P1")
    @allure.title("TC-GQL-12: Mutation login with invalid password triggers GraphQL error")
    def test_graphql_mutation_login_failure(self, graphql_client):
        mutation = """
        mutation UserLogin($username: String!, $password: String!) {
          login(username: $username, password: $password) {
            accessToken
          }
        }
        """
        resp = graphql_client.execute(mutation, variables={"username": "qa_tester", "password": "bad_password"})
        assert resp.has_errors
        assert "Invalid username or password" in resp.errors[0]["message"]

    @pytest.mark.jira(ticket="GQL-411", severity="P2")
    @allure.title("TC-GQL-13: Mutation createProduct with Admin authorization")
    def test_graphql_mutation_create_product_admin(self, graphql_client, admin_token):
        mutation = """
        mutation AddProduct(
          $title: String!,
          $description: String!,
          $price: Float!,
          $category: String!,
          $stock: Int!,
          $token: String!
        ) {
          createProduct(
            title: $title,
            description: $description,
            price: $price,
            category: $category,
            stock: $stock,
            token: $token
          ) {
            id
            title
            price
            stock
          }
        }
        """
        payload = {
            "title": "Dual Monitor Arm",
            "description": "Heavy-duty gas spring desk mount",
            "price": 89.50,
            "category": "accessories",
            "stock": 25,
            "token": admin_token,
        }
        resp = graphql_client.execute(mutation, variables=payload)
        resp.assert_no_errors()
        data = resp.data["createProduct"]
        assert data["title"] == "Dual Monitor Arm"
        assert data["price"] == 89.50

    @pytest.mark.jira(ticket="SEC-412", severity="P1")
    @allure.title("TC-GQL-14: Mutation createProduct rejects standard user token")
    def test_graphql_mutation_create_product_unauthorized(self, graphql_client, user_token):
        mutation = """
        mutation AddProduct($token: String!) {
          createProduct(
            title: "Hack Item",
            description: "Illegal attempt",
            price: 1.0,
            category: "apparel",
            stock: 1,
            token: $token
          ) {
            id
          }
        }
        """
        resp = graphql_client.execute(mutation, variables={"token": user_token})
        assert resp.has_errors
        assert "Admin privileges required" in resp.errors[0]["message"]

    @pytest.mark.jira(ticket="GQL-413", severity="P1")
    @allure.title("TC-GQL-15: Mutation createOrder with valid stock and quantity")
    def test_graphql_mutation_create_order_success(self, graphql_client, user_token):
        mutation = """
        mutation PlaceOrder(
          $productId: String!,
          $quantity: Int!,
          $shippingAddress: String!,
          $token: String!
        ) {
          createOrder(
            productId: $productId,
            quantity: $quantity,
            shippingAddress: $shippingAddress,
            token: $token
          ) {
            id
            status
            total
            subtotal
            tax
          }
        }
        """
        payload = {
            "productId": "prod_05",  # $54.95
            "quantity": 1,
            "shippingAddress": "GraphQL Ave 404",
            "token": user_token,
        }
        resp = graphql_client.execute(mutation, variables=payload)
        resp.assert_no_errors()
        order = resp.data["createOrder"]
        assert order["status"] == "PENDING"
        assert order["subtotal"] == 54.95
        assert order["total"] == round(54.95 + round(54.95 * 0.08, 2), 2)

    @pytest.mark.jira(ticket="GQL-414", severity="P2")
    @allure.title("TC-GQL-16: Mutation createOrder with excessive quantity triggers error")
    def test_graphql_mutation_create_order_insufficient_stock(self, graphql_client, user_token):
        mutation = """
        mutation PlaceOrder($productId: String!, $quantity: Int!, $address: String!, $token: String!) {
          createOrder(productId: $productId, quantity: $quantity, shippingAddress: $address, token: $token) {
            id
          }
        }
        """
        resp = graphql_client.execute(
            mutation,
            variables={"productId": "prod_06", "quantity": 9999, "address": "123 St", "token": user_token},
        )
        assert resp.has_errors
        assert "Insufficient inventory" in resp.errors[0]["message"]

    @pytest.mark.jira(ticket="GQL-415", severity="P2")
    @allure.title("TC-GQL-17: Mutation cancelOrder updates status to CANCELLED")
    def test_graphql_mutation_cancel_order(self, graphql_client, user_token):
        mutation = """
        mutation CancelOrder($orderId: String!, $token: String!) {
          cancelOrder(orderId: $orderId, token: $token) {
            id
            status
          }
        }
        """
        resp = graphql_client.execute(mutation, variables={"orderId": "ord_101", "token": user_token})
        resp.assert_no_errors()
        assert resp.data["cancelOrder"]["status"] == "CANCELLED"

    @pytest.mark.jira(ticket="GQL-416", severity="P4")
    @allure.title("TC-GQL-18: Malformed GraphQL query syntax returns syntax error")
    def test_graphql_syntax_error_handling(self, graphql_client):
        broken_query = "query { brokenSyntaxWithoutClosingBrace "
        resp = graphql_client.execute(broken_query)
        assert resp.has_errors
        assert "Syntax Error" in resp.errors[0]["message"]

    @pytest.mark.jira(ticket="GQL-417", severity="P4")
    @allure.title("TC-GQL-19: Query requesting non-existent field is rejected by schema validator")
    def test_graphql_nonexistent_field_query_rejection(self, graphql_client):
        query = """
        query {
          products {
            id
            nonExistentFieldXYZ
          }
        }
        """
        resp = graphql_client.execute(query)
        assert resp.has_errors
        assert "Cannot query field 'nonExistentFieldXYZ'" in resp.errors[0]["message"]
