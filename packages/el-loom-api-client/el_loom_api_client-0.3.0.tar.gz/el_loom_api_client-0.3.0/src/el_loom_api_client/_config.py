import sys
from pathlib import Path

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

_CONFIG_FILE_PATH = Path.home() / ".loom" / "config.json"


class Config(BaseSettings):
    api_url: HttpUrl | None = Field(
        default=None,
        description="The base URL of the Loom API.",
    )

    api_token: SecretStr | None = Field(
        default=None,
        description="The API token for authenticating with the Loom API.",
    )

    model_config = SettingsConfigDict(
        validate_assignment=True,
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LOOM_",
        extra="ignore",
        json_file=_CONFIG_FILE_PATH,
        json_file_encoding="utf-8",
    )

    # In merge order:
    # - defaults
    # - json file
    # - .env file
    # - environment variables
    # - initialization arguments
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            # omitted: file_secret_settings,
            JsonConfigSettingsSource(settings_cls),
        )


def print_config_error_help() -> None:
    config_dir = _CONFIG_FILE_PATH.parent
    print(
        f"""
Error: Loom APIs configuration file not found!

Please create a config file at: {_CONFIG_FILE_PATH}
You may need to create the directory first: mkdir -p {config_dir}

The config file should contain JSON with the following structure:
{{
    "api_url": "https://your-loom-api-endpoint.com",
    "api_token": "your-api-token"
}}

Alternatively, you can set two environment variables:
- LOOM_API_URL
- LOOM_API_TOKEN
    """,
        flush=True,
        file=sys.stderr,  # Print to stderr
    )
