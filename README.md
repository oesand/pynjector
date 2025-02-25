# Pynjector

A lightweight Dependency Injection (DI) container for Python that allows automatic resolution of dependencies based on constructor type hints.

## 🚀 Features
- Simple and intuitive API
- Automatic dependency resolution based on type hints
- Supports binding classes, factory functions, and pre-initialized instances
- Inspired by C#'s dependency injection approach

## 📦 Installation

Install via pip:

```sh
pip install pynjector
```

## 🎯 Usage

```python
from pynjector import DIContainer

class Database:
    def query(self) -> str:
        return "Data from Database"

class Service:
    def __init__(self, db: Database):
        self.db = db

    def get_data(self) -> str:
        return self.db.query()

# Create the container
container = DIContainer()

# Register dependencies
container.bind(Database)

# Resolve a service instance
service = container.resolve(Service)

print(service.get_data())  # Output: "Data from Database"
```
