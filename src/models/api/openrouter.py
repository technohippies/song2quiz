"""OpenRouter API client."""
import logging
from typing import Dict, Any, Optional, List
import httpx
from src.utils.settings import settings
from src.constants.api import OPENROUTER_MODELS, FALLBACK_MODEL
from src.services.langfuse import langfuse

logger = logging.getLogger(__name__)

class OpenRouterAPIError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass

class OpenRouterAPI:
    """Client for OpenRouter API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenRouter API client."""
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise OpenRouterAPIError("OpenRouter API key not found in settings")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.Client(timeout=120.0)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/sage-ai/sage",
            "X-Title": "Sage AI"
        }
    
    def _select_model(self, task_type: str, fallback_model: Optional[str] = None) -> Optional[str]:
        """Select appropriate model based on task type."""
        if fallback_model:
            return fallback_model
            
        task_models = OPENROUTER_MODELS.get(task_type, [])
        return task_models[0] if task_models else None
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        task_type: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        fallback_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete a chat conversation."""
        try:
            model = self._select_model(task_type, fallback_model)
            if not model:
                raise OpenRouterAPIError(f"No model found for task type: {task_type}")
            
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            if "blocklist" in str(e).lower() and not fallback_model:
                fallback = FALLBACK_MODEL[0]
                logger.warning(f"Model {model} blocked, trying fallback: {fallback}")
                return await self.complete(
                    messages=messages,
                    task_type=task_type,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    fallback_model=fallback
                )
                
            raise OpenRouterAPIError(f"HTTP error: {str(e)}") from e