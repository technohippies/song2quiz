import logging
from typing import Any, Dict, Optional, cast

import httpx
from langfuse.decorators import langfuse_context, observe
from langfuse.model import ModelUsage
from prefect import task

from src.models.api.openrouter import OpenRouterAPI, OpenRouterAPIError

logger = logging.getLogger(__name__)

@task(name="complete_openrouter_prompt")
@observe(as_type="generation")
async def complete_openrouter_prompt(
    formatted_prompt: str,
    system_prompt: str,
    task_type: str,
    temperature: float = 0.7,
    max_tokens: int = 512
) -> Optional[Dict[str, Any]]:
    """Complete a prompt using OpenRouter API."""
    try:
        client = OpenRouterAPI()
        model = client._select_model(task_type)
        if not model:
            raise ValueError(f"No model found for task type: {task_type}") from None

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_prompt}
        ]

        async with client:
            try:
                response = await client.complete(
                    messages=messages,
                    task_type=task_type,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except httpx.HTTPError as e:
                raise OpenRouterAPIError(f"HTTP error occurred: {str(e)}")  # noqa: B904 from e

        logger.info(f"OpenRouter API Response: {response}")

        # Create ModelUsage as a dict since it's a TypedDict
        usage: ModelUsage = {
            "input": cast(int, response.get("usage", {}).get("prompt_tokens", 0)),
            "output": cast(int, response.get("usage", {}).get("completion_tokens", 0)),
            "total": cast(int, response.get("usage", {}).get("total_tokens", 0)),
            "unit": "TOKENS",
            "input_cost": None,
            "output_cost": None,
            "total_cost": None
        }

        # Update observation with usage and model info
        langfuse_context.update_current_observation(
            model=model,
            input=messages,
            output=response,
            usage=usage,
            metadata={
                "model": model,
                "task_type": task_type,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "finish_reason": response.get("choices", [{}])[0].get("finish_reason"),
                "prompt_version": "1",
                "prompt_template": "semantic_analysis",
                "response_format": "json"
            }
        )

        return response

    except Exception as e:
        langfuse_context.update_current_observation(
            level="ERROR",
            metadata={"error": str(e)}
        )
        raise OpenRouterAPIError(f"Error completing OpenRouter prompt: {str(e)}") from e
