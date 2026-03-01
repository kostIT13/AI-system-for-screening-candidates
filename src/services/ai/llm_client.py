from openai import AsyncOpenAI
from src.core.config import settings
from typing import Optional, Dict
import json
import re


class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            extra_headers={
                "HTTP-Referer": "https://your-app.com", 
                "X-Title": "AI Screening System",
            }
        )
        return response.choices[0].message.content


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
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        fixed = content.strip().strip('```json').strip('```').strip()
        try:
            return json.loads(fixed)
        except:
            pass
        
        raise ValueError(f"Failed to parse JSON: {content[:200]}...")