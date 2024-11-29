"""OpenRouter API client."""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from src.constants.api import FALLBACK_MODEL, OPENROUTER_MODELS
from src.utils.settings import settings

logger = logging.getLogger(__name__)

class OpenRouterAPIError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass

class RateLimitError(OpenRouterAPIError):
    """Error raised when API rate limit is exceeded."""
    pass

class OpenRouterAPI:
    """Client for OpenRouter API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenRouter API client."""
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise OpenRouterAPIError("OpenRouter API key not found in settings") from None

        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient(timeout=120.0)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/sage-ai/sage",
            "X-Title": "Sage AI"
        }
        self.max_retries = 3
        self.base_delay = 1  # Start with 1 second delay

    async def __aenter__(self):
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.client.aclose()

    def _select_model(self, task_type: str, fallback_model: Optional[str] = None) -> Optional[str]:
        """Select appropriate model based on task type."""
        if fallback_model:
            return fallback_model

        task_models = OPENROUTER_MODELS.get(task_type, [])
        return task_models[0] if task_models else None

    async def _handle_rate_limit(self, retry_count: int) -> None:
        """Handle rate limit with exponential backoff."""
        delay = self.base_delay * (2 ** retry_count)  # Exponential backoff
        logger.warning(f"Rate limit exceeded. Retrying in {delay} seconds...")
        await asyncio.sleep(delay)

    async def complete(
        self,
        messages: List[Dict[str, str]],
        task_type: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        fallback_model: Optional[str] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Complete a chat conversation."""
        try:
            model = self._select_model(task_type, fallback_model)
            if not model:
                raise OpenRouterAPIError(f"No model found for task type: {task_type}") from None

            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": { "type": "json_object" }
            }
            logger.info(f"OpenRouter API Request to {self.base_url}/chat/completions:")
            logger.info(f"Headers: {self.headers}")
            logger.info(f"Request Data: {request_data}")

            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=request_data
            )

            try:
                response.raise_for_status()
            except httpx.HTTPError as e:
                logger.error(f"HTTP Error: {str(e)}")
                logger.error(f"Response Status: {response.status_code}")
                logger.error(f"Response Text: {response.text}")

                # Check for rate limit error
                if "rate limit exceeded" in str(e).lower():
                    if retry_count < self.max_retries:
                        await self._handle_rate_limit(retry_count)
                        return await self.complete(
                            messages=messages,
                            task_type=task_type,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            fallback_model=fallback_model,
                            retry_count=retry_count + 1
                        )
                    raise RateLimitError("Rate limit exceeded and max retries reached") from e

                # Check for blocklist error
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
                raise OpenRouterAPIError(f"HTTP error occurred: {str(e)}") from e

            try:
                response_data = response.json()
                logger.info(f"OpenRouter API Raw Response: {response_data}")
                return response_data
            except Exception as e:
                logger.error(f"Error parsing response JSON: {str(e)}")
                logger.error(f"Raw Response Text: {response.text}")
                raise OpenRouterAPIError(f"Failed to parse response JSON: {str(e)}") from e

        except Exception as e:
            if isinstance(e, (OpenRouterAPIError, RateLimitError)):
                raise
            raise OpenRouterAPIError(f"Error during API request: {str(e)}") from e
