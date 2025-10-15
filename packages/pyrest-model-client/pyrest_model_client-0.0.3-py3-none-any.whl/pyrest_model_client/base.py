from typing import ClassVar

from pydantic import BaseModel

from pyrest_model_client.client import RequestClient

client: RequestClient | None = None  # Module-level global client


def set_client(new_client: RequestClient) -> None:
    """Set the global client instance for all API models."""
    global client  # pylint: disable=W0603
    client = new_client


class BaseAPIModel(BaseModel):
    id: int | str | None = None
    _resource_path: ClassVar[str] = ""

    def save(self) -> None:
        data = self.model_dump(exclude_unset=True)
        response = (
            client.put(f"/{self._resource_path}/{self.id}", data=data)
            if self.id
            else client.post(f"/{self._resource_path}", data=data)
        )

        response.raise_for_status()
        self.id = response.json()["id"]

    def delete(self) -> None:
        if not self.id:
            raise ValueError("Cannot delete unsaved resource.")
        response = client.delete(f"/{self._resource_path}/{self.id}")
        response.raise_for_status()

    @classmethod
    def load(cls, resource_id: str) -> "BaseAPIModel":
        response = client.get(f"/{cls._resource_path}/{resource_id}")
        if response.status_code == 404:
            raise ValueError(f"{cls.__name__} not found.")
        response.raise_for_status()
        return cls(**response.json())

    @classmethod
    def find(cls) -> list["BaseAPIModel"]:
        response = client.get(f"/{cls._resource_path}")
        response.raise_for_status()
        return [cls(**item) for item in response.json()]
