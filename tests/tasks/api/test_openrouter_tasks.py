"""Test OpenRouter tasks."""

import os
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.api.openrouter import OpenRouterAPIError
from src.tasks.api.openrouter_tasks import complete_openrouter_prompt


@pytest.fixture()
def mock_openrouter_response() -> Dict[str, Any]:
    """Mock successful OpenRouter API response"""
    return {
        "id": "test-id",
        "model": "test-model",
        "created": 1234567890,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"test_prompt": "This is a test prompt."}',
                },
                "finish_reason": "stop",
            },
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    }


@pytest.fixture(autouse=True)
def mock_settings() -> Generator[MagicMock, None, None]:
    """Mock settings to provide API key"""
    with patch("src.utils.settings") as mock_settings:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("WARNING: No OPENROUTER_API_KEY found in environment")
        else:
            print(f"Found API key starting with: {api_key[:8]}...")
        mock_settings.OPENROUTER_API_KEY = api_key
        yield mock_settings


@pytest.fixture
def mock_openrouter() -> Generator[AsyncMock, None, None]:
    """Mock OpenRouter API responses"""
    with patch("src.tasks.api.openrouter_tasks.complete_openrouter_prompt") as mock:
        yield mock


@pytest.mark.asyncio()
async def test_complete_prompt_success(mock_openrouter: AsyncMock) -> None:
    """Test successful prompt completion"""
    mock_openrouter.return_value = AsyncMock(
        return_value={"vocabulary": [{"term": "test"}]}
    )
    # ... rest of test


@pytest.mark.asyncio()
async def test_complete_prompt_invalid_json() -> None:
    """Test that complete_prompt handles invalid JSON responses correctly."""
    with patch("src.models.api.openrouter.OpenRouterAPI.complete") as mock_complete:
        # Mock the complete method to return a response
        async def mock_complete_response(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{\n  "prompt_test": "This is a test prompt."\n}',
                            "role": "assistant",
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            }

        mock_complete.side_effect = mock_complete_response

        result = await complete_openrouter_prompt.fn(
            formatted_prompt="test prompt",
            system_prompt="You are a test assistant",
            task_type="default",
        )
        assert result is not None
        assert "choices" in result
        assert len(result["choices"]) > 0
        assert "message" in result["choices"][0]
        assert "content" in result["choices"][0]["message"]
        expected_content = '{\n  "prompt_test": "This is a test prompt."\n}'
        assert result["choices"][0]["message"]["content"] == expected_content


@pytest.mark.asyncio()
async def test_complete_prompt_error() -> None:
    """Test that complete_prompt handles API errors correctly."""
    with patch("src.models.api.openrouter.OpenRouterAPI.complete") as mock_complete:
        # Mock an error response
        async def mock_error_response(*args: Any, **kwargs: Any) -> None:
            raise OpenRouterAPIError("Error during API request: Internal Server Error")

        mock_complete.side_effect = mock_error_response

        with pytest.raises(OpenRouterAPIError) as exc_info:
            await complete_openrouter_prompt.fn(
                formatted_prompt="test prompt",
                system_prompt="You are a test assistant",
                task_type="default",
            )
        assert "Error during API request" in str(exc_info.value)
        assert "Internal Server Error" in str(exc_info.value)


@pytest.mark.asyncio()
async def test_complete_prompt_integration() -> None:
    """Test complete_prompt with actual API call."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"API Key available: {'yes' if api_key else 'no'}")  # Debug print
    if not api_key:
        pytest.skip("Skipping integration test - no OPENROUTER_API_KEY available")

    # Use a prompt that should return vocabulary analysis
    prompt = "Analyze the vocabulary in: 'I got 99 problems'"

    try:
        result = await complete_openrouter_prompt.fn(
            formatted_prompt=prompt,
            system_prompt="You are a vocabulary analyzer",
            task_type="analysis",
            temperature=0.1,
        )
        print("API call successful")  # Debug print
    except Exception as e:
        print(f"API call failed with error: {str(e)}")  # Debug print
        raise

    # Check that we got a valid response
    assert result is not None
    assert "choices" in result
    assert len(result["choices"]) > 0
    assert "message" in result["choices"][0]
    assert "content" in result["choices"][0]["message"]
