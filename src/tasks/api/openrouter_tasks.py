"""OpenRouter API tasks."""

import json
import logging
from typing import Any, Callable, Dict, Literal, Optional, TypeVar

import httpx
from langfuse.decorators import langfuse_context, observe
from prefect import task
from pydantic import BaseModel, ValidationError

from src.models.api.openrouter import OpenRouterAPI, OpenRouterAPIError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def typed_observe(
    as_type: Optional[Literal["generation"]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Type-safe wrapper for observe decorator."""
    return observe(as_type=as_type)


class TokenUsage(BaseModel):
    unit: str
    input: int
    output: int
    total: int


@task(name="complete_openrouter_prompt")
@typed_observe(as_type="generation")
async def complete_openrouter_prompt(
    formatted_prompt: str,
    system_prompt: str,
    task_type: str,
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> Optional[Dict[str, Any]]:
    """Complete a prompt using OpenRouter API."""
    try:
        logger.info("\n" + "=" * 50 + " OpenRouter API Call " + "=" * 50)
        logger.info(f"Task Type: {task_type}")
        logger.info(f"Temperature: {temperature}")
        logger.info(f"Max Tokens: {max_tokens}")
        logger.info("\n System Prompt:")
        logger.info(system_prompt)
        logger.info("\n User Prompt:")
        logger.info(formatted_prompt)

        client = OpenRouterAPI()
        model = client._select_model(task_type)
        if not model:
            logger.error(f" No model found for task type: {task_type}")
            raise ValueError(f"No model found for task type: {task_type}") from None

        logger.info(f"\n Selected Model: {model}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_prompt},
        ]

        # Update the current observation with input data
        langfuse_context.update_current_observation(
            name=f"openrouter_{model}_completion",
            input=messages,
            model=model,
            metadata={
                "task_type": task_type,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )

        async with client:
            try:
                logger.info("\n Sending request to OpenRouter API...")
                logger.info(
                    f"Request data: {json.dumps({'messages': messages, 'temperature': temperature, 'max_tokens': max_tokens}, indent=2)}"
                )

                response = await client.complete(
                    messages=messages,
                    task_type=task_type,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                logger.info(" Received response from OpenRouter API")
                logger.info("\n OpenRouter API Response:")
                logger.info(f"Response: {json.dumps(response, indent=2, default=str)}")

                if not response or "choices" not in response:
                    error_msg = "Invalid response format - missing choices"
                    logger.error(f" {error_msg}")
                    langfuse_context.update_current_observation(
                        output=None, level="ERROR", metadata={"error": error_msg}
                    )
                    return None

                if not response["choices"]:
                    error_msg = "Empty choices in response"
                    logger.error(f" {error_msg}")
                    langfuse_context.update_current_observation(
                        output=None, level="ERROR", metadata={"error": error_msg}
                    )
                    return None

                if "message" not in response["choices"][0]:
                    error_msg = "Missing message in first choice"
                    logger.error(f" {error_msg}")
                    langfuse_context.update_current_observation(
                        output=None, level="ERROR", metadata={"error": error_msg}
                    )
                    return None

                if "content" not in response["choices"][0]["message"]:
                    error_msg = "Missing content in message"
                    logger.error(f" {error_msg}")
                    langfuse_context.update_current_observation(
                        output=None, level="ERROR", metadata={"error": error_msg}
                    )
                    return None

                content = response["choices"][0]["message"]["content"]
                logger.info("\n Response Content:")
                logger.info(content)

                # Update observation with response data
                if "usage" in response:
                    try:
                        usage = response["usage"]
                        # Try to create TokenUsage model - this will validate the data
                        usage_data = TokenUsage(
                            unit="TOKENS",
                            input=usage.get("prompt_tokens", 0),
                            output=usage.get("completion_tokens", 0),
                            total=usage.get("total_tokens", 0),
                        )
                        # If validation succeeds, update with usage data
                        langfuse_context.update_current_observation(
                            output=content,
                            usage=usage_data,
                            metadata={
                                "provider": response.get("provider", "unknown"),
                                "model_id": response.get("id", "unknown"),
                            },
                        )

                        logger.info("\n Usage Statistics:")
                        logger.info(f"Input Tokens: {usage_data.input}")
                        logger.info(f"Output Tokens: {usage_data.output}")
                        logger.info(f"Total Tokens: {usage_data.total}")
                        logger.info("=" * 100)
                    except ValidationError as e:
                        # Log the validation error and update with warning
                        error_msg = f"Error processing token usage data: {str(e)}"
                        logger.warning(error_msg)
                        langfuse_context.update_current_observation(
                            output=content,
                            metadata={
                                "warning": "Error processing token usage data",
                                "error": str(e),
                                "provider": response.get("provider", "unknown"),
                                "model_id": response.get("id", "unknown"),
                            },
                        )
                    except Exception as e:
                        # Log the error and update with warning
                        error_msg = f"Error processing token usage data: {str(e)}"
                        logger.warning(error_msg)
                        langfuse_context.update_current_observation(
                            output=content,
                            metadata={
                                "warning": "Error processing token usage data",
                                "error": str(e),
                                "provider": response.get("provider", "unknown"),
                                "model_id": response.get("id", "unknown"),
                            },
                        )
                else:
                    langfuse_context.update_current_observation(
                        output=content,
                        metadata={"warning": "No token usage information available"},
                    )

                return response

            except httpx.HTTPError as e:
                error_msg = f"HTTP error occurred: {str(e)}"
                logger.error(f" {error_msg}")
                langfuse_context.update_current_observation(
                    level="ERROR", metadata={"error": error_msg}
                )
                raise OpenRouterAPIError(error_msg) from e

    except Exception as e:
        logger.error(f" Error in complete_openrouter_prompt: {str(e)}")
        langfuse_context.update_current_observation(
            level="ERROR", metadata={"error": str(e)}
        )
        raise
