"""Models for OpenRouter API requests and responses."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

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