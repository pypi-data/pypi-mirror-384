# Apeex Framework

A modular, interface-driven Python web framework inspired by **Symfony**, built on top of **FastAPI**.

---

## 🧩 Project Structure

```
apeex/         # Core framework (Kernel, Container, HTTP, ORM, CLI, Events)
adapters/      # Integrations and adapters for external libraries
bundles/       # Feature modules (bundles)
scripts/       # CLI and dev utilities
config/        # Configuration files and service definitions
tests/         # Unit and integration tests
```

---

## 🧰 Development

Install dependencies (assuming poetry is used):

```bash
poetry install
```

Run code quality checks:

```bash
poetry run black .
poetry run isort .
poetry run flake8 .
poetry run mypy .
poetry run pytest -v
```

All comments in code should be in **English**.

---

## ⚙️ DI Container

The framework provides a Dependency Injection container for managing services.

**Register services:**

```python
from apeex.container.container import Container

container = Container()
container.set('Logger', Logger())
container.set_factory('UserService', lambda c: UserService(c.get('Logger')))
```

**Autowire classes:**

```python
user_service = container.autowire(UserService)  # dependencies resolved automatically
```

**Singleton scope:**

```python
a1 = container.autowire(UserService)
a2 = container.autowire(UserService)
assert a1 is a2
```

**Build bundles:**

```python
from bundles.sample_bundle.bundle import SampleBundle
bundle = SampleBundle()
container.build_bundle(bundle)
```

---

## 🏗️ Kernel & Bundles (Planned)

* `Kernel` will manage application lifecycle, bundles, container, and routing.
* `Bundle` is an abstract class that allows registration of services and lifecycle hooks (`build`, `boot`, `shutdown`).
* Bundles can define controllers and services with full container integration.
* Example bundles: `DemoBundle`, `SampleBundle`.

---

## 📄 Contributing

See `CONTRIBUTING.md` for guidelines on:

* Branching strategy
* Commit messages (use Conventional Commits)
* Code formatting and linting
* Testing

---

## 🚦 CI/CD

The project includes a GitHub Actions pipeline to automatically:

* Install dependencies
* Run black, isort, flake8, mypy checks
* Run pytest

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: |
          pip install poetry
          poetry install
      - run: |
          poetry run black --check .
          poetry run isort --check-only .
          poetry run flake8 .
          poetry run mypy .
      - run: poetry run pytest -v
```

---

## 📖 Examples

**Defining a simple service and controller:**

```python
class HelloService:
    def greet(self, name: str) -> str:
        return f'Hello, {name}!'

class HelloController:
    def __init__(self, service: HelloService):
        self.service = service

    def hello(self, name: str) -> str:
        return self.service.greet(name)

container.set_factory('HelloService', lambda c: HelloService())
container.set_factory('HelloController', lambda c: HelloController(c.get('HelloService')))

controller = container.get('HelloController')
print(controller.hello('World'))
```

**Autowiring example:**

```python
controller2 = container.autowire(HelloController)
assert controller2 is container.get('HelloController')  # singleton behavior
```
