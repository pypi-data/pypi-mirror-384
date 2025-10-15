import pytest

from pyrest_model_client.base import BaseAPIModel, set_client
from pyrest_model_client.client import RequestClient


class DummyModel(BaseAPIModel):
    name: str
    _resource_path: str = "dummy"


def setup_module(module) -> None:  # pylint: disable=W0613
    # Set a dummy client for all tests
    set_client(RequestClient(header={"Authorization": "Token test"}, base_url="http://api"))


def test_save_create(monkeypatch):
    model = DummyModel(name="foo")

    def fake_post(endpoint, data) -> None:  # pylint: disable=W0613
        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"id": 42}

        return Resp()

    set_client(RequestClient(header={"Authorization": "Token test"}, base_url="http://api"))
    monkeypatch.setattr("pyrest_model_client.base.client.post", fake_post)
    model.save()
    assert model.id == 42


def test_save_update(monkeypatch):
    model = DummyModel(name="foo", id=99)

    def fake_put(endpoint, data) -> None:  # pylint: disable=W0613
        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"id": 99}

        return Resp()

    set_client(RequestClient(header={"Authorization": "Token test"}, base_url="http://api"))
    monkeypatch.setattr("pyrest_model_client.base.client.put", fake_put)
    model.save()
    assert model.id == 99


def test_delete(monkeypatch):
    model = DummyModel(name="foo", id=1)

    def fake_delete(endpoint) -> None:  # pylint: disable=W0613
        class Resp:
            def raise_for_status(self):
                pass

        return Resp()

    set_client(RequestClient(header={"Authorization": "Token test"}, base_url="http://api"))
    monkeypatch.setattr("pyrest_model_client.base.client.delete", fake_delete)
    model.delete()


def test_delete_unsaved():
    model = DummyModel(name="foo")
    with pytest.raises(ValueError):
        model.delete()


def test_load(monkeypatch):
    def fake_get(endpoint) -> None:  # pylint: disable=W0613
        class Resp:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {"id": 5, "name": "bar"}

        return Resp()

    set_client(RequestClient(header={"Authorization": "Token test"}, base_url="http://api"))
    monkeypatch.setattr("pyrest_model_client.base.client.get", fake_get)
    obj = DummyModel.load("5")
    assert obj.id == 5
    assert obj.name == "bar"


def test_load_not_found(monkeypatch):
    def fake_get(endpoint) -> None:  # pylint: disable=W0613
        class Resp:
            status_code = 404

            def raise_for_status(self):
                pass

            def json(self):
                return {}

        return Resp()

    set_client(RequestClient(header={"Authorization": "Token test"}, base_url="http://api"))
    monkeypatch.setattr("pyrest_model_client.base.client.get", fake_get)
    with pytest.raises(ValueError):
        DummyModel.load("123")


def test_find(monkeypatch):
    def fake_get(endpoint) -> None:  # pylint: disable=W0613
        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]

        return Resp()

    set_client(RequestClient(header={"Authorization": "Token test"}, base_url="http://api"))
    monkeypatch.setattr("pyrest_model_client.base.client.get", fake_get)
    objs = DummyModel.find()
    assert len(objs) == 2
    assert objs[0].name == "a"
    assert objs[1].id == 2
