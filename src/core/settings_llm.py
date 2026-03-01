from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from typing import Optional


class LLMSettings(BaseSettings):
    
    OPENROUTER_API_KEY: Optional[str] = Field(..., description="API ключ OpenRouter")
    LLM_MODEL: str = Field(default="qwen/qwen3-coder:free", description="ID модели")
    LLM_TEMPERATURE: float = Field(default=0.1, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int = Field(default=1000, ge=1, le=32000)
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")

    @field_validator('OPENROUTER_API_KEY')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('OPENROUTER_API_KEY is required')
        return v.strip()
    
    @field_validator('LLM_MODEL')
    @classmethod
    def validate_model(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('LLM_MODEL cannot be empty')
        return v.strip()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_llm_settings() -> LLMSettings:
    return LLMSettings()


llm_settings = get_llm_settings()