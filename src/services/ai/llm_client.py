from openai import AsyncOpenAI
import json
import re
import logging
from typing import Optional, Dict
from src.core.settings_llm import get_llm_settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self.settings = get_llm_settings()
  
        key_preview = self.settings.OPENROUTER_API_KEY[:10] + "..." if self.settings.OPENROUTER_API_KEY else "None"
        logger.info(f"LLMClient init: key={key_preview}, model={self.settings.OPENROUTER_MODEL}, base_url={self.settings.OPENROUTER_BASE_URL}")
        
        if not self.settings.OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY is empty - LLM calls will fail")
        
        self.client = AsyncOpenAI(
            api_key=self.settings.OPENROUTER_API_KEY,
            base_url=self.settings.OPENROUTER_BASE_URL
        )
        self.model = self.settings.OPENROUTER_MODEL
        self.temperature = self.settings.LLM_TEMPERATURE
        self.max_tokens = self.settings.LLM_MAX_TOKENS

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        logger.debug(f"Calling LLM: model={self.model}, prompt_len={len(prompt)}")
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            extra_headers={
                "HTTP-Referer": "https://github.com/kostIT13/AI-system-for-screening-candidates",
                "X-Title": "AI Screening System"
            }
        )
        
        content = response.choices[0].message.content
        logger.debug(f"LLM response received: {len(content)} chars")
        return content

    async def generate_json_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> Dict:
        json_instruction = "\n\nОтвечай ТОЛЬКО валидным JSON. Без markdown, без пояснений."
        full_prompt = f"{prompt}{json_instruction}"
        
        content = await self.generate_response(full_prompt, system_prompt)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON, trying fallback parsers")
            try:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
            try:
                fixed = content.strip().strip('```json').strip('```').strip()
                return json.loads(fixed)
            except:
                pass
            
            logger.error(f"Failed to parse JSON from LLM response: {content[:200]}...")
            raise ValueError(f"Failed to parse JSON from LLM response: {content[:200]}...")