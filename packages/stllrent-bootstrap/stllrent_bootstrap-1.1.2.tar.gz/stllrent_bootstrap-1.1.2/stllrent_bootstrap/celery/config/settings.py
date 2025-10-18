import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from typing import Any, List, Tuple, Optional
from kombu import Queue

from stllrent_bootstrap.celery.model.brokers import RabbitMQModel
from stllrent_bootstrap.celery.model.task_queues_factory import create_queues_from_models

class BaseCelerySettings(BaseSettings):
    """
    Configurações base para um worker Celery.
    Aplicações devem herdar desta classe e, no mínimo, definir o campo 'broker_models'.
    """
    # --- Configurações Obrigatórias para a utilização deste módulo ---
    APP_NAME: str = Field("default_celery_app")
    APP_LOG_FORMATTER: Optional[str] = Field(default="json")
    APP_LOG_LEVEL: Optional[str] = Field(default="DEBUG")
    celery_task_default_queue: str = Field(...)

    TASK_DEFAULT_RETRY_DELAY: Optional[int] = Field(default=160)
    TASK_BUSINESS_EXC_RETRY_DELAY: Optional[int] = Field(default=86400)

    RESULT_BACKEND_URL: str = Field(alias="RESULT_BACKEND_URL")
    RESULT_BACKEND_PORT: int = Field(alias="RESULT_BACKEND_PORT")
    RESULT_BACKEND_USER: str = Field(alias="RESULT_BACKEND_USER")
    RESULT_BACKEND_PASS: str = Field(alias="RESULT_BACKEND_PASS")
    RESULT_BACKEND_DATABASE: str = Field(alias="RESULT_BACKEND_DATABASE")

    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")

    celery_result_backend: Optional[str] = Field(
        default=None,
        alias="RESULT_BACKEND_URI"
    )

    # --- Configurações Opcionais para a utilização deste módulo ---
    # --- Modelos de Broker para Geração de Filas e Rotas ---
    # Este campo DEVE ser sobrescrito pela classe filha com a lista de modelos de broker.
    broker_models: List[RabbitMQModel] = Field(default_factory=list, exclude=True)

    # --- Campos Computados para Configuração do Celery ---
    celery_task_queues: Tuple[Queue, ...] = Field(default=(), exclude=True)

    # --- Configurações Padrão de Comportamento do Celery ---
    celery_task_acks_late: bool = Field(default=True)
    celery_result_persistent: bool = Field(default=True)
    celery_result_extended: bool = Field(default=True)
    celery_result_expires: int = Field(default=0)
    celery_worker_prefetch_multiplier: int = Field(default=1)
    celery_task_track_started: bool = Field(default=True)
    celery_broker_connection_retry_on_startup: bool = Field(default=True)
    celery_task_create_missing_queues: bool = Field(default=False)
    celery_broker_heartbeat: int = Field(default=60)
    celery_broker_transport_options: dict[str, Any] = Field(default={'confirm_publish': True,'keepalive': True})

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True,
    )

    @model_validator(mode='after')
    def _generate_computed_fields(self) -> 'BaseCelerySettings':
        """
        Gera campos computados como a URI do backend e as filas de tarefas.
        """
        # Constrói a URI do backend de resultados se não for fornecida diretamente
        if self.celery_result_backend is None and self.RESULT_BACKEND_URL:
            self.celery_result_backend = (
                f"db+postgresql://{self.RESULT_BACKEND_USER}:"
                f"{self.RESULT_BACKEND_PASS}@{self.RESULT_BACKEND_URL}:"
                f"{self.RESULT_BACKEND_PORT}/{self.RESULT_BACKEND_DATABASE}"
            )
        # Gera as filas do Kombu a partir dos modelos de broker fornecidos
        if self.broker_models:
            self.celery_task_queues = create_queues_from_models(self.broker_models)

        return self

    @property
    def task_routes(self) -> dict[str, dict[str, str]]:
        """Define as rotas de tarefas do Celery dinamicamente a partir dos modelos de broker."""
        if not self.broker_models:
            return {}
        return {
            broker.queue: {'queue': broker.queue} for broker in self.broker_models
        }

    @property
    def celery_config_dict(self) -> dict[str, Any]:
        """
        Gera um dicionário de configurações Celery adequado para app.conf.update().
        """
        config = self.model_dump(by_alias=True, exclude_none=True)
        celery_conf = {}

        for key, value in config.items():
            if key.lower().startswith("celery_"):
                # Converte para o novo formato de configuração do Celery 5+ (lowercase).
                # Ex: 'celery_task_acks_late' -> 'task_acks_late'
                celery_key = key.replace("celery_", "")
                celery_conf[celery_key] = value

        celery_conf['task_routes'] = self.task_routes
        celery_conf['task_queues'] = self.celery_task_queues

        return celery_conf