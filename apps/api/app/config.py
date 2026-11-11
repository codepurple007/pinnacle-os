from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://pinnacle:pinnacle@localhost:5432/pinnacleos"
    token_encryption_key: str
    web_origin: str = "http://localhost:3000"
    api_public_url: str = "http://localhost:8000"
    dev_mode: bool = True
    dev_ingest_enabled: bool = True
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/v1/oauth/google/callback"
    founder_email: str = "alex@pinnacle.example"
    founder_name: str = "Alex Quinn"


@lru_cache
def get_settings() -> Settings:
    return Settings()
