# src/auth_rsha/config.py
from pydantic_settings import BaseSettings
from pydantic import Field

class AuthSettings(BaseSettings):
    jwt_secret: str = Field(..., min_length=32)
    jwt_alg: str = "HS256"
    access_ttl: int = 3600
    refresh_ttl: int = 60 * 60 * 24 * 7
    token_url_path: str = "/auth/token"
    issuer: str | None = None
    audience: str | None = None
    leeway_sec: int = 30  # допуск по времени

    model_config = {
        "env_prefix": "AUTH_RSHA_",
        "env_file": ".env",
        "extra": "ignore",
    }
