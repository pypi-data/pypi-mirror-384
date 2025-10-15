import httpx
import pytest

from pyrest_model_client.client import RequestClient, build_header


def test_build_header():
    token = "abc123"
    header = build_header(token)
    assert header["Authorization"] == f"Token {token}"
    assert header["Content-Type"] == "application/json"


def test_set_credentials(monkeypatch: pytest.MonkeyPatch) -> None:  # pylint: disable=W0613
    client = RequestClient(header={"Authorization": "Token test"})
    new_header = {"Authorization": "Token new", "X-Test": "1"}
    client.set_credentials(new_header)
    for k, v in new_header.items():
        assert client.client.headers[k] == v


def test_request_format(monkeypatch: pytest.MonkeyPatch) -> None:
    client = RequestClient(header={"Authorization": "Token test"}, base_url="http://api")
    called = {}

    def fake_request(method, endpoint, **kwargs):
        called["method"] = method
        called["endpoint"] = endpoint
        called["kwargs"] = kwargs

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"id": 1}

        return Resp()

    monkeypatch.setattr(client.client, "request", fake_request)
    _ = client.request("GET", "test")
    assert called["endpoint"].startswith("/test/")
    assert called["method"] == "GET"


def test_get_post_put_delete(monkeypatch):
    client = RequestClient(header={"Authorization": "Token test"}, base_url="http://api")

    def fake_request(method, endpoint, **kwargs):
        return (method, endpoint, kwargs)

    monkeypatch.setattr(client, "request", fake_request)
    for method_name, expected_method in (
        ("get", "GET"),
        ("post", "POST"),
        ("put", "PUT"),
        ("delete", "DELETE"),
    ):
        func = getattr(client, method_name)
        if method_name == "get":
            result = func("foo")
        elif method_name == "delete":
            result = func("foo")
        else:
            result = func("foo", {"a": 1})
        method, endpoint, _ = result
        assert (method, endpoint) == (expected_method, "foo")


def test_request_raises(monkeypatch):
    client = RequestClient(header={"Authorization": "Token test"}, base_url="http://api")

    class FakeResp:
        def raise_for_status(self):
            req = httpx.Request("GET", "http://api/fail")
            resp = httpx.Response(500, request=req)
            raise httpx.HTTPStatusError("fail", request=req, response=resp)

    monkeypatch.setattr(client.client, "request", lambda *a, **k: FakeResp())
    with pytest.raises(httpx.HTTPStatusError):
        client.request("GET", "fail")
