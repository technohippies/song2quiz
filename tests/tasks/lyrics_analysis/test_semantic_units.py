"""Tests for semantic units analysis tasks."""

# Standard library imports
import json
from unittest.mock import AsyncMock, patch

# Third-party imports
import pytest

# Local imports
from src.tasks.lyrics_analysis.semantic_units import analyze_fragment


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response for semantic units"""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {"semantic_units": [{"text": "test unit", "type": "phrase"}]}
                    )
                }
            }
        ]
    }


@pytest.mark.asyncio()
async def test_analyze_fragment_single_unit():
    """Test analyzing a single semantic unit"""
    with patch(
        "src.tasks.lyrics_analysis.semantic_units.complete_openrouter_prompt",
        new_callable=AsyncMock,
    ) as mock_openrouter:
        # Setup mock response with matching text
        mock_openrouter.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"semantic_units": [{"id": "1", "text": "test line"}]}',
                        "role": "assistant",
                    }
                }
            ]
        }

        # Call the function with test data
        fragment = {"text": "test line"}
        result = await analyze_fragment(fragment, 1, 1)

        # Verify the result
        assert result is not None
        assert "choices" in result
        assert len(result["choices"]) == 1
        assert "message" in result["choices"][0]
        assert "content" in result["choices"][0]["message"]

        # Parse and verify the content
        content = json.loads(result["choices"][0]["message"]["content"])
        assert "semantic_units" in content
        assert len(content["semantic_units"]) == 1
        assert content["semantic_units"][0]["id"] == "1"
        assert content["semantic_units"][0]["text"] == "test line"

        # Verify the mock was called correctly
        mock_openrouter.assert_called_once()


@pytest.mark.asyncio()
async def test_analyze_fragment_multiple_units():
    """Test that analyze_fragment correctly processes a line with multiple semantic units."""
    with patch(
        "src.tasks.lyrics_analysis.semantic_units.complete_openrouter_prompt",
        new_callable=AsyncMock,
    ) as mock_complete:
        # Mock the API response
        mock_complete.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "semantic_units": [
                                    {
                                        "id": "1",
                                        "text": "what she order",
                                        "type": "CULTURAL_REFERENCE",
                                        "meaning": "Reference to ordering at a restaurant",
                                        "layers": ["LITERAL"],
                                        "annotation": "Setup for wordplay",
                                    },
                                    {
                                        "id": "2",
                                        "text": "Fish fillet",
                                        "type": "WORDPLAY",
                                        "meaning": "McDonald's Filet-O-Fish sandwich",
                                        "layers": ["LITERAL", "CULTURAL"],
                                        "annotation": "Fast food reference",
                                    },
                                ]
                            }
                        ),
                        "role": "assistant",
                    }
                }
            ]
        }

        fragment = {"text": "what she order? Fish fillet"}
        result = await analyze_fragment(fragment, 1, 1)

        # Parse the response
        assert result is not None
        assert "choices" in result
        assert len(result["choices"]) > 0
        assert "message" in result["choices"][0]
        assert "content" in result["choices"][0]["message"]

        # Parse the content as JSON
        content = json.loads(result["choices"][0]["message"]["content"])
        assert "semantic_units" in content
        assert len(content["semantic_units"]) == 2
        # Compare core text content without punctuation
        assert content["semantic_units"][0]["text"].rstrip("?") == "what she order"
        assert content["semantic_units"][1]["text"].rstrip("?") == "Fish fillet"


@pytest.mark.asyncio()
async def test_analyze_fragment_rate_limit():
    """Test that analyze_fragment handles rate limit errors with retries."""
    with patch(
        "src.tasks.lyrics_analysis.semantic_units.complete_openrouter_prompt",
        new_callable=AsyncMock,
    ) as mock_complete:
        # Mock rate limit error that succeeds after retry
        mock_complete.side_effect = [
            RuntimeError("resource_exhausted: rate limit exceeded"),  # First call fails
            {  # Second call succeeds
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "semantic_units": [
                                        {
                                            "id": "1",
                                            "text": "test line",
                                            "type": "PHRASE",
                                            "meaning": "A test phrase",
                                            "layers": ["LITERAL"],
                                            "annotation": "Test annotation",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ]
            },
        ]

        fragment = {"text": "test line"}
        result = await analyze_fragment(fragment, 1, 1)

        # Should succeed on retry
        assert result is not None
        content = json.loads(result["choices"][0]["message"]["content"])
        assert "semantic_units" in content
        assert len(content["semantic_units"]) == 1
        assert content["semantic_units"][0]["text"] == "test line"

        # Verify it was called twice (initial + retry)
        assert mock_complete.call_count == 2


@pytest.mark.asyncio()
async def test_analyze_fragment_error_handling():
    """Test that analyze_fragment handles various error cases."""
    with patch(
        "src.tasks.lyrics_analysis.semantic_units.complete_openrouter_prompt",
        new_callable=AsyncMock,
    ) as mock_complete:
        # Test generic error
        mock_complete.side_effect = RuntimeError("API Error")
        fragment = {"text": "test line"}
        result = await analyze_fragment(fragment, 1, 1)
        assert result is None

        # Test rate limit error with max retries exceeded
        mock_complete.side_effect = [
            RuntimeError("resource_exhausted: rate limit exceeded"),
            RuntimeError("resource_exhausted: rate limit exceeded"),
            RuntimeError("resource_exhausted: rate limit exceeded"),
            RuntimeError("resource_exhausted: rate limit exceeded"),
        ]
        result = await analyze_fragment(fragment, 1, 1)
        assert result is None

        # Test empty response
        mock_complete.side_effect = None
        mock_complete.return_value = None
        result = await analyze_fragment(fragment, 1, 1)
        assert result is None
