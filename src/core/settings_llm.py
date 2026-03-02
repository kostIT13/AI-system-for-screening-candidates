from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator, ConfigDict  # ✅ Добавили ConfigDict
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LLMSettings(BaseSettings):
    OLLAMA_MODEL: str = Field(default="qwen3:4b", env="OLLAMA_MODEL")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434/v1", env="OLLAMA_BASE_URL")
    OLLAMA_API_KEY: Optional[str] = Field(default="ollama", env="OLLAMA_API_KEY")
    LLM_TEMPERATURE: float = Field(default=0.1, ge=0.0, le=2.0, env="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=500, ge=1, le=32000, env="LLM_MAX_TOKENS")
    USE_FALLBACK_ON_ERROR: bool = Field(default=True, env="USE_FALLBACK_ON_ERROR")
    USE_FALLBACK_ONLY: bool = Field(default=False, env="USE_FALLBACK_ONLY")

    @field_validator('OLLAMA_MODEL')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        if not v or not v.strip():
            logger.warning("OLLAMA_MODEL is empty, using default: qwen3:4b")
            return "qwen3:4b"
        return v.strip()
    
    @field_validator('OLLAMA_BASE_URL')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        return v.strip()
    
    @model_validator(mode='after')
    def validate_consistency(self) -> 'LLMSettings':
        if self.USE_FALLBACK_ONLY:
            logger.info("⚙ USE_FALLBACK_ONLY=true - LLM будет пропущен, используется rule-based")
        else:
            logger.info(f"⚙ LLM mode: provider=ollama, model={self.OLLAMA_MODEL}, url={self.OLLAMA_BASE_URL}")
        return self

    # ✅ Pydantic v2 стиль
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


_llm_settings_cache: Optional[LLMSettings] = None

def get_llm_settings() -> LLMSettings:
    global _llm_settings_cache
    if _llm_settings_cache is None:
        try:
            _llm_settings_cache = LLMSettings()
            logger.info(
                f"LLMSettings loaded: "
                f"provider=ollama, "
                f"model={_llm_settings_cache.OLLAMA_MODEL}, "
                f"base_url={_llm_settings_cache.OLLAMA_BASE_URL}, "
                f"temperature={_llm_settings_cache.LLM_TEMPERATURE}, "
                f"max_tokens={_llm_settings_cache.LLM_MAX_TOKENS}"
            )
        except Exception as e:
            logger.error(f"Failed to load LLMSettings: {e}")
            raise
    return _llm_settings_cache