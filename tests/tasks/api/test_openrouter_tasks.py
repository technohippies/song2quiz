"""Tests for OpenRouter API tasks and Langfuse integration."""

from unittest.mock import AsyncMock, patch

import pytest

from src.tasks.api.openrouter_tasks import TokenUsage, complete_openrouter_prompt


@pytest.mark.asyncio
async def test_openrouter_token_tracking_mock() -> None:
    """Test that token counts are correctly sent to Langfuse using mocks."""
    # Mock response from OpenRouter
    mock_response = {
        "id": "test-id",
        "model": "test-model",
        "choices": [{"message": {"content": "test response", "role": "assistant"}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }

    # Mock the OpenRouter API call and Langfuse context
    with (
        patch(
            "src.models.api.openrouter.OpenRouterAPI.complete", new_callable=AsyncMock
        ) as mock_complete,
        patch(
            "langfuse.decorators.langfuse_context.update_current_observation"
        ) as mock_langfuse,
    ):
        mock_complete.return_value = mock_response

        # Make the API call using the underlying function
        result = await complete_openrouter_prompt.fn(
            formatted_prompt="test prompt",
            system_prompt="test system prompt",
            task_type="default",
        )

        # Verify the response
        assert result is not None
        assert isinstance(result, dict)
        assert result["usage"]["prompt_tokens"] == 100
        assert result["usage"]["completion_tokens"] == 50

        # Verify the mock was called correctly
        mock_complete.assert_called_once()

        # Verify Langfuse was called with correct token usage
        mock_langfuse.assert_called()
        usage_arg = mock_langfuse.call_args.kwargs["usage"]
        assert isinstance(usage_arg, TokenUsage)
        assert usage_arg.unit == "TOKENS"
        assert usage_arg.input == 100
        assert usage_arg.output == 50
        assert usage_arg.total == 150


@pytest.mark.asyncio
async def test_openrouter_token_tracking_missing_usage() -> None:
    """Test handling of missing token usage data."""
    # Mock response without usage data
    mock_response = {
        "id": "test-id",
        "model": "test-model",
        "choices": [{"message": {"content": "test response", "role": "assistant"}}],
    }

    # Mock the OpenRouter API call and Langfuse context
    with (
        patch(
            "src.models.api.openrouter.OpenRouterAPI.complete", new_callable=AsyncMock
        ) as mock_complete,
        patch(
            "langfuse.decorators.langfuse_context.update_current_observation"
        ) as mock_langfuse,
    ):
        mock_complete.return_value = mock_response

        # Make the API call using the underlying function
        result = await complete_openrouter_prompt.fn(
            formatted_prompt="test prompt",
            system_prompt="test system prompt",
            task_type="default",
        )

        # Verify the response
        assert result is not None
        assert isinstance(result, dict)
        assert "usage" not in result

        # Verify Langfuse was called with warning metadata
        mock_langfuse.assert_called()
        metadata_arg = mock_langfuse.call_args.kwargs["metadata"]
        assert "warning" in metadata_arg
        assert "No token usage information available" in metadata_arg["warning"]


@pytest.mark.asyncio
async def test_openrouter_token_tracking_malformed_usage() -> None:
    """Test handling of malformed token usage data."""
    # Create a mock response with malformed token usage data that will trigger Pydantic validation error
    mock_response = {
        "choices": [{"message": {"content": "test response"}}],
        "usage": {
            "prompt_tokens": "invalid",  # String instead of int
            "completion_tokens": None,  # None instead of int
            "total_tokens": "bad",  # String instead of int
        },
    }

    # Mock the OpenRouter API call and Langfuse context
    with (
        patch(
            "src.models.api.openrouter.OpenRouterAPI.complete", new_callable=AsyncMock
        ) as mock_complete,
        patch(
            "langfuse.decorators.langfuse_context.update_current_observation"
        ) as mock_langfuse,
    ):
        mock_complete.return_value = mock_response

        # Make the API call
        result = await complete_openrouter_prompt.fn(
            formatted_prompt="test prompt",
            system_prompt="test system prompt",
            task_type="default",
        )

        # Verify we got a response despite malformed usage data
        assert result is not None
        assert isinstance(result, dict)

        # Get all calls to Langfuse for debugging
        all_calls = mock_langfuse.call_args_list
        print("\nAll Langfuse calls:")
        for i, call in enumerate(all_calls):
            print(f"\nCall {i}:")
            print(f"Kwargs metadata: {call.kwargs.get('metadata', {})}")

        # Find calls with our error message
        error_calls = [
            call
            for call in all_calls
            if call.kwargs.get("metadata", {}).get("warning")
            == "Error processing token usage data"
        ]

        # Verify we found the error call
        assert len(error_calls) > 0, "No Langfuse calls found with token usage error"

        # Check the error metadata
        error_call = error_calls[0]
        metadata = error_call.kwargs["metadata"]
        assert metadata["warning"] == "Error processing token usage data"
        assert "error" in metadata
        assert (
            "validation error" in metadata["error"].lower()
            or "type error" in metadata["error"].lower()
        )


@pytest.mark.asyncio
@pytest.mark.integration  # Mark as integration test so it can be skipped
async def test_openrouter_token_tracking_real() -> None:
    """Test token tracking with real API calls (requires API keys)."""
    # This will make a real API call using the underlying function
    result = await complete_openrouter_prompt.fn(
        formatted_prompt="What is 2+2?",  # Simple prompt to minimize tokens
        system_prompt="You are a helpful assistant.",
        task_type="default",
    )

    # Verify we got a response
    assert result is not None
    assert isinstance(result, dict)
    assert "usage" in result
    assert "prompt_tokens" in result["usage"]
    assert "completion_tokens" in result["usage"]
    assert "total_tokens" in result["usage"]

    # Verify token counts are reasonable
    assert result["usage"]["prompt_tokens"] > 0
    assert result["usage"]["completion_tokens"] > 0
    assert result["usage"]["total_tokens"] == (
        result["usage"]["prompt_tokens"] + result["usage"]["completion_tokens"]
    )
