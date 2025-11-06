import os
import json
from typing import List, Optional, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Centralized application settings using Pydantic.

    Settings are loaded from environment variables. Default values are provided for
    non-sensitive configurations.
    """

    # --- API Keys & Secrets ---
    # These should be set in your .env file and have no defaults
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    GROQ_API_KEY: Optional[str] = Field(None, env="GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    GEMINI_API_KEY: Optional[str] = Field(None, env="GEMINI_API_KEY")
    WANDB_API_KEY: Optional[str] = Field(None, env="WANDB_API_KEY")
    BETTER_STACK_SOURCE_TOKEN: Optional[str] = Field(None, env="BETTER_STACK_SOURCE_TOKEN")
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")

    # --- Application Behavior ---
    FLASK_ENV: str = Field("development", env="FLASK_ENV")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    ALLOWED_ORIGINS: List[str] = Field(["*"], env="ALLOWED_ORIGINS")
    VISION_PROVIDER_ORDER: List[str] = Field(["openai", "gemini"], env="VISION_PROVIDER_ORDER")

    # --- Infrastructure ---
    REDIS_URL: Optional[str] = Field("memory://", env="REDIS_URL")
    CACHE_TYPE: str = Field("simple", env="CACHE_TYPE")
    CACHE_REDIS_URL: Optional[str] = Field(None, env="CACHE_REDIS_URL")

    # --- Monitoring & Features ---
    WANDB_ENABLED: bool = Field(False, env="WANDB_ENABLED")
    MODEL_CACHE_ENABLED: bool = Field(True, env="MODEL_CACHE_ENABLED")

    @validator('ALLOWED_ORIGINS', pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback: split by comma if JSON parsing fails
                return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    @validator('VISION_PROVIDER_ORDER', pre=True)
    def parse_vision_provider_order(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback: split by comma if JSON parsing fails
                return [provider.strip() for provider in v.split(',') if provider.strip()]
        return v

    class Config:
        # This tells Pydantic to load variables from a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create a single, importable instance of the settings
settings = Settings()
