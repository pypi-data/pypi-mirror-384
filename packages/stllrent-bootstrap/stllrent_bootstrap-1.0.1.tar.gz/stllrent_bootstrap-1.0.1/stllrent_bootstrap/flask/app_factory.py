from flask import Flask, request
from celery import Celery
from stllrent_bootstrap.flask.app_logger import configure_logging
from stllrent_bootstrap.flask.app_settings import BaseAppSettings
from stllrent_bootstrap.exc import ProjectStandardException
from stllrent_bootstrap.database.discovery import load_project_models
from stllrent_bootstrap.database.manager import DatabaseManager
from stllrent_bootstrap.celery.base_task import BootstrapTask
import logging

def setup_blueprints(app:Flask):
    try:
        from route.api import register_blueprints # Importação específica do projeto
    except ModuleNotFoundError as mdf:
        raise ProjectStandardException(requirements="route/api.py with method register_blueprints is required")
    register_blueprints(app)


def create_app(settings: BaseAppSettings) -> Flask:
    configure_logging(settings)
    log = logging.getLogger(__name__)
    log.debug("Configuring Flask aplication")
    app = Flask(settings.APP_NAME)
    
    app.config.from_object(settings)

    load_project_models(settings.MODEL_DISCOVERY_PATHS)
    db_manager = DatabaseManager(settings)
    app.extensions["db_manager"] = db_manager
    db_manager.setup_database(app)
    
    setup_blueprints(app) 
    
    app.after_request(after_request_func)
    return app

def configure_celery_for_flask(celery: Celery, app: Flask):
    """Configura a task do Celery para rodar dentro do contexto do app Flask."""
    log = logging.getLogger(__name__)
    class FlaskTask(BootstrapTask):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return super().__call__(*args, **kwargs)
    
    celery.Task = FlaskTask

    try:
        # Acessa a URL do broker que o Celery *realmente* está usando para a conexão
        # current_broker é um objeto Kombu Connection, e tem um atributo transport.default_connection.hostname
        # ou url.
        broker_connection_url = celery.connection().as_uri()
        log.debug(f"DEBUG_CELERY_CONNECTION: Celery app connected to broker: {broker_connection_url}")
    except Exception as e:
        log.error(f"DEBUG_CELERY_CONNECTION: Erro ao obter URL de conexão do broker: {e}")

    celery.set_default()

def after_request_func(response):
    log = logging.getLogger(__name__)
    log.info(
        f"{request.method} {request.full_path} -> {response.status} ",
        extra={
            "remote_addr": request.remote_addr,
            "method": request.method,
            "scheme": request.scheme,
            "path": request.full_path,
            "status": response.status,
            "log_type": "request_log" # Adiciona um identificador para este tipo de log
        }
    )
    return response