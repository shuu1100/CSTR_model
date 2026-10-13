"""Application configuration and environment settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """CSTR Lab Backend Settings."""

    app_name: str = "CSTR Lab API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    # CORS origins: restricted to local development origins
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Computation safety limits
    max_simulation_horizon_min: float = 10000.0
    max_output_points: int = 10000

    # Persistence settings
    database_url: str = "sqlite:///data/cstr_lab.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
