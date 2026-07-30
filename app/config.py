from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://simulador:simulador@localhost:5432/simulador"
    taxa_juros_mensal: Decimal = Decimal("0.0179")
    limite_cartao_multiplicador: Decimal = Decimal("1.5")
    app_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
