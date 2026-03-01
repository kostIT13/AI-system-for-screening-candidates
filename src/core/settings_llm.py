from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LLMSettings(BaseSettings):
    OPENROUTER_API_KEY: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = Field(default="qwen/qwen3-coder:free", env="OPENROUTER_MODEL")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    
    LLM_TEMPERATURE: float = Field(default=0.1, ge=0.0, le=2.0, env="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=1000, ge=1, le=32000, env="LLM_MAX_TOKENS")
    
    USE_FALLBACK_ON_ERROR: bool = Field(default=True, env="USE_FALLBACK_ON_ERROR")
    USE_FALLBACK_ONLY: bool = Field(default=False, env="USE_FALLBACK_ONLY")

    @field_validator('OPENROUTER_API_KEY')
    @classmethod
    def warn_if_api_key_missing(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            logger.warning("OPENROUTER_API_KEY not set - fallback mode will be used")
        return v
    
    @model_validator(mode='after')
    def validate_consistency(self) -> 'LLMSettings':
        if self.USE_FALLBACK_ONLY and self.OPENROUTER_API_KEY:
            logger.info("ℹUSE_FALLBACK_ONLY=true - LLM will be skipped even with API key")
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" 

_llm_settings_cache: Optional[LLMSettings] = None

def get_llm_settings() -> LLMSettings:
    global _llm_settings_cache
    if _llm_settings_cache is None:
        try:
            _llm_settings_cache = LLMSettings()
            key_preview = _llm_settings_cache.OPENROUTER_API_KEY[:10] + "..." if _llm_settings_cache.OPENROUTER_API_KEY else "None"
            logger.info(f"LLMSettings loaded: model={_llm_settings_cache.OPENROUTER_MODEL}, key={key_preview}")
        except Exception as e:
            logger.error(f"Failed to load LLMSettings: {e}")
            raise
    return _llm_settings_cache