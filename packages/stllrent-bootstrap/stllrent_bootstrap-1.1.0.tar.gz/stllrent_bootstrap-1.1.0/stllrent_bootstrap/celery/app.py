from celery import Celery
from typing import List, Optional
import logging.config
import sys
import logging

from stllrent_bootstrap.celery.bootsteps import SetupQueuesBootstep
from .app_logger import get_logging_config

# IMPORTAÇÃO CORRETA DOS SINAIS
from celery.signals import setup_logging, worker_init, worker_process_init

_celery_settings = None
_log = logging.getLogger(__name__)

@setup_logging.connect(weak=False)
def on_setup_logging(**kwargs):
    """
    Desabilita a configuração de log padrão do Celery.
    """
    pass

def _configure_logging(**kwargs):
    """Função auxiliar para aplicar a configuração de log."""
    if _celery_settings:
        log_config = get_logging_config(_celery_settings)
        logging.config.dictConfig(log_config)
    else:
        _log.warning("AVISO: _celery_settings não foi definido. O logger do worker não será configurado.", file=sys.stderr)

# CONECTA A CONFIGURAÇÃO AOS DOIS SINAIS: O DO PROCESSO PRINCIPAL E O DOS FILHOS
@worker_init.connect(weak=False)
def on_worker_init(**kwargs):
    """
    Aplica a configuração de log quando o processo principal do worker inicia.
    """
    _configure_logging()

@worker_process_init.connect(weak=False)
def on_worker_process_init(**kwargs):
    """
    Aplica a configuração de log customizada quando cada processo de worker inicia.
    """
    _configure_logging()


def create_celery_app(
    celery_settings: object,
    autodiscover_paths: Optional[List[str]] = None
) -> Celery:
    """
    Função Fábrica para criar e configurar uma instância do Celery App.

    Args:
        settings: O objeto de configuração já carregado (ex: celery_settings).
        autodiscover_paths: Lista de caminhos de importação onde as tarefas estão definidas.

    Returns:
        Uma instância configurada do aplicativo Celery.
    """
    global _celery_settings
    _celery_settings = celery_settings

    celery_app = Celery(celery_settings.APP_NAME)
    celery_app.conf.update(celery_settings.celery_config_dict)
    celery_app.steps['worker'].add(SetupQueuesBootstep)

    # REMOÇÃO DA LÓGICA REDUNDANTE DE DECLARAÇÃO DE FILAS.
    # O SetupQueuesBootstep já cuida disso no momento apropriado,
    # garantindo que os logs sejam emitidos corretamente.

    if autodiscover_paths:
        celery_app.autodiscover_tasks(autodiscover_paths)

    _log.debug("Instância unica Celery App configurada e gerada com sucesso.")
    _log.debug(celery_app.conf.humanize(with_defaults=False, censored=True))
    return celery_app