from prefect import task
from src.services.openrouter import OpenRouterClient, OpenRouterAPIError
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

@task(name="complete_openrouter_prompt")
async def complete_openrouter_prompt(
    formatted_prompt: str,
    task_type: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """Complete a prompt using OpenRouter API."""
    try:
        client = OpenRouterClient(task_type=task_type)
        return await client.complete(
            prompt=formatted_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except OpenRouterAPIError as e:
        logger.error(f"OpenRouter API error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in OpenRouter task: {str(e)}")
        return {"error": str(e)} 