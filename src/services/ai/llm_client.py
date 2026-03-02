from openai import AsyncOpenAI
import json
import re
import logging
from typing import Optional, Dict, Any
from src.core.settings_llm import get_llm_settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self.settings = get_llm_settings()
        self.model = self.settings.OLLAMA_MODEL
        self.base_url = self.settings.OLLAMA_BASE_URL
        self.api_key = self.settings.OLLAMA_API_KEY
        self.temperature = self.settings.LLM_TEMPERATURE
        self.max_tokens = self.settings.LLM_MAX_TOKENS
        
        logger.info(
            f"LLMClient init: provider=ollama, model={self.model}, "
            f"base_url={self.base_url}, temperature={self.temperature}, max_tokens={self.max_tokens}"
        )
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=60.0 
            
        )

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        logger.debug(f"Calling Ollama: model={self.model}, prompt_len={len(prompt)}")
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False
        )
        
        content = response.choices[0].message.content or ""
        logger.debug(f"Ollama response: {len(content)} chars")
        return content

    async def generate_json_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        json_instruction = (
            "\n\n### ВАЖНО ###\n"
            "Ответь ТОЛЬКО валидным JSON объектом. "
            "Без markdown, без текста до или после. "
            "Начни с { и закончи }."
        )
        full_prompt = f"{prompt}{json_instruction}"
        
        content = await self.generate_response(full_prompt, system_prompt)
        return self._parse_json_robust(content)

    def _parse_json_robust(self, content: str) -> Dict[str, Any]:
        logger.debug(f"Raw response preview: {repr(content[:200])}")
        
        original = content
        content = content.strip()
        
        if content.startswith('```'):
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            content = content.rstrip('`').strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.debug(f"Direct parse failed: {e}")
        
        
        try:
            start = content.find('{')
            end = content.rfind('}') 
            if start != -1 and end > start:
                json_str = content[start:end+1]
                logger.debug(f"Extracted by brackets: {json_str[:100]}...")
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.debug(f"Bracket extract failed: {e}")
        
        try:
            fixed = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            return json.loads(fixed)
        except:
            pass
        
        try:
            result = {}
            score = re.search(r'"match_score"\s*:\s*(\d+\.?\d*)', content)
            if score:
                result["match_score"] = float(score.group(1))
            conf = re.search(r'"confidence"\s*:\s*(\d+\.?\d*)', content)
            if conf:
                result["confidence"] = float(conf.group(1))
            
            if result:
                result["confidence"] = result.get("confidence", 0.5)
                result["analysis"] = {"parsed_partially": True}
                result["method"] = "partial_parse"
                logger.warning(f"Partial parse success: {result}")
                return result
        except Exception as e:
            logger.debug(f"Partial parse failed: {e}")
        
        logger.warning(f"JSON parse failed. Preview: {original[:150]}...")
        return {
            "match_score": 50,
            "confidence": 0.5,
            "analysis": {
                "error": "JSON parse failed",
                "model": self.model,
                "response_preview": original[:100]
            },
            "method": "fallback"
        }