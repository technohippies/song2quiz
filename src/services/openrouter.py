"""Client for making requests to OpenRouter API with configurable models"""
import json
import logging
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
        self.client = httpx.Client(timeout=30.0)  # Reduced timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/sage-ai/sage",
            "X-Title": "Sage AI",
            "Content-Type": "application/json"
        }
        
        self.task_type = task_type or "default"
        logger.debug(f"Task type: {self.task_type}")
    
    def _select_model(self, fallback_model: Optional[str] = None) -> str:
        """Select appropriate model based on task type."""
        logger.debug(f"Task type: {self.task_type}, Selected model: {fallback_model}")
        
        if fallback_model:
            return fallback_model
        
        task_models = OPENROUTER_MODELS.get(self.task_type, OPENROUTER_MODELS["default"])
        if not task_models:
            raise OpenRouterAPIError(f"No models configured for task type: {self.task_type}")
            
        selected_model = task_models[0]
        logger.debug(f"Selected model: {selected_model}")
        return selected_model
    
    def _clean_response_content(self, content: str) -> str:
        """Clean response content and extract JSON."""
        if not content:
            return ""
            
        # Remove any markdown or whitespace
        content = content.strip("` \n")
        
        try:
            # Use text cleaning utilities to extract and clean JSON
            result = extract_and_clean_json(content)
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False)
            elif isinstance(result, str):
                # If extract_and_clean_json returns a string, it means it couldn't parse the JSON
                logger.warning("Could not parse response as JSON")
                return result
            return str(result)
        except Exception as e:
            logger.error(f"Error cleaning response content: {str(e)}")
            raise OpenRouterAPIError(f"Failed to clean response: {str(e)}") from e
    
    async def chat_completion(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        fallback_model: Optional[str] = None
    ) -> str:
        """Make a chat completion request."""
        try:
            model = self._select_model(fallback_model)
            
            data = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens:
                data["max_tokens"] = max_tokens
                
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data
            )
            
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}"
                if not fallback_model and "google/gemini" in model:
                    # Try fallback to Nemotron if Gemini fails
                    logger.warning(f"{error_msg}, falling back to Nemotron")
                    return await self.chat_completion(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        fallback_model=OPENROUTER_MODELS["fallback"][0]
                    )
                raise OpenRouterAPIError(error_msg)
                
            try:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content.strip()
                
            except (json.JSONDecodeError, KeyError) as e:
                if not fallback_model and "google/gemini" in model:
                    # Try fallback to Nemotron for parsing errors
                    logger.warning(f"Failed to parse response, falling back to Nemotron: {str(e)}")
                    return await self.chat_completion(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        fallback_model=OPENROUTER_MODELS["fallback"][0]
                    )
                raise OpenRouterAPIError(f"Failed to parse API response: {str(e)}")
                
        except Exception as e:
            if not fallback_model and "google/gemini" in model:
                # Try fallback to Nemotron for any other errors
                logger.warning(f"Request failed, falling back to Nemotron: {str(e)}")
                return await self.chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    fallback_model=OPENROUTER_MODELS["fallback"][0]
                )
            raise OpenRouterAPIError(f"Request failed: {str(e)}")
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        fallback_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete a chat conversation."""
        model = self._select_model(fallback_model)
        
        # Log the request
        request_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt} if system_prompt else None,
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens or 1024,
            "response_format": {"type": "json_object"}
        }
        request_data["messages"] = [m for m in request_data["messages"] if m]  # Remove None
        logger.info(f"Request to OpenRouter:\n{json.dumps(request_data, indent=2)}")
        
        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=request_data
            )
            response.raise_for_status()
            
            response_data = response.json()
            logger.info(f"Full OpenRouter Response:\n{json.dumps(response_data, indent=2)}")
            
            content = response_data["choices"][0]["message"]["content"]
            logger.info(f"Raw content:\n{content}")
            
            # Clean and parse the response
            cleaned_content = self._clean_response_content(content)
            logger.info(f"Cleaned content:\n{cleaned_content}")
            
            try:
                return json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON Parse Error: {str(e)}")
                logger.error(f"Failed content was:\n{cleaned_content}")
                return {"error": f"Failed to parse response as JSON: {str(e)}"}
            
        except httpx.HTTPError as e:
            if "blocklist" in str(e).lower() and not fallback_model:
                fallback = "nvidia/llama-3.1-nemotron-70b-instruct"
                logger.warning(f"Model {model} blocked, trying fallback model: {fallback}")
                return await self.complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    fallback_model=fallback
                )
            raise OpenRouterAPIError(f"HTTP error: {str(e)}") from e
        except Exception as e:
            raise OpenRouterAPIError(f"Unexpected error: {str(e)}") from e