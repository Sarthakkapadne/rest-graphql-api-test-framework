"""
Reusable REST API Client for automated testing.
Provides automatic JWT token management, response timing, and request logging.
"""
import time
import requests
from typing import Any, Dict, Optional


class ApiResponse:
    def __init__(self, raw_response: requests.Response, elapsed_ms: float):
        self.raw = raw_response
        self.status_code = raw_response.status_code
        self.headers = raw_response.headers
        self.elapsed_ms = elapsed_ms
        self._json_cache = None

    def json(self) -> Any:
        if self._json_cache is None:
            self._json_cache = self.raw.json()
        return self._json_cache

    @property
    def text(self) -> str:
        return self.raw.text

    def assert_status(self, expected_code: int):
        assert self.status_code == expected_code, (
            f"Expected status code {expected_code}, got {self.status_code}. Response: {self.text}"
        )


class RestClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token: Optional[str] = None

    def set_token(self, token: str):
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self):
        self.token = None
        self.session.headers.pop("Authorization", None)

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> ApiResponse:
        url = self._build_url(endpoint)
        start = time.perf_counter()
        resp = self.session.get(url, params=params, headers=headers)
        elapsed = (time.perf_counter() - start) * 1000
        return ApiResponse(resp, elapsed)

    def post(
        self,
        endpoint: str,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict] = None,
    ) -> ApiResponse:
        url = self._build_url(endpoint)
        start = time.perf_counter()
        resp = self.session.post(url, json=json, data=data, headers=headers)
        elapsed = (time.perf_counter() - start) * 1000
        return ApiResponse(resp, elapsed)

    def put(self, endpoint: str, json: Optional[Any] = None, headers: Optional[Dict] = None) -> ApiResponse:
        url = self._build_url(endpoint)
        start = time.perf_counter()
        resp = self.session.put(url, json=json, headers=headers)
        elapsed = (time.perf_counter() - start) * 1000
        return ApiResponse(resp, elapsed)

    def patch(self, endpoint: str, json: Optional[Any] = None, headers: Optional[Dict] = None) -> ApiResponse:
        url = self._build_url(endpoint)
        start = time.perf_counter()
        resp = self.session.patch(url, json=json, headers=headers)
        elapsed = (time.perf_counter() - start) * 1000
        return ApiResponse(resp, elapsed)

    def delete(self, endpoint: str, headers: Optional[Dict] = None) -> ApiResponse:
        url = self._build_url(endpoint)
        start = time.perf_counter()
        resp = self.session.delete(url, headers=headers)
        elapsed = (time.perf_counter() - start) * 1000
        return ApiResponse(resp, elapsed)
