from prefect import task
from src.services.openrouter import OpenRouterClient
from typing import Optional, Union, Dict, Any

@task(
    name="complete_openrouter_prompt",
    retries=3,
    retry_delay_seconds=60,
    tags=["api", "openrouter"]
)
async def complete_prompt(
    prompt: str,
    system_prompt: Optional[str] = None,
    task_type: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> Union[str, Dict[str, Any]]:
    """Prefect task wrapper for OpenRouter API calls"""
    client = OpenRouterClient(task_type=task_type)
    return await client.complete(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens
    ) 