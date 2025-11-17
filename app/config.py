"""
Configurações da aplicação usando Pydantic Settings
"""
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field
import json

class Settings(BaseSettings):
    """Configurações principais da aplicação"""

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/granaiadb",
        description="URL de conexão assíncrona com PostgreSQL"
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/granaiadb",
        description="URL de conexão síncrona (para Alembic)"
    )

    # PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "granaiadb"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Application
    APP_NAME: str = "Grana IA API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:8000"]

    def get_cors_origins(self) -> List[str]:
        """
        Garante que CORS_ORIGINS sempre seja uma lista válida,
        mesmo quando vier como string do .env.
        """
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS  # já é lista, ok

        # Se vier como string JSON
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            pass

        # Se vier como 'a,b,c'
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instância global de configurações
settings = Settings()
