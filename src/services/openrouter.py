"""Client for making requests to OpenRouter API with configurable models"""
import json
import logging
import re
from typing import Optional, Dict, Any, Union
from dotenv import load_dotenv
from src.constants.api import OPENROUTER_MODELS, DEFAULT_MODEL
from src.utils.settings import settings
from aiohttp import ClientSession, ClientTimeout
import asyncio
import time

load_dotenv()

class OpenRouterClient:
    """Client for making requests to OpenRouter API with configurable models"""
    
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    TIMEOUT = 180
    MAX_RETRIES = 5
    INITIAL_RETRY_DELAY = 10
    MAX_RETRY_DELAY = 120
    
    def __init__(self, task_type: Optional[str] = None):
        """
        Initialize client with optional task type to determine model
        
        Args:
            task_type: Type of task (e.g., 'enhance_lyrics', 'translation')
                      If None, uses DEFAULT_MODEL
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up logging with a specific format
        self.logger.setLevel(logging.DEBUG)
        
        # Add a console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            
        self.api_key = settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in settings")
            
        # Get model from environment variable if set, otherwise use constants
        self.model = OPENROUTER_MODELS.get('default', DEFAULT_MODEL) if task_type is None else OPENROUTER_MODELS.get(task_type, OPENROUTER_MODELS['default'])
        
        self.logger.debug(f"Task type: {task_type}, Selected model: {self.model}")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/technohippies/",
            "X-Title": "song2quiz"
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 3.0
        
        self.logger.debug("OpenRouterClient initialized")

    async def _wait_for_rate_limit(self):
        """Wait if needed to respect rate limits"""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_request_interval:
            delay = self.min_request_interval - time_since_last
            self.logger.debug(f"Rate limiting: waiting {delay:.2f} seconds")
            await asyncio.sleep(delay)
        self.last_request_time = time.time()

    def clean_response(self, content: str) -> Union[str, Dict[str, Any]]:
        """Clean the response content from the API"""
        if not content:
            return content
        
        # Enhanced logging
        self.logger.debug("========== CLEAN RESPONSE START ==========")
        self.logger.debug(f"Raw content type: {type(content)}")
        self.logger.debug(f"Raw content: {repr(content)}")
        
        def clean_json_str(json_str: str) -> str:
            """Helper function to clean JSON string"""
            # Normalize quotes - replace escaped single quotes with regular single quotes
            json_str = json_str.replace("\\'", "'")
            
            # Handle nested quotes in usage_notes and other fields
            # Replace any remaining escaped double quotes with single quotes
            json_str = json_str.replace('\\"', "'")
            
            # Remove any trailing commas before closing brackets
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # Fix any remaining unescaped quotes inside strings
            def fix_nested_quotes(match):
                # Replace unescaped double quotes in the string with single quotes
                string_content = match.group(1)
                return '"' + string_content.replace('"', "'") + '"'
                
            json_str = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', fix_nested_quotes, json_str)
            
            return json_str

        # First try to extract JSON from markdown code blocks
        json_block_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_block_match:
            try:
                json_str = clean_json_str(json_block_match.group(1).strip())
                self.logger.debug(f"Found JSON block: {json_str}")
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON from code block: {str(e)}")
        
        # If no JSON block or parsing failed, try to find any JSON structure
        json_match = re.search(r'(\{[\s\S]*\})', content)
        if json_match:
            try:
                json_str = clean_json_str(json_match.group(0))
                self.logger.debug(f"Found JSON structure: {json_str}")
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON structure: {str(e)}")
                # Try one more time with more aggressive cleaning
                try:
                    # Remove any non-JSON characters
                    json_str = re.sub(r'[^\[\]{}",:\s\w\-\'.]', '', json_str)
                    # Normalize all quotes to double quotes
                    json_str = json_str.replace("'", '"')
                    # Fix double-quoted strings
                    json_str = re.sub(r'""([^"]*?)""', r'"\1"', json_str)
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON even after aggressive cleaning: {str(e)}")
        
        self.logger.debug("========== CLEAN RESPONSE END ==========")
        self.logger.info(f"Cleaned content: {repr(content)}")
        
        # If we couldn't parse as JSON, try to extract just the vocabulary array
        vocab_match = re.search(r'"vocabulary":\s*(\[.*?\])', content, re.DOTALL)
        if vocab_match:
            try:
                vocab_str = clean_json_str(vocab_match.group(1))
                vocab_list = json.loads(vocab_str)
                return {"vocabulary": vocab_list}
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse vocabulary array")
        
        return content

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> Union[str, Dict[str, Any]]:
        """Make request to OpenRouter API with retry logic and fallback for blocklist events"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Try with primary model first
        data = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 2000,
            "response_format": {"type": "json_object"}
        }
        
        retries = 0
        current_delay = self.INITIAL_RETRY_DELAY
        
        while retries <= self.MAX_RETRIES:
            try:
                await self._wait_for_rate_limit()
                
                timeout = ClientTimeout(total=self.TIMEOUT)
                async with ClientSession(timeout=timeout) as session:
                    async with session.post(
                        self.BASE_URL,
                        headers=self.headers,
                        json=data,
                        raise_for_status=True
                    ) as response:
                        response_data = await response.json()
                        self.logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
                        
                        # Check for blocklist event
                        if 'choices' in response_data and response_data['choices']:
                            choice = response_data['choices'][0]
                            if choice.get('finish_reason') == 'BLOCKLIST':
                                self.logger.warning("=== BLOCKLIST EVENT DETECTED ===")
                                self.logger.warning(f"Prompt that triggered blocklist: {prompt}")
                                content = choice.get('message', {}).get('content', '')
                                self.logger.warning(f"Truncated response: {content}")
                                self.logger.warning("================================")
                                
                                # Try with fallback model
                                self.logger.info(f"Retrying with fallback model: {OPENROUTER_MODELS['fallback']}")
                                data["model"] = OPENROUTER_MODELS['fallback']
                                
                                # Make request with fallback model
                                async with session.post(
                                    self.BASE_URL,
                                    headers=self.headers,
                                    json=data,
                                    raise_for_status=True
                                ) as fallback_response:
                                    fallback_data = await fallback_response.json()
                                    self.logger.info(f"Fallback model response: {json.dumps(fallback_data, indent=2)}")
                                    
                                    if 'choices' in fallback_data and fallback_data['choices']:
                                        content = fallback_data['choices'][0].get('message', {}).get('content', '')
                                        self.logger.info(f"Fallback raw content: {repr(content)}")
                                        return self.clean_response(content)
                                    
                                    return "{}"
                            
                            # Process normal response (no blocklist)
                            content = choice.get('message', {}).get('content', '')
                            self.logger.info(f"Raw content: {repr(content)}")
                            return self.clean_response(content)
                        
                        return "{}"
                        
            except Exception as e:
                self.logger.error(f"Error during API request: {str(e)}")
                if retries == self.MAX_RETRIES:
                    raise
                
                retries += 1
                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * 2, self.MAX_RETRY_DELAY)
        
        return "{}"

    def _find_complete_json(self, content: str) -> str:
        """Find the last complete JSON object/array in a potentially truncated string"""
        # Remove markdown
        content = re.sub(r'```(?:json)?\n?(.*?)```', r'\1', content, flags=re.DOTALL)
        
        # Find all potential JSON objects/arrays
        json_matches = list(re.finditer(r'(\{[\s\S]*?\}|\[[\s\S]*?\])', content))
        
        if not json_matches:
            return content
            
        # Get the last complete match
        last_match = json_matches[-1]
        json_str = last_match.group(0)
        
        # Validate JSON structure
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            # If the last match is invalid, try the previous ones
            for match in reversed(json_matches[:-1]):
                try:
                    json_str = match.group(0)
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    continue
                    
        return content