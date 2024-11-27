from prefect import task
from src.services.openrouter import OpenRouterClient
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

# Create a single client instance
openrouter_client = OpenRouterClient()

@task(name="complete_openrouter_prompt",
      retries=3,
      retry_delay_seconds=2,
      tags=["api"])
async def complete_openrouter_prompt(
    formatted_prompt: str,
    task_type: str,
    system_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 512
) -> Dict[str, Any]:
    """Complete a prompt using OpenRouter API."""
    try:
        response = await openrouter_client.complete(
            prompt=formatted_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response and isinstance(response, dict) and "choices" in response:
            content = response["choices"][0]["message"]["content"]
            try:
                return json.loads(content)  # Return parsed JSON directly
            except json.JSONDecodeError:
                return response  # Return raw response if not JSON
        return response
    except Exception as e:
        raise RuntimeError(f"Failed to complete prompt: {str(e)}") 