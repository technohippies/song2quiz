"""Test OpenRouter tasks."""

import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.models.api.openrouter import OpenRouterAPIError
from src.tasks.api.openrouter_tasks import complete_openrouter_prompt


@pytest.fixture()
def mock_openrouter_response():
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
def mock_settings():
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
def mock_openrouter():
    """Mock OpenRouter API responses"""
    with patch("src.tasks.api.openrouter_tasks.complete_openrouter_prompt") as mock:
        yield mock


@pytest.mark.asyncio()
async def test_complete_prompt_success(mock_openrouter):
    """Test successful prompt completion"""
    mock_openrouter.return_value = {"vocabulary": [{"term": "test"}]}
    # ... rest of test


@pytest.mark.asyncio()
async def test_complete_prompt_invalid_json():
    """Test that complete_prompt handles invalid JSON responses correctly."""
    with patch("httpx.AsyncClient.post") as mock_post:
        # Mock an invalid JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{\n  "prompt_test": "This is a test prompt."\n}',
                        "role": "assistant",
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = await complete_openrouter_prompt(
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
async def test_complete_prompt_error():
    """Test that complete_prompt handles API errors correctly."""
    with patch("src.models.api.openrouter.OpenRouterAPI.complete") as mock_complete:
        # Mock an error response
        mock_complete.side_effect = httpx.HTTPError("Internal Server Error")

        with pytest.raises(OpenRouterAPIError) as exc_info:
            await complete_openrouter_prompt(
                formatted_prompt="test prompt",
                system_prompt="You are a test assistant",
                task_type="default",
            )
        assert "HTTP error occurred" in str(exc_info.value)
        assert "Internal Server Error" in str(exc_info.value)


@pytest.mark.asyncio()
async def test_complete_prompt_integration():
    """Test complete_prompt with actual API call."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"API Key available: {'yes' if api_key else 'no'}")  # Debug print
    if not api_key:
        pytest.skip("Skipping integration test - no OPENROUTER_API_KEY available")

    # Use a prompt that should return vocabulary analysis
    prompt = "Analyze the vocabulary in: 'I got 99 problems'"

    try:
        result = await complete_openrouter_prompt(
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
