"""
Pytest configuration and session-wide fixtures for REST & GraphQL Test Framework.
Spins up the FastAPI + Strawberry GraphQL target service and provisions auth clients.
"""
import time
import threading
import requests
import pytest
import uvicorn
from server.app import app
from server.db import db
from clients.rest_client import RestClient
from clients.graphql_client import GraphQLClient

pytest_plugins = ["plugins.jira_defect_plugin"]

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


class UvicornTestServer(threading.Thread):
    def __init__(self, host: str, port: int):
        super().__init__(daemon=True)
        config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


@pytest.fixture(scope="session", autouse=True)
def start_test_server():
    # Check if server is already running
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=1)
        if r.status_code == 200:
            yield
            return
    except Exception:
        pass

    server_thread = UvicornTestServer(SERVER_HOST, SERVER_PORT)
    server_thread.start()

    # Wait for server to be responsive
    for _ in range(50):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=0.5)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError(f"FastAPI + GraphQL server failed to start on {BASE_URL}")

    yield

    server_thread.stop()


@pytest.fixture(autouse=True)
def reset_db_before_test():
    db.reset()
    yield


@pytest.fixture(scope="session")
def api_client() -> RestClient:
    return RestClient(base_url=BASE_URL)


@pytest.fixture(scope="session")
def graphql_client() -> GraphQLClient:
    return GraphQLClient(endpoint_url=f"{BASE_URL}/graphql")


@pytest.fixture(scope="session")
def admin_token(api_client) -> str:
    resp = api_client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def user_token(api_client) -> str:
    resp = api_client.post("/api/v1/auth/login", json={"username": "qa_tester", "password": "tester123!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def admin_client(api_client, admin_token) -> RestClient:
    client = RestClient(base_url=BASE_URL)
    client.set_token(admin_token)
    return client


@pytest.fixture
def user_client(api_client, user_token) -> RestClient:
    client = RestClient(base_url=BASE_URL)
    client.set_token(user_token)
    return client
