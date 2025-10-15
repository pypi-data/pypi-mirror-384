from typing import Any

import httpx


def build_header(
    token: str,
    authorization_type: str = "Token",
    content_type: str = "application/json",
) -> dict:
    return {
        "Content-Type": content_type,
        "Authorization": f"{authorization_type} {token}",
    }


class RequestClient:
    client: httpx.Client

    def __init__(self, header: dict, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url
        self.client = httpx.Client(base_url=self.base_url)
        self.set_credentials(header=header)

    def set_credentials(self, header: dict) -> None:
        self.client.headers.update(header)

    def request(self, method: str, endpoint: str, **kwargs: Any) -> httpx.Response:
        if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
            if not endpoint.startswith("/"):  # Ensure endpoint starts with a slash if it's a path (not a full URL)
                endpoint = "/" + endpoint

        if not endpoint.endswith("/"):  # Ensure endpoint ends with a slash
            endpoint = endpoint + "/"

        response = self.client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response

    def get(self, endpoint: str, params: dict | None = None) -> httpx.Response:
        if params is None:
            params = {}
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: dict | None = None) -> httpx.Response:
        if data is None:
            data = {}
        return self.request("POST", endpoint, json=data)

    def put(self, endpoint: str, data: dict | None = None) -> httpx.Response:
        if data is None:
            data = {}
        return self.request("PUT", endpoint, json=data)

    def delete(self, endpoint: str) -> httpx.Response:
        return self.request("DELETE", endpoint)
