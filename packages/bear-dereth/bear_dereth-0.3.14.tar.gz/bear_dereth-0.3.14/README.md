
# Bear Dereth

[![pypi version](https://img.shields.io/pypi/v/bear-dereth.svg)](https://pypi.org/project/bear-dereth/)

A set of common tools for various bear projects.

## Installation

```bash
uv pip install bear-dereth
```

## Dependency Injection

The project ships with a lightweight dependency injection container.  Services
can register cleanup callbacks that run when the container shuts down:

```python
from bear_dereth.di import DeclarativeContainer

class AppContainer(DeclarativeContainer):
    db: Database

db = Database()
AppContainer.register("db", db)
AppContainer.register_teardown(lambda: db.close())
AppContainer.shutdown()
```

Callbacks registered with :func:`register_teardown` run after any service
``shutdown()`` method has been invoked.
