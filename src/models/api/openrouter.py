"""Models for OpenRouter API requests and responses."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import json
import asyncio
from aiohttp import ClientSession, ClientTimeout
from logging import Logger

class Role(Enum):
    """Roles in a chat conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class Message:
    """A single message in the conversation."""
    role: Role
    content: str

@dataclass
class ChatCompletionRequest:
    """Request structure for OpenRouter chat completion."""
    messages: List[Message]
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenRouter API format."""
        return {
            "messages": [
                {"role": msg.role.value, "content": msg.content}
                for msg in self.messages
            ],
            "model": self.model,
            "temperature": self.temperature,
            **({"max_tokens": self.max_tokens} if self.max_tokens else {}),
            "stream": self.stream
        }

@dataclass
class CompletionChoice:
    """A single completion choice from the response."""
    index: int
    message: Message
    finish_reason: Optional[str] = None

@dataclass
class Usage:
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass
class ChatCompletionResponse:
    """Response structure from OpenRouter chat completion."""
    id: str
    model: str
    created: int  # Unix timestamp
    choices: List[CompletionChoice]
    usage: Usage

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatCompletionResponse':
        """Create from OpenRouter API response."""
        choices = [
            CompletionChoice(
                index=c["index"],
                message=Message(
                    role=Role(c["message"]["role"]),
                    content=c["message"]["content"]
                ),
                finish_reason=c.get("finish_reason")
            )
            for c in data["choices"]
        ]
        
        usage = Usage(
            prompt_tokens=data["usage"]["prompt_tokens"],
            completion_tokens=data["usage"]["completion_tokens"],
            total_tokens=data["usage"]["total_tokens"]
        )
        
        return cls(
            id=data["id"],
            model=data["model"],
            created=data["created"],
            choices=choices,
            usage=usage
        )

class OpenRouterAPI:
    def __init__(self, model: str, headers: Dict[str, str], logger: Logger):
        self.model = model
        self.headers = headers
        self.logger = logger
        self.BASE_URL = "https://api.openrouter.com/v1/chat/completions"
        self.INITIAL_RETRY_DELAY = 1
        self.MAX_RETRIES = 3
        self.MAX_RETRY_DELAY = 30
        self.TIMEOUT = 30

    async def _wait_for_rate_limit(self):
        # implement rate limit logic here
        pass

    def clean_response(self, content: str) -> Union[str, Dict[str, Any]]:
        # implement response cleaning logic here
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
                                self.logger.warning(f"Truncated response: {choice.get('message', {}).get('content', '')}")
                                self.logger.warning("================================")
                                
                                # Try with fallback model
                                self.logger.info(f"Retrying with fallback model: {OPENROUTER_MODELS['fallback']}")
                                fallback_data = {
                                    "model": OPENROUTER_MODELS['fallback'],
                                    "messages": messages,
                                    "temperature": temperature,
                                    "max_tokens": max_tokens or 2000,
                                    "response_format": {"type": "json_object"}
                                }
                                
                                # Make request with fallback model
                                async with session.post(
                                    self.BASE_URL,
                                    headers=self.headers,
                                    json=fallback_data,
                                    raise_for_status=True
                                ) as fallback_response:
                                    fallback_data = await fallback_response.json()
                                    self.logger.info(f"Fallback model response: {json.dumps(fallback_data, indent=2)}")
                                    
                                    if 'choices' in fallback_data and fallback_data['choices']:
                                        fallback_content = fallback_data['choices'][0].get('message', {}).get('content', '')
                                        self.logger.info(f"Fallback raw content: {repr(fallback_content)}")
                                        
                                        # Process fallback response
                                        try:
                                            if fallback_content.startswith('```json'):
                                                fallback_content = fallback_content[7:]
                                            if fallback_content.endswith('```'):
                                                fallback_content = fallback_content[:-3]
                                            fallback_content = fallback_content.strip()
                                            return json.loads(fallback_content)
                                        except json.JSONDecodeError:
                                            cleaned = self.clean_response(fallback_content)
                                            if isinstance(cleaned, dict):
                                                return cleaned
                                            return fallback_content if fallback_content else "{}"
                                    return "{}"
                            
                            # Process normal response (no blocklist)
                            content = choice.get('message', {}).get('content', '')
                            self.logger.info(f"Raw content: {repr(content)}")
                            
                            try:
                                if content.startswith('```json'):
                                    content = content[7:]
                                if content.endswith('```'):
                                    content = content[:-3]
                                content = content.strip()
                                return json.loads(content)
                            except json.JSONDecodeError:
                                cleaned = self.clean_response(content)
                                if isinstance(cleaned, dict):
                                    return cleaned
                                return content if content else "{}"
                        
                        return "{}"
                        
            except Exception as e:
                self.logger.error(f"Error during API request: {str(e)}")
                if retries == self.MAX_RETRIES:
                    raise
                
                retries += 1
                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * 2, self.MAX_RETRY_DELAY)
        
        return "{}"