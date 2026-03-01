from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Literal, Optional
from functools import lru_cache


class LLMSettings(BaseSettings):

    LLM_PROVIDER: Literal["openrouter", "ollama", "groq", "openai"] = Field(
        default="openrouter",
        description="LLM провайдер: openrouter, ollama, groq, openai"
    )
    
    OPENROUTER_API_KEY: Optional[str] = Field(default=None)
    GROQ_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    
    LLM_MODEL: str = Field(default="qwen/qwen3-coder:free", description="ID модели")
    LLM_TEMPERATURE: float = Field(default=0.1, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int = Field(default=1000, ge=1, le=32000)
    

    @field_validator('LLM_MODEL')
    @classmethod
    def validate_model(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError('LLM_MODEL cannot be empty')
        return v.strip()
    
    def get_api_key(self) -> Optional[str]:
        keys = {
            "openrouter": self.OPENROUTER_API_KEY,
        }
        return keys.get(self.LLM_PROVIDER)
    
    def get_base_url(self) -> Optional[str]:
        urls = {
            "openrouter": "https://openrouter.ai/api/v1",
        }
        return urls.get(self.LLM_PROVIDER)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_llm_settings() -> LLMSettings:
    return LLMSettings()


llm_settings = get_llm_settings()