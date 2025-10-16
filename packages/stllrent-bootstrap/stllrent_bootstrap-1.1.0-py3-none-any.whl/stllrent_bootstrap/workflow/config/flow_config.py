from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, HttpUrl, ValidationError, model_validator
import logging
import os

log = logging.getLogger(__name__)

# Definição da sua classe de Settings
class WorkflowMonitoringSettings(BaseSettings):
    # --- Configurações de Conexão ---
    FLOWMON_URL: HttpUrl = Field(...)
    FLOWMON_API_PRIMARY_PATH: str = Field(...)

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),
        env_file_encoding='utf-8',
        extra='ignore', # Importante: ignora variáveis não definidas no modelo
    )

try:
    settings = WorkflowMonitoringSettings()
    log.info("Configurações para Workflow Monitoring carregadas com sucesso.")


except ValidationError as e:
    # Em caso de erro, configure um logger básico para garantir que a mensagem seja vista
    log.error(f"ERRO CRÍTICO: Falha na validação das configurações: {e.errors()}")
    raise
except Exception as e:
    log.error(f"ERRO CRÍTICO: Não foi possível carregar as configurações: {e}")
    raise