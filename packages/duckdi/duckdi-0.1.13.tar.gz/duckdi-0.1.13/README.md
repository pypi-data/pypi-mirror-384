<p align="center">
  <img src="assets/logo.png" alt="DuckDI Logo" width="150" />
</p>

# 🦆 DuckDI

**DuckDI** is a minimal, type-safe, and architecture-friendly dependency injection library for Python.

It provides a clean interface to register and resolve dependencies at runtime using a TOML-based configuration, following the duck typing principle: _"if it implements the expected methods, it’s good enough."_  
Ideal for developers who want clarity, zero magic, and full control over dependency resolution.

---

## 🚀 Features

- ✅ Clean and lightweight API  
- ✅ Zero runtime dependencies  
- ✅ Fully type-safe (no introspection magic)  
- ✅ Supports singleton and transient resolution  
- ✅ Uses TOML to bind interfaces to adapters  
- ✅ Works with `ABC` and regular classes (no need for Protocols)  
- ✅ Clear and informative error messages  
- ✅ Environment-based configuration (`INJECTIONS_PATH`)  

---

## 📦 Installation

With [Poetry](https://python-poetry.org):

```bash
poetry add duckdi
```

Or using pip:

```bash
pip install duckdi
```

---

## 🛠️ Usage

### 1. Define an interface

```python
from duckdi import Interface
from abc import ABC, abstractmethod

@Interface
class IUserRepository(ABC):
    @abstractmethod
    def get_user(self, user_id: str) -> dict: ...
```

---

### 2. Register an adapter

```python
from duckdi import register

class PostgresUserRepository(IUserRepository):
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id, "name": "John Doe"}

register(PostgresUserRepository)
```

You can also register it as a singleton:

```python
register(PostgresUserRepository, is_singleton=True)
```

---

### 3. Create your injection payload

Create a file called `injections.toml`:

```toml
[injections]
"i_user_repository" = "postgres_user_repository"
```

---

### 4. Set the environment variable

Set the injection file path using the `INJECTIONS_PATH` environment variable:

```bash
export INJECTIONS_PATH=./injections.toml
```

---

### 5. Resolve your dependencies

```python
from duckdi import Get

repo = Get(IUserRepository)
user = repo.get_user("123")
print(user)  # {'id': '123', 'name': 'John Doe'}
```

---

## 💥 Error Handling

### `MissingInjectionPayloadError`
Raised when no injection payload file is found at the specified path.

### `InvalidAdapterImplementationError`
Raised when the adapter registered does not implement the expected interface.

### `InterfaceAlreadyRegisteredError`
Raised when trying to register the same interface twice.

### `AdapterAlreadyRegisteredError`
Raised when the same adapter is registered more than once.

---

## 📁 Project Structure

```
duckdi/
├── pyproject.toml
├── README.md
├── src/
│   └── duckdi/
│       ├── __init__.py
│       ├── cli.py
│       ├── duck.py
│       ├── errors/
│       │   ├── __init__.py
│       │   ├── invalid_adapter_implementation_error.py
│       │   ├── interface_already_registered_error.py
│       │   ├── adapter_already_registered_error.py
│       │   └── missing_injection_payload_error.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── buffer_readers.py
│       │   └── to_snake.py
│       └── injections/
│           ├── injections_container.py
│           └── injections_payload.py
└── tests/
    ├── test_interface.py
    ├── test_register.py
    └── test_get.py
```

---

## 🧩 Advanced Example

You can register multiple adapters and resolve them dynamically based on the TOML mapping:

```python
from duckdi import Interface, register, Get

@Interface
class INotifier:
    def send(self, msg: str): ...

class EmailNotifier(INotifier):
    def send(self, msg: str):
        print(f"Sending email: {msg}")

register(EmailNotifier)

# injections.toml
# [injections]
# "i_notifier" = "email_notifier"

notifier = Get(INotifier)
notifier.send("Hello from DuckDI!")
```

---

## 🧪 Testing

To run tests:

```bash
pytest
```

Or via Makefile:

```bash
make test
```

To check static typing:

```bash
make check
```

---

## 📄 License

Licensed under the MIT License.  
See the [LICENSE](LICENSE) file for more information.

---

## 👤 Author

Made with ❤️ by **PhePato**  
Pull requests, issues and ideas are always welcome!
