from __future__ import annotations

import enum
import json
import logging
import os
from functools import lru_cache
from importlib.metadata import Distribution, PackageNotFoundError
from typing import Any, Dict  # noqa: UP035

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

logger = logging.getLogger(__name__)

# If the package is editable, we want to use:
# base_url = localhost:3000
# base_api_url = localhost:8000


def is_editable_install() -> bool:
    if os.getenv("ENVIRONMENT") == "test" or os.getenv("EXPONENT_TEST_AUTO_UPGRADE"):
        # We should explicitly set these variables
        # in test when needed
        return False

    try:
        dist = Distribution.from_name("indent")
    except PackageNotFoundError:
        logger.info("No distribution info found for indent")
        return False

    direct_url = dist.read_text("direct_url.json")
    if not direct_url:
        return False

    try:
        direct_url_json = json.loads(direct_url)
    except json.JSONDecodeError:
        logger.warning("Failed to decode distribution info for exponent-run")
        return False

    pkg_is_editable = direct_url_json.get("dir_info", {}).get("editable", False)
    return bool(pkg_is_editable)


class Environment(str, enum.Enum):
    test = "test"
    development = "development"
    staging = "staging"
    production = "production"

    @property
    def is_local(self) -> bool:
        return self in [Environment.development, Environment.test]


class APIKeys(BaseModel):
    development: str | None = None
    staging: str | None = None
    production: str | None = None


SETTINGS_FOLDER = os.path.expanduser("~/.config/indent")
SETTINGS_FILE_PATH = os.path.join(SETTINGS_FOLDER, "config.json")


class GlobalExponentOptions(BaseModel):
    git_warning_disabled: bool = False
    auto_upgrade: bool = True
    base_api_url_override: str | None = None
    base_ws_url_override: str | None = None
    use_default_colors: bool = False


class Settings(BaseSettings):
    environment: Environment
    base_url: str
    base_api_url: str
    base_ws_url: str

    exponent_api_key: str | None = None
    extra_exponent_api_keys: Dict[str, str] = {}  # noqa: UP006

    options: GlobalExponentOptions = GlobalExponentOptions()

    log_level: str = "WARNING"

    model_config = SettingsConfigDict(
        json_file=SETTINGS_FILE_PATH,
        json_file_encoding="utf-8",
        env_prefix="EXPONENT_",
    )

    def get_base_api_url(self) -> str:
        return self.options.base_api_url_override or self.base_api_url

    def get_base_ws_url(self) -> str:
        return self.options.base_ws_url_override or self.base_ws_url

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, JsonConfigSettingsSource(settings_cls), init_settings

    def write_settings_to_config_file(self) -> None:
        os.makedirs(SETTINGS_FOLDER, exist_ok=True)
        with open(SETTINGS_FILE_PATH, "w") as f:
            f.write(
                self.model_dump_json(
                    include=self.config_file_keys, exclude_defaults=True
                )
            )

    def get_config_file_settings(self) -> dict[str, Any]:
        return self.model_dump(include=self.config_file_keys, exclude_defaults=True)

    @property
    def config_file_path(self) -> str:
        return SETTINGS_FILE_PATH

    @property
    def config_file_keys(self) -> set[str]:
        return {"exponent_api_key", "extra_exponent_api_keys", "options"}

    @property
    def api_key(self) -> str | None:
        if self.environment.is_local:
            return self.extra_exponent_api_keys.get(Environment.development)
        elif self.environment == Environment.staging:
            return self.extra_exponent_api_keys.get(Environment.staging)
        elif self.environment == Environment.production:
            return self.exponent_api_key
        else:
            raise ValueError(f"Unknown environment: {self.environment}")

    def update_api_key(self, api_key: str) -> None:
        if self.environment == Environment.development:
            self.extra_exponent_api_keys[Environment.development] = api_key
        elif self.environment == Environment.staging:
            self.extra_exponent_api_keys[Environment.staging] = api_key
        elif self.environment == Environment.production:
            self.exponent_api_key = api_key


@lru_cache(maxsize=1)
def get_settings(use_prod: bool = False, use_staging: bool = False) -> Settings:
    if is_editable_install() and not (use_prod or use_staging):
        base_url = "http://localhost:3000"
        base_api_url = "http://localhost:8000"
        base_ws_url = "ws://localhost:8000"
        environment = Environment.development
    elif use_staging:
        base_url = "https://staging.indent.com"
        base_api_url = "https://staging-api.indent.com"
        base_ws_url = "wss://ws-staging-api.indent.com"
        environment = Environment.staging
    else:
        base_url = "https://app.indent.com"
        base_api_url = "https://api.indent.com"
        base_ws_url = "wss://ws-api.indent.com"
        environment = Environment.production

    return Settings(
        base_url=base_url,
        base_api_url=base_api_url,
        base_ws_url=base_ws_url,
        environment=environment,
    )
