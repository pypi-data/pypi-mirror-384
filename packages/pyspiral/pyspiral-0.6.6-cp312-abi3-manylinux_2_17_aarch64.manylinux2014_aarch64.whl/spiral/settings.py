import functools
import os
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from pydantic import Field, ValidatorFunctionWrapHandler, WrapValidator
from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from spiral.core.authn import Authn, DeviceCodeAuth, Token
from spiral.core.client import Spiral

if TYPE_CHECKING:
    from spiral.api import SpiralAPI

DEV = "PYTEST_VERSION" in os.environ or bool(os.environ.get("SPIRAL_DEV", None))
CI = "GITHUB_ACTIONS" in os.environ

APP_DIR = Path(typer.get_app_dir("pyspiral"))
LOG_DIR = APP_DIR / "logs"

PACKAGE_NAME = "pyspiral"


def validate_token(v, handler: ValidatorFunctionWrapHandler):
    if isinstance(v, str):
        return Token(v)
    else:
        raise ValueError("Token value must be a string")


TokenType = Annotated[Token, WrapValidator(validate_token)]


class SpiralDBSettings(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)

    host: str = "localhost" if DEV else "api.spiraldb.com"
    port: int = 4279 if DEV else 443
    ssl: bool = not DEV
    token: TokenType | None = None

    @property
    def uri(self) -> str:
        return f"{'https' if self.ssl else 'http'}://{self.host}:{self.port}"


class SpfsSettings(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)

    host: str = "localhost" if DEV else "spfs.spiraldb.dev"
    port: int = 4295 if DEV else 443
    ssl: bool = not DEV

    @property
    def uri(self) -> str:
        return f"{'https' if self.ssl else 'http'}://{self.host}:{self.port}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="SPIRAL__",
        frozen=True,
    )

    spiraldb: SpiralDBSettings = Field(default_factory=SpiralDBSettings)
    spfs: SpfsSettings = Field(default_factory=SpfsSettings)
    file_format: str = Field(default="vortex")

    @functools.cached_property
    def api(self) -> "SpiralAPI":
        from spiral.api import SpiralAPI

        return SpiralAPI(self.authn, base_url=self.spiraldb.uri)

    @functools.cached_property
    def core(self) -> Spiral:
        return Spiral(
            api_url=self.spiraldb.uri,
            spfs_url=self.spfs.uri,
            authn=self.authn,
        )

    @functools.cached_property
    def authn(self):
        if self.spiraldb.token:
            return Authn.from_token(self.spiraldb.token)
        return Authn.from_fallback(self.spiraldb.uri)

    @functools.cached_property
    def device_code_auth(self) -> DeviceCodeAuth:
        return DeviceCodeAuth.default()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        init_settings: InitSettingsSource,
        **kwargs,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, dotenv_settings, init_settings


@functools.cache
def settings() -> Settings:
    return Settings()
