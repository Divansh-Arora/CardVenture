"""
Centralized app configuration.

Everything environment-specific (secrets, URLs, keys) is loaded here from
environment variables / a local .env file. Nothing sensitive is ever
hardcoded elsewhere in the codebase.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str

    # NVIDIA / Nemotron
    nvidia_api_key: str
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "nvidia/nemotron-3-ultra-550b-a55b"

    # CORS - comma-separated origins
    cors_origins: str = "http://localhost:5173"

    # JWT auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
