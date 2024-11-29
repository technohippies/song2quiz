"""Client for making requests to OpenRouter API with configurable models"""

import json
import logging
import sys
from typing import Any, Dict, Optional

import httpx

from src.constants.api import OPENROUTER_MODELS
from src.utils.settings import settings

# FORCE LOGS TO SHOW
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False  # Don't double log


class OpenRouterAPIError(Exception):
    """Custom exception for OpenRouter API errors."""

    pass


class OpenRouterClient:
    """Client for making requests to OpenRouter API with configurable models"""

    def __init__(self, task_type: Optional[str] = None):
        """Initialize client with optional task type to determine model."""
        self.api_key = settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise OpenRouterAPIError("OpenRouter API key not found in settings")

        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.Client(timeout=15.0)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/sage-ai/sage",
            "X-Title": "Sage AI",
            "Content-Type": "application/json",
        }

        self.task_type = task_type or "default"
        self._failed_models = set()
        logger.debug(f"Task type: {self.task_type}")

    def _select_model(self, fallback_model: Optional[str] = None) -> str:
        """Select appropriate model based on task type and failure history."""
        if fallback_model:
            logger.info(f"Using specified fallback model: {fallback_model}")
            return fallback_model

        task_models = OPENROUTER_MODELS.get(
            self.task_type, OPENROUTER_MODELS["default"]
        )
        if not task_models:
            raise OpenRouterAPIError(
                f"No models configured for task type: {self.task_type}"
            )

        # If primary model has failed before, use fallback immediately
        primary_model = task_models[0]
        if primary_model in self._failed_models:
            fallback = OPENROUTER_MODELS["fallback"][0]
            logger.info(
                f"Using fallback model {fallback} (primary model {primary_model} failed previously)"
            )
            return fallback

        logger.info(f"Using model: {primary_model}")
        return primary_model

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        fallback_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Complete a chat conversation."""
        try:
            model = self._select_model(fallback_model)

            request_data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt or ""},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens or 256,
                "response_format": {"type": "json_object"},
            }

            logger.info("=" * 100)
            logger.info("OUTGOING REQUEST:")
            logger.info(f"URL: {self.base_url}/chat/completions")
            logger.info(f"Headers: {json.dumps(self.headers, indent=2)}")
            logger.info(f"Data: {json.dumps(request_data, indent=2)}")
            logger.info("=" * 100)

            try:
                response = self.client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=request_data,
                )

                logger.info("=" * 100)
                logger.info("RAW RESPONSE:")
                logger.info(f"Status: {response.status_code}")
                logger.info(f"Headers: {dict(response.headers)}")
                logger.info(f"Text: {response.text}")
                logger.info("=" * 100)

                response.raise_for_status()

                response_data = response.json()
                logger.info("=" * 100)
                logger.info("PARSED RESPONSE:")
                logger.info(json.dumps(response_data, indent=2))
                logger.info("=" * 100)

                content = response_data["choices"][0]["message"]["content"]
                logger.info("=" * 100)
                logger.info("CONTENT:")
                logger.info(content)
                logger.info("=" * 100)

                try:
                    result = json.loads(content)
                    logger.info("=" * 100)
                    logger.info("PARSED CONTENT:")
                    logger.info(json.dumps(result, indent=2))
                    logger.info("=" * 100)

                    if not isinstance(result, dict):
                        raise json.JSONDecodeError(
                            "Response must be a JSON object", content, 0
                        )
                    return result
                except json.JSONDecodeError as e:
                    if not fallback_model and "google/gemini" in model:
                        self._failed_models.add(model)
                        fallback = OPENROUTER_MODELS["fallback"][0]
                        logger.warning(
                            f"🔄 JSON parsing failed with {model}, falling back to {fallback}"
                        )
                        return await self.complete(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            fallback_model=fallback,
                        )
                    logger.error(f"❌ JSON parsing failed with {model}: {str(e)}")
                    return {"error": f"Failed to parse response as JSON: {str(e)}"}

            except httpx.HTTPError as e:
                if "blocklist" in str(e).lower() and not fallback_model:
                    self._failed_models.add(model)
                    fallback = OPENROUTER_MODELS["fallback"][0]
                    logger.warning(
                        f"⚠️ Model {model} blocked, falling back to {fallback}"
                    )
                    return await self.complete(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        fallback_model=fallback,
                    )
                return {"error": f"HTTP error with {model}: {str(e)}"}
            except Exception as e:
                if not fallback_model and "google/gemini" in model:
                    self._failed_models.add(model)
                    fallback = OPENROUTER_MODELS["fallback"][0]
                    logger.warning(
                        f"⚠️ Unexpected error with {model}, falling back to {fallback}: {str(e)}"
                    )
                    return await self.complete(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        fallback_model=fallback,
                    )
                return {"error": f"Unexpected error with {model}: {str(e)}"}

        except Exception as e:
            logger.error(f"❌ Critical error: {str(e)}")
            return {"error": f"Critical error: {str(e)}"}
