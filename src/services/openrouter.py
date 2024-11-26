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
        
        # Strip whitespace and remove markdown
        content = content.strip()
        content = re.sub(r'```(?:json)?\n?(.*?)```', r'\1', content, flags=re.DOTALL)
        
        # Find JSON structure and ensure it's complete
        json_match = re.search(r'(\{[\s\S]*?\}|\[[\s\S]*?\])', content)
        if json_match:
            json_str = json_match.group(0)
            
            # Count braces to ensure complete JSON
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            
            if open_braces != close_braces or open_brackets != close_brackets:
                self.logger.warning("Incomplete JSON structure detected")
                self.logger.warning(f"Open braces: {open_braces}, Close braces: {close_braces}")
                self.logger.warning(f"Open brackets: {open_brackets}, Close brackets: {close_brackets}")
                
                # Try to find a valid complete subset of the JSON
                stack = []
                valid_json = ""
                for i, char in enumerate(json_str):
                    if char in '{[':
                        stack.append(char)
                        valid_json += char
                    elif char in '}]':
                        if not stack:  # Ignore closing without opening
                            continue
                        if (char == '}' and stack[-1] == '{') or (char == ']' and stack[-1] == '['):
                            stack.pop()
                            valid_json += char
                            if not stack:  # We found a complete valid JSON structure
                                break
                    else:
                        valid_json += char
                
                if not stack:  # We found a complete valid JSON
                    json_str = valid_json
                else:  # Add missing closing braces/brackets
                    while stack:
                        char = stack.pop()
                        if char == '{':
                            json_str += '}'
                        elif char == '[':
                            json_str += ']'
            
            try:
                # Basic cleanup
                json_str = re.sub(r'\\([^"\\])', r'\1', json_str)  # Remove invalid escapes
                json_str = re.sub(r'(?<!\\)"([^"]*?)(?<!\\)"', r'"\1"', json_str)  # Fix quotes
                json_str = re.sub(r'(\s*)(\w+)(\s*):', r'\1"\2"\3:', json_str)  # Quote property names
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # Remove trailing commas
                
                self.logger.debug(f"Cleaned JSON string: {repr(json_str)}")
                parsed = json.loads(json_str)
                self.logger.debug("Successfully parsed JSON structure")
                return parsed
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing failed: {str(e)}")
                self.logger.error(f"Failed JSON: {repr(json_str)}")
                
                # Try one more time with aggressive cleaning
                try:
                    cleaned = json_str.replace('\t', '    ')  # Replace tabs with spaces
                    cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)  # Remove trailing commas
                    cleaned = re.sub(r',(\s*$)', '', cleaned)  # Remove trailing commas at end of lines
                    cleaned = re.sub(r'(?m),(\s*$)', '', cleaned)  # Remove trailing commas at end of lines (multiline)
                    
                    self.logger.debug(f"Aggressively cleaned JSON: {repr(cleaned)}")
                    parsed = json.loads(cleaned)
                    self.logger.debug("Successfully parsed JSON after aggressive cleaning")
                    return parsed
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse JSON even after aggressive cleaning")
                    
        self.logger.debug("========== CLEAN RESPONSE END ==========")
        self.logger.info(f"Cleaned content: {repr(content)}")
        
        # If we couldn't parse JSON, return the cleaned string
        return content

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> Union[str, Dict[str, Any]]:
        """Make request to OpenRouter API with retry logic"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 2000,  # Reduced to avoid truncation
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
                        
                        if 'choices' in response_data and response_data['choices']:
                            content = response_data['choices'][0].get('message', {}).get('content', '')
                            self.logger.info(f"Raw content: {repr(content)}")
                            
                            # Try to parse as JSON first
                            try:
                                if content.startswith('```json'):
                                    content = content[7:]  # Remove ```json
                                if content.endswith('```'):
                                    content = content[:-3]  # Remove ```
                                content = content.strip()
                                return json.loads(content)
                            except json.JSONDecodeError:
                                # If JSON parsing fails, try cleaning
                                cleaned = self.clean_response(content)
                                if isinstance(cleaned, dict):
                                    return cleaned
                                
                                # If all else fails, return the raw content
                                return content if content else "{}"
                        
                        return "{}"  # Return empty JSON object if no content
                        
            except Exception as e:
                self.logger.error(f"Error during API request: {str(e)}")
                if retries == self.MAX_RETRIES:
                    raise
                
                retries += 1
                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * 2, self.MAX_RETRY_DELAY)
        
        return "{}"  # Return empty JSON object after all retries fail

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