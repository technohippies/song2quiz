"""OpenRouter API client."""
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from src.utils.settings import settings
from src.constants.api import OPENROUTER_MODELS

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
        logger.debug(f"Task type: {task_type}, Selected model: {fallback_model}")
        
        if fallback_model:
            return fallback_model
        
        task_models = OPENROUTER_MODELS.get(task_type, [])
        return task_models[0] if task_models else None
    
    def complete(
        self,
        messages: List[Dict[str, str]],
        task_type: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        fallback_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete a chat conversation."""
        model = self._select_model(task_type, fallback_model)
        if not model:
            raise OpenRouterAPIError(f"No model found for task type: {task_type}")
        
        try:
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
            
            response_data = response.json()
            logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
            
            content = response_data["choices"][0]["message"]["content"]
            logger.info(f"Raw content: {repr(content)}")
            
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse response as JSON: {str(e)}")
                return {"content": content}
            
        except httpx.HTTPError as e:
            if "blocklist" in str(e).lower() and not fallback_model:
                # Try fallback model
                fallback = "nvidia/llama-3.1-nemotron-70b-instruct"
                logger.warning(f"Model {model} blocked, trying fallback model: {fallback}")
                return self.complete(
                    messages=messages,
                    task_type=task_type,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    fallback_model=fallback
                )
            raise OpenRouterAPIError(f"HTTP error: {str(e)}") from e
        except Exception as e:
            raise OpenRouterAPIError(f"Unexpected error: {str(e)}") from e