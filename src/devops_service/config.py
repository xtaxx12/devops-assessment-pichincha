from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_key: str = Field(min_length=1, description="Valor esperado del header X-Parse-REST-API-Key")
    jwt_secret: str = Field(min_length=1, description="Secreto HS256 para firmar los JWT")
    jwt_ttl_seconds: int = Field(default=300, gt=0)
    app_name: str = "devops-service"


@lru_cache
def get_settings() -> Settings:
    return Settings()
