import os
from collections.abc import Callable
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

check_env: Callable[[str], bool] = lambda env_key: (False, True)[os.getenv(env_key) in ["true", "True", "1"]]


class Settings(BaseSettings):
    DEBUG: bool = False
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    RELOAD: bool = True
    PAYLOAD_ENCRYPTION: bool = Field(default_factory=lambda: check_env("PAYLOAD_ENCRYPTION"))
    JWT_PAYLOAD_ENCRY: str = "29WIjxes6WgHJPfC0ngT9TG7f1Grhky8SpuZrkEC86U="
    APP_LOG_LEVEL: Literal["critical", "error", "info", "debug"] = "debug"
    ENVIRONMENT: Literal["local", "platform", "production"] = "local"
    WS_MAX_QUEUE: int = 100
    WORKERS: int = 1
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_BASE_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536
    JWT_SECRET_KEY: str = (
        "35678eb97d529e5502c0db50da70e4304ba9361296e91e718e176ba861eb6cdfe2e99b907e52a9e353354a609f9e7e6b6b73cb9907f84aa84bacf29816f14a77"
    )
    JWT_ALGORITHM: str = "HS256"
    QDRANT_CLOUD: bool = Field(default_factory=lambda: check_env("QDRANT_CLOUD"))
    QDRANT_URL: str = "https://qdrant.mypits.org"
    QDRANT_TLS: bool = Field(default_factory=lambda: check_env("QDRANT_TLS"))
    QDRANT_API_KEY: str | None = "mqbglPIm1s4MrKcHalNMRhKYR9noUT_QxBSX8TXrtXdJgFFUUc67sQ"
    QDRANT_MAIN_COLLECTION: str = "360inControl"
    QDRANT_CACHE_COLLECTION: str = "llm_cache"
    QDRANT_SEARCH_LIMIT: int = 10
    QDRANT_CACHE_SCORE: float = 0.8
    FORWARDED_ALLOW_IPS: list[str] | str = "*"


class ProductionSettings(Settings):
    WORKERS: int
    QDRANT_URL: str
    QDRANT_CLOUD: bool
    QDRANT_API_KEY: str = Field(default_factory=lambda: os.getenv("QDRANT_API_KEY") if check_env("QDRANT_CLOUD") else "")
    DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 80
    RELOAD: bool = False
    APP_LOG_LEVEL: Literal["critical", "error", "info", "debug"] = "info"
    ENVIRONMENT: Literal["local", "platform", "production"] = "production"

    model_config = SettingsConfigDict(
        validate_default=False,
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
    )

    @model_validator(mode="after")
    def check_worker_config(self) -> Self:  # pragma: no cover
        """

        :return:
        """
        if self.RELOAD and self.WORKERS > 1:
            self.RELOAD = False
        return self


@lru_cache
def get_config(env: str) -> Settings:
    """

    :param env:
    :return:
    """
    config_type = {
        "production": ProductionSettings,
        "local": Settings,
    }
    application_config = config_type[env]
    config: Settings = application_config()

    if config.ENVIRONMENT in ["local"]:  # pragma: no cover
        for key, value in config.model_dump().items():
            if isinstance(value, bool):
                continue
            os.environ.setdefault(key, str(value))
    return config


settings = get_config(os.getenv("ENVIRONMENT", "local"))
