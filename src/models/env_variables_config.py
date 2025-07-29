from typing import Any

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentVariableSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    gem_api_base_url: str = Field(alias="GEM_API_BASE_URL")
    gem_client_id: str = Field(alias="GEM_CLIENT_ID")
    gem_client_secret: str = Field(alias="GEM_CLIENT_SECRET")
    gem_calculation_function_key: str = Field(alias="GEM_CALCULATION_FUNCTION_KEY")
    gem_calculation_function_url: str = Field(alias="GEM_CALCULATION_FUNCTION_URL")
    gem_batch_size: int = Field(120, alias="GEM_CHUNK_SIZE")
    gem_user_agent: str = Field("GEM_PROTOTYPE_SENSITIVITY/1.0", alias="GEM_USER_AGENT")

    def model_post_init(self, _: Any) -> None:
        for field_name, value in self.__dict__.items():
            if value is None:
                raise ValueError(f"Environment variable {field_name} must not be empty")


try:
    environment_variables = EnvironmentVariableSettings()  # type: ignore
except ValidationError as e:
    print("Validation error:", e)
except Exception as e:
    print("Other error:", e)
