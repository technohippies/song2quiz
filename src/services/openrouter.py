"""Client for making requests to OpenRouter API with configurable models"""
import json
import logging
import time
from typing import Optional, Dict, Any
import httpx
from src.utils.settings import settings
from src.utils.cleaning.text import extract_and_clean_json
from src.constants.api import OPENROUTER_MODELS

logger = logging.getLogger(__name__)

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
            "Content-Type": "application/json"
        }
        
        self.task_type = task_type or "default"
        self._failed_models = set()
        logger.debug(f"Task type: {self.task_type}")
        
    def _select_model(self, fallback_model: Optional[str] = None) -> str:
        """Select appropriate model based on task type and failure history."""
        if fallback_model:
            logger.info(f"Using specified fallback model: {fallback_model}")
            return fallback_model
        
        task_models = OPENROUTER_MODELS.get(self.task_type, OPENROUTER_MODELS["default"])
        if not task_models:
            raise OpenRouterAPIError(f"No models configured for task type: {self.task_type}")
        
        # If primary model has failed before, use fallback immediately
        primary_model = task_models[0]
        if primary_model in self._failed_models:
            fallback = OPENROUTER_MODELS["fallback"][0]
            logger.info(f"Using fallback model {fallback} (primary model {primary_model} failed previously)")
            return fallback
            
        logger.info(f"Using model: {primary_model}")
        return primary_model
        
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        fallback_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete a chat conversation."""
        try:
            model = self._select_model(fallback_model)
            
            json_reminder = """
            IMPORTANT: You must respond with a valid, complete JSON object following these rules:
            1. Include EXACTLY ONE term in the response
            2. Use this structure:
            {
              "vocabulary": [
                {
                  "term": "example",
                  "vocabulary_type": "type",
                  "definition": "definition",
                  "usage_notes": "notes",
                  "variants": ["variant1", "variant2"]
                }
              ]
            }
            3. Do not include any text outside the JSON.
            4. Keep each field under 100 characters.
            5. Include all offensive or explicit terms as-is without censoring.
            """
            
            enhanced_system_prompt = (system_prompt or "") + json_reminder
            
            request_data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens or 256,
                "response_format": {"type": "json_object"}
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
                    json=request_data
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
                    
                    if not isinstance(result, dict) or "vocabulary" not in result:
                        raise json.JSONDecodeError("Missing vocabulary key", content, 0)
                    if not isinstance(result["vocabulary"], list):
                        raise json.JSONDecodeError("vocabulary must be an array", content, 0)
                    if len(result["vocabulary"]) != 1:
                        logger.warning(f"⚠️ Expected 1 term but got {len(result['vocabulary'])} terms")
                    return result
                except json.JSONDecodeError as e:
                    if not fallback_model and "google/gemini" in model:
                        self._failed_models.add(model)
                        fallback = OPENROUTER_MODELS["fallback"][0]
                        logger.warning(f"🔄 JSON parsing failed with {model}, falling back to {fallback}")
                        return await self.complete(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            fallback_model=fallback
                        )
                    logger.error(f"❌ JSON parsing failed with {model}: {str(e)}")
                    return {"error": f"Failed to parse response as JSON: {str(e)}"}
                    
            except httpx.HTTPError as e:
                if "blocklist" in str(e).lower() and not fallback_model:
                    self._failed_models.add(model)
                    fallback = OPENROUTER_MODELS["fallback"][0]
                    logger.warning(f"⚠️ Model {model} blocked, falling back to {fallback}")
                    return await self.complete(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        fallback_model=fallback
                    )
                return {"error": f"HTTP error with {model}: {str(e)}"}
            except Exception as e:
                if not fallback_model and "google/gemini" in model:
                    self._failed_models.add(model)
                    fallback = OPENROUTER_MODELS["fallback"][0]
                    logger.warning(f"⚠️ Unexpected error with {model}, falling back to {fallback}: {str(e)}")
                    return await self.complete(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        fallback_model=fallback
                    )
                return {"error": f"Unexpected error with {model}: {str(e)}"}
                
        except Exception as e:
            logger.error(f"❌ Critical error: {str(e)}")
            return {"error": f"Critical error: {str(e)}"}