import logging.config
import sys
import os
from pythonjsonlogger import jsonlogger

# Filtro para separar os logs por nível (DEBUG, INFO, WARNING)
class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO, logging.WARNING)

def get_logging_config(settings_instance):
    """
    Retorna um dicionário de configuração de logging para Flask.
    """
    log_level = settings_instance.APP_LOG_LEVEL.upper()
    formatter = settings_instance.APP_LOG_FORMATTER

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(name)s %(levelname)s %(funcName)s %(lineno)d %(message)s'
            },
            'console': {
                'format': '[%(asctime)s] [%(levelname)-8s] %(message)s',
            },
        },
        'filters': {
            'info_filter': {
                '()': InfoFilter,
            }
        },
        'handlers': {
            'console_stdout': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': formatter,
                'stream': sys.stdout,
                'filters': ['info_filter'],
            },
            'console_stderr': {
                'class': 'logging.StreamHandler',
                'level': 'ERROR',
                'formatter': formatter,
                'stream': sys.stderr,
            },
        },
        'loggers': {
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

def configure_logging(settings_instance):
    """
    Aplica a configuração de logging para a aplicação Flask.
    """
    log_config = get_logging_config(settings_instance)
    logging.config.dictConfig(log_config)
    
    # Adiciona um log para confirmar que a configuração foi aplicada.
    logger = logging.getLogger(__name__)
    logger.info("Application logger successfully configured.", extra={
        "logger_name": __name__,
        "root_log_level": log_config['root']['level'],
        "formatter": log_config['handlers']['console_stdout']['formatter'],
        "status": "success"
    })
