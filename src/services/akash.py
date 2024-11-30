"""Service for interacting with the Akash Chat API."""

import os
from typing import Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from prefect import get_run_logger

# Constants
AKASH_API_URL = "https://chatapi.akash.network/api/v1"
AKASH_MODEL = "nvidia-Llama-3-1-Nemotron-70B-Instruct-HF"


async def complete_akash_prompt(
    formatted_prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
) -> Optional[Dict]:
    """Complete a prompt using the Akash Chat API.

    Args:
        formatted_prompt: The formatted prompt to send
        system_prompt: Optional system prompt
        temperature: Temperature for response generation

    Returns:
        Response from the API or None if failed
    """
    log = get_run_logger()

    try:
        client = AsyncOpenAI(api_key=os.getenv("AKASH_API_KEY"), base_url=AKASH_API_URL)

        messages: List[ChatCompletionMessageParam] = []
        if system_prompt:
            messages.append(
                ChatCompletionSystemMessageParam(role="system", content=system_prompt)
            )

        messages.append(
            ChatCompletionUserMessageParam(role="user", content=formatted_prompt)
        )

        response = await client.chat.completions.create(
            model=AKASH_MODEL, messages=messages, temperature=temperature
        )

        # Convert to dict format matching OpenRouter
        return {
            "choices": [
                {
                    "message": {
                        "content": response.choices[0].message.content,
                        "role": "assistant",
                    }
                }
            ]
        }

    except Exception as e:
        log.error(f"Error calling Akash API: {str(e)}")
        return None
