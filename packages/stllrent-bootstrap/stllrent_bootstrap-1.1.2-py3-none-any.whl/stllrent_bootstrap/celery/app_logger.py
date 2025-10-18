import logging
import sys
import os
from celery import current_task
from stllrent_bootstrap.celery.config.settings import BaseCelerySettings

# FILTRO CUSTOMIZADO PARA INJETAR O CONTEXTO DA TASK CELERY
class CeleryTaskContextFilter(logging.Filter):
    """
    Este filtro injeta o ID e o nome da tarefa Celery nos registros de log.
    """
    def filter(self, record):
        if current_task and hasattr(current_task, 'request'):
            record.task_id = current_task.request.id
            record.task_name = current_task.name
        else:
            record.task_id = None
            record.task_name = None
        return True

# Filtro para separar os logs por nível
class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO, logging.WARNING)

def get_logging_config(settings_instance: BaseCelerySettings):
    """
    Retorna um dicionário de configuração de logging para ser usado com
    logging.config.dictConfig.
    """
    log_level = settings_instance.APP_LOG_LEVEL.upper()
    formatter = settings_instance.APP_LOG_FORMATTER

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(name)s %(levelname)s %(message)s %(task_id)s %(task_name)s'
            },
            'console': {
                'format': '[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(task_name)s:%(task_id)s] %(message)s',
            },
        },
        'filters': {
            'info_filter': {
                '()': InfoFilter,
            },
            'celery_context_filter': {
                '()': CeleryTaskContextFilter,
            }
        },
        'handlers': {
            'console_stdout': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': formatter,
                'stream': sys.stdout,
                'filters': ['info_filter', 'celery_context_filter'],
            },
            'console_stderr': {
                'class': 'logging.StreamHandler',
                'level': 'ERROR',
                'formatter': formatter,
                'stream': sys.stderr,
                'filters': ['celery_context_filter'],
            },
        },
        'loggers': {
            # --- NOVA SEÇÃO ---
            # Configuração explícita para o logger 'celery' e seus filhos.
            'celery': {
                'level': log_level,
                'handlers': ['console_stdout', 'console_stderr'],
                'propagate': False, # Impede que os logs sejam passados para o logger root, evitando duplicação.
            },
            'urllib3': {
                'level': log_level,
                'handlers': ['console_stdout', 'console_stderr'],
                'propagate': False, 
            },
            'requests': {
                'level': log_level,
                'handlers': ['console_stdout', 'console_stderr'],
                'propagate': False,
            },
        },
        'root': {
            'level': log_level,
            'handlers': ['console_stdout', 'console_stderr'],
        },
    }

