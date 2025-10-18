# stllrent-bootstrap

## 🌟 Project Overview

`stllrent-bootstrap` is a comprehensive Python module designed to **standardize and accelerate the development of responsive Flask APIs** that leverage Celery for asynchronous workload processing. This module is optimized for containerized production environments and is designed to work seamlessly with industry-standard technologies like **Kubernetes**, **RabbitMQ**, and **PostgreSQL**.

With this module, you can focus on your API's business logic, while `stllrent-bootstrap` handles the robust configuration and best practices for asynchronous processing.

---

## ✨ Why Use `stllrent-bootstrap`?

In a microservices architecture, managing asynchronous communication, result persistence, and workflow monitoring can be challenging. `stllrent-bootstrap` addresses these challenges by providing a solid, standardized foundation, ensuring:

* **Standardization and Reusability**: Offers a consistent structure for initializing Flask applications and Celery Workers, promoting code reuse and simplified maintenance across multiple projects.
* **Robust Asynchronous Processing**: Configures Celery with high-reliability patterns, including:
    * **`acks_late=True`**: Ensures messages are acknowledged in RabbitMQ only after successful processing, preventing message loss in case of Worker failures.
    * **DLQs (Dead-Letter Queues)**: Automatically routes messages from failed tasks to a Dead-Letter Queue in RabbitMQ, allowing for auditing, debugging, and reprocessing without data loss.
    * **Extended Result Persistence**: Saves detailed task results (success, failure, tracebacks) to PostgreSQL via `result_extended=True`.
* **Cloud and Container-Ready**: Pre-configured to work seamlessly with databases and message brokers as a service on any cloud provider, or in a self-hosted infrastructure. The design is optimized for deployment in **Kubernetes** clusters.
* **Clear Code Structure**: Separates responsibilities between the Flask API (task producer) and Celery Workers (task consumers), facilitating development and maintenance.
* **Application Factories**: Provides factory functions to create configured instances of Flask and Celery applications, simplifying initialization in your integration projects.

---

## 🚀 Key Features

* **Centralized Configuration**: Manages all environment configurations (broker URLs, backend URLs, DBs) via `pydantic-settings`.
* **Robust Connection Management**: Includes hooks to ensure proper database session closing in both Flask and Celery contexts.
* **Dynamic Model Discovery**: Automatically loads SQLAlchemy models defined in your project, simplifying database initialization.
* **Custom Base Task**: Provides a `BootstrapTask` class that enhances Celery tasks with improved logging, exception handling for DLQ, and automatic integration with workflow monitoring services.

---

## 🏁 Getting Started: Integrating `stllrent-bootstrap`

To integrate `stllrent-bootstrap` into your project, it is recommended to follow a standard structure and configuration pattern to fully leverage the module's automation features. The `stellrent-contract` project serves as an excellent implementation example of this pattern.

### 1. Installation

Add `stllrent-bootstrap` to your project's `requirements.txt` file.

```bash
# Example of installing from a private Git repository
pip install stllrent-bootstrap
```

### 2. Project Structure Requirements

For stllrent-bootstrap to work correctly, your project must follow a minimal structure. The bootstrap module expects to find the following files and directories:

```text
your_project/
├── src/
│   ├── app.py                  # Flask application entry point
│   ├── celery_app.py           # Celery App instantiation
│   ├── config/
│   │   ├── base_settings.py    # Application settings (inherits from BaseAppSettings)
│   │   └── celery_settings.py  # Celery settings (inherits from BaseCelerySettings)
│   ├── model/                  # Package for SQLAlchemy models
│   │   └── __init__.py
│   ├── route/
│   │   └── api.py              # Must contain the register_blueprints(app) function
│   └── worker/
│       └── ...                 # Modules containing your Celery tasks
└── .env
```

### 3. Configuration

#### Environment Variables (.env)

Your .env file must contain all the necessary environment variables. The bootstrap will load them to populate the configuration objects.

```text
# Application Settings (Flask)
DATABASE_HOST=localhost
DATABASE_USER=user
DATABASE_PASS=password
DATABASE_PORT=5432
DATABASE_NAME=mydatabase
API_PRIMARY_PATH=api/v1
APP_NAME=my-service
APP_LOG_LEVEL=DEBUG
FLASK_ENV=development

# Celery Settings
CELERY_BROKER_URL="amqp://user:password@rabbitmq-host:5672//"
RESULT_BACKEND_URL=localhost
RESULT_BACKEND_PORT=55432
RESULT_BACKEND_USER=user
RESULT_BACKEND_PASS=password
RESULT_BACKEND_DATABASE=celery_results
```

#### Configuration Classes

In your project, create classes that inherit from the base settings classes provided by stllrent-bootstrap to extend and customize the behavior.

Example - `src/config/base_settings.py`:

```python
from stllrent_bootstrap.flask.app_settings import BaseAppSettings

class Settings(BaseAppSettings):
    # Override or add service-specific settings
    APP_NAME: str = "my-contract-service"
    MODEL_DISCOVERY_PATHS: list[str] = ["model"] # Tells bootstrap where to find your models
```

Example - `src/config/celery_settings.py`:

```python
from stllrent_bootstrap.celery.config.settings import BaseCelerySettings
from stllrent_bootstrap.celery.model.brokers import RabbitMQModel
from .base_settings import settings # Import your app settings

# Define the broker models for your queues
example_broker = RabbitMQModel(queue="my-service.my-queue.example")

```python
class CelerySettings(BaseCelerySettings):
    APP_NAME: str = settings.APP_NAME
    celery_task_default_queue: str = example_broker.queue
    broker_models: list[RabbitMQModel] = [example_broker]
```

### 4. Application Initialization

Use the factory functions from the bootstrap to instantiate your Flask and Celery applications.

`src/app.py`:

```python
from config.base_settings import Settings
from stllrent_bootstrap.flask.app_factory import create_app

settings = Settings()
app = create_app(settings)

# Optional: for local execution
if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=settings.APP_PORT)
```

`src/celery_app.py`:
```python
from config.celery_settings import celery_settings
from stllrent_bootstrap.celery.app import create_celery_app

# List of modules where your tasks are defined for autodiscovery
PROJECT_TASK_PATHS = [
    'worker.my_worker_1',
    'worker.my_worker_2',
]

celery_app = create_celery_app(
    celery_settings=celery_settings,
    autodiscover_paths=PROJECT_TASK_PATHS
)
```

### 5. Route Definitions

The bootstrap's app_factory expects to find a route.api module with a register_blueprints function to load your application's routes.

`src/route/api.py`:

```python
def register_blueprints(app):
    from route.endpoint.public import public_blueprint
    app.register_blueprint(public_blueprint)

    # Register other blueprints here
```

By following these steps, your project will be correctly integrated with stllrent-bootstrap, allowing you to leverage all its features for standardization and development acceleration in any containerized environment.