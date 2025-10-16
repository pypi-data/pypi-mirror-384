from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, HttpUrl, PostgresDsn, ValidationError, model_validator
from typing import Optional
import os

# Definição da sua classe de Settings
class BaseAppSettings(BaseSettings):
    # --- Configurações de Conexão ---
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = Field(default=None)
    APP_LOG_FORMATTER: Optional[str] = Field(default="json")
    APP_LOG_LEVEL: Optional[str] = Field(default="DEBUG")
    
    DATABASE_HOST: str = Field(alias="DATABASE_HOST")
    DATABASE_USER: str = Field(alias="DATABASE_USER")
    DATABASE_PASS: str = Field(alias="DATABASE_PASS")
    DATABASE_PORT: str = Field(alias="DATABASE_PORT")
    DATABASE_NAME: str = Field(alias="DATABASE_NAME")

    SQL_ALCHEMY_ECHO: bool = Field(default=False)
    SQL_ALCHEMY_TRACK_MODIFICATIONS: bool = Field(default=False)
    SQLALCHEMY_MAX_OVERFLOW: int = Field(default=10)
    SQLALCHEMY_POOL_RECYCLE: bool = Field(default=False)
    SQLALCHEMY_POOL_SIZE: int = Field(default=4)

    APP_ENVIRONMENT: Optional[str] = Field(default="nonprod", alias="APP_ENVIRONMENT")
    APP_LOG_LEVEL: Optional[str] = Field(default="INFO", alias="APP_LOG_LEVEL")
    APP_NAME: str = Field(default="stllrent-contract")
    APP_PORT: int = Field(default=8080)

    FLASK_ENV: Optional[str] = Field(default="production")
    API_PRIMARY_PATH: str = Field(...)

    # Path para o carregamento dinâmico dos models SQLAlchemy
    MODEL_DISCOVERY_PATHS: Optional[list[str]] = Field(default=["model"])

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),
        env_file_encoding='utf-8',
        extra='ignore', # Importante: ignora variáveis não definidas no modelo
    )

    @model_validator(mode='after')
    def define_url_database(self) -> PostgresDsn:
        
        if self.SQLALCHEMY_DATABASE_URI is None:
            self.SQLALCHEMY_DATABASE_URI = f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASS}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        
        return self