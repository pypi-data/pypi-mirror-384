# python-requests-client

A simple, flexible Python HTTP client and API modeling toolkit built on top of [httpx](https://www.python-httpx.org/) and [pydantic](https://docs.pydantic.dev/). Easily integrate robust API requests and resource models into your Python projects.

---

## 🚀 Features
- **Model-driven**: Define and interact with API resources as Python classes.
- **Easy HTTP Requests**: Simple `RequestClient` for GET, POST, PUT, DELETE with automatic header and base URL management.
- **Pydantic API Models**: Define resource models with CRUD helpers (`save`, `delete`, `load`, `find`).
- **Global Client Setup**: Set a global API client for all models with `set_client()`.
- **Type Safety**: All models use Pydantic for validation and serialization.
- **Extensible**: Easily create new models for any RESTful resource.

---

## 📦 Installation
```bash
pip install python-requests-client
```

---

## 🔧 Usage

### 1. Define Your Models

```python
from pyrest_model_client.base import BaseAPIModel
from typing import ClassVar


class User(BaseAPIModel):
  name: str
  email: str
  _resource_path: ClassVar[str] = "user"


class Environment(BaseAPIModel):
  name: str
  _resource_path: ClassVar[str] = "environment"
```

### 2. Initialize the Client

```python
from pyrest_model_client import RequestClient, build_header, set_client
from example_usage.models.user import User
from example_usage.models.environment import Environment

set_client(
  new_client=RequestClient(
    base_url="http://localhost:8000",
    header=build_header(token="YOUR_API_TOKEN")
  )
)

# Create and save a new user
e = User(name="Alice", email="alice@example.com")
e.save()

# Update and save
e.name = "Alice Smith"
e.save()

# Find all environments
environments = Environment.find()
print(environments)

# Load a specific user by ID
user = User.load(resource_id="123")

# Delete a user
user.delete()
```

---

## 🤝 Contributing
Contributions are welcome! Please fork the repo, create a branch, and submit a pull request.

---

## 📄 License
MIT License — see [LICENSE](LICENSE) for details.
