"""
Reusable GraphQL Client for automated testing of GraphQL Queries and Mutations.
"""
import requests
from typing import Any, Dict, Optional


class GraphQLResponse:
    def __init__(self, raw: requests.Response):
        self.raw = raw
        self.status_code = raw.status_code
        try:
            self._data_json = raw.json()
        except Exception:
            self._data_json = {"errors": [{"message": raw.text}]}

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        return self._data_json.get("data")

    @property
    def errors(self) -> Optional[list]:
        return self._data_json.get("errors")

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def assert_no_errors(self):
        assert not self.has_errors, f"GraphQL query failed with errors: {self.errors}"


class GraphQLClient:
    def __init__(self, endpoint_url: str = "http://127.0.0.1:8000/graphql"):
        self.endpoint = endpoint_url
        self.session = requests.Session()

    def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
    ) -> GraphQLResponse:
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        if token:
            req_headers["Authorization"] = f"Bearer {token}"

        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        resp = self.session.post(self.endpoint, json=payload, headers=req_headers)
        return GraphQLResponse(resp)
