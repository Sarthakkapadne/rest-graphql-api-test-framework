"""
REST Authentication & Access Control Test Suite (16 Parametrized Test Cases).
Covers JWT issuance, validation, refresh, revocation, schema validation, and RBAC security.
"""
import pytest
import allure
import jsonschema
import json
import time
import jwt
from server.auth import JWT_SECRET, JWT_ALGORITHM


@allure.feature("Authentication & Identity")
@allure.story("REST Auth Endpoints")
@pytest.mark.rest
class TestAuthRest:

    @pytest.fixture(autouse=True)
    def load_schema(self):
        with open("schemas/auth_response_schema.json") as f:
            self.auth_schema = json.load(f)

    @pytest.mark.jira(ticket="SEC-101", severity="P1")
    @allure.title("TC-REST-01: Valid user login returns signed JWT tokens")
    def test_valid_user_login(self, api_client):
        resp = api_client.post("/api/v1/auth/login", json={"username": "qa_tester", "password": "tester123!"})
        resp.assert_status(200)
        data = resp.json()
        assert data["username"] == "qa_tester"
        assert data["role"] == "user"
        assert "access_token" in data
        assert "refresh_token" in data
        jsonschema.validate(data, self.auth_schema)

    @pytest.mark.jira(ticket="SEC-102", severity="P1")
    @allure.title("TC-REST-02: Invalid password returns 401 Unauthorized")
    def test_invalid_password_returns_401(self, api_client):
        resp = api_client.post("/api/v1/auth/login", json={"username": "qa_tester", "password": "wrong_password!"})
        resp.assert_status(401)
        assert "Invalid username or password" in resp.json()["detail"]

    @pytest.mark.jira(ticket="SEC-103", severity="P1")
    @allure.title("TC-REST-03: Non-existent user login returns 401")
    def test_nonexistent_user_login_returns_401(self, api_client):
        resp = api_client.post("/api/v1/auth/login", json={"username": "non_existent_user_999", "password": "password"})
        resp.assert_status(401)
        assert "Invalid username or password" in resp.json()["detail"]

    @pytest.mark.jira(ticket="SEC-104", severity="P2")
    @allure.title("TC-REST-04: User registration creates profile")
    def test_valid_user_registration(self, api_client):
        unique_user = f"new_qa_{int(time.time() * 1000) % 10000}"
        payload = {
            "username": unique_user,
            "email": f"{unique_user}@example.com",
            "password": "secure_password_123",
            "role": "user",
        }
        resp = api_client.post("/api/v1/auth/register", json=payload)
        resp.assert_status(201)
        data = resp.json()
        assert data["username"] == unique_user
        assert data["role"] == "user"

    @pytest.mark.jira(ticket="SEC-105", severity="P2")
    @allure.title("TC-REST-05: Duplicate username registration returns 409 Conflict")
    def test_duplicate_username_conflict(self, api_client):
        payload = {
            "username": "qa_tester",
            "email": "another_email@example.com",
            "password": "secure_password_123",
            "role": "user",
        }
        resp = api_client.post("/api/v1/auth/register", json=payload)
        resp.assert_status(409)
        assert "already registered" in resp.json()["detail"]

    @pytest.mark.jira(ticket="SEC-106", severity="P2")
    @allure.title("TC-REST-06: Duplicate email registration returns 409 Conflict")
    def test_duplicate_email_conflict(self, api_client):
        payload = {
            "username": "unique_qa_username_xyz",
            "email": "tester@qa-suite.io",
            "password": "secure_password_123",
            "role": "user",
        }
        resp = api_client.post("/api/v1/auth/register", json=payload)
        resp.assert_status(409)
        assert "already registered" in resp.json()["detail"]

    @pytest.mark.jira(ticket="SEC-107", severity="P3")
    @pytest.mark.parametrize(
        "username,password,expected_error",
        [
            ("", "some_password", "Field required"),
            ("valid_user", "", "Field required"),
            ("", "", "Field required"),
        ],
        ids=["empty_username", "empty_password", "both_empty"],
    )
    def test_empty_credentials_validation(self, api_client, username, password, expected_error):
        # Empty string handling in validation or auth
        resp = api_client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert resp.status_code in [401, 422]

    @pytest.mark.jira(ticket="SEC-108", severity="P1")
    @allure.title("TC-REST-08: Protected profile endpoint returns authenticated user details")
    def test_auth_me_authenticated(self, user_client):
        resp = user_client.get("/api/v1/auth/me")
        resp.assert_status(200)
        data = resp.json()
        assert data["username"] == "qa_tester"
        assert data["role"] == "user"

    @pytest.mark.jira(ticket="SEC-109", severity="P1")
    @allure.title("TC-REST-09: Protected profile without Authorization header returns 401")
    def test_auth_me_unauthorized_missing_header(self, api_client):
        api_client.clear_token()
        resp = api_client.get("/api/v1/auth/me")
        resp.assert_status(401)
        assert "Missing Authorization header" in resp.json()["detail"]

    @pytest.mark.jira(ticket="SEC-110", severity="P1")
    @allure.title("TC-REST-10: Malformed Authorization header returns 401")
    def test_auth_me_malformed_bearer_token(self, api_client):
        resp = api_client.get("/api/v1/auth/me", headers={"Authorization": "InvalidFormatToken123"})
        resp.assert_status(401)
        assert "Malformed Authorization header" in resp.json()["detail"]

    @pytest.mark.jira(ticket="SEC-111", severity="P1")
    @allure.title("TC-REST-11: Expired JWT token is rejected with 401")
    def test_expired_token_handling(self, api_client):
        # Generate an intentionally expired token (100 seconds in past)
        now = int(time.time())
        expired_payload = {
            "sub": "usr_standard",
            "username": "qa_tester",
            "role": "user",
            "iat": now - 3600,
            "exp": now - 100,
            "type": "access",
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        resp = api_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        resp.assert_status(401)
        assert "Token has expired" in resp.json()["detail"]

    @pytest.mark.jira(ticket="SEC-112", severity="P2")
    @allure.title("TC-REST-12: Refresh token issues new valid access token")
    def test_refresh_token_rotation(self, api_client):
        login_resp = api_client.post("/api/v1/auth/login", json={"username": "qa_tester", "password": "tester123!"})
        refresh_token = login_resp.json()["refresh_token"]

        refresh_resp = api_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        refresh_resp.assert_status(200)
        data = refresh_resp.json()
        assert "access_token" in data
        assert data["access_token"] != refresh_token

    @pytest.mark.jira(ticket="SEC-113", severity="P1")
    @allure.title("TC-REST-13: Logout invalidates the active bearer token")
    def test_logout_invalidates_token(self, api_client):
        login_resp = api_client.post("/api/v1/auth/login", json={"username": "qa_tester", "password": "tester123!"})
        access_token = login_resp.json()["access_token"]

        # Logout
        logout_resp = api_client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
        logout_resp.assert_status(200)

        # Subsequent call with same token must fail
        profile_resp = api_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        profile_resp.assert_status(401)
        assert "Token has been revoked" in profile_resp.json()["detail"]
