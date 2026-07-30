from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# Eu centralizo as configurações da aplicação aqui.
# Uso `pydantic-settings` para facilitar o carregamento via `.env`.
class Settings(BaseSettings):
    # Configurei para ler `.env` e ignorar extras não esperados.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # URL do banco — em ambiente de dev uso o host local.
    database_url: str = "postgresql://simulador:simulador@localhost:5432/simulador"
    # Taxa de juros mensal padrão (1,79% a.m.) como Decimal para precisão monetária.
    taxa_juros_mensal: Decimal = Decimal("0.0179")
    # Multiplicador para calcular limite do cartão consignado (1.5× salário).
    limite_cartao_multiplicador: Decimal = Decimal("1.5")
    app_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    # Uso lru_cache para manter a mesma instância durante a execução.
    return Settings()
