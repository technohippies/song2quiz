"""Tests for semantic units analysis tasks."""

# Standard library imports
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Third-party imports
import pytest

# Local imports
from src.tasks.lyrics_analysis.semantic_units import analyze_fragment


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response for semantic units"""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "semantic_units": [
                        {"text": "test unit", "type": "phrase"}
                    ]
                })
            }
        }]
    }


@pytest.mark.asyncio()
async def test_analyze_fragment_single_unit(mock_openrouter):
    """Test analyzing a single semantic unit"""
    mock_openrouter.return_value = {
        "choices": [{
            "message": {
                "content": '{"semantic_units": [{"id": "1", "text": "test"}]}',
                "role": "assistant"
            }
        }]
    }
    # ... rest of test


@pytest.mark.asyncio()
async def test_analyze_fragment_multiple_units():
    """Test that analyze_fragment correctly processes a line with multiple semantic units."""
    with patch("httpx.Client.post") as mock_post:
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
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
                    }),
                    "role": "assistant"
                }
            }]
        }
        mock_post.return_value = mock_response

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
        assert content["semantic_units"][0]["text"] == "what she order?"
        assert content["semantic_units"][1]["text"] == "Fish fillet"


@pytest.mark.asyncio()
async def test_analyze_fragment_error_handling():
    """Test that analyze_fragment handles errors gracefully."""
    with patch(
        "src.tasks.lyrics_analysis.semantic_units.complete_openrouter_prompt",
        new_callable=AsyncMock,
    ) as mock_complete:
        mock_complete.side_effect = RuntimeError("API Error")

        fragment = {
            "original": "test line",
            "id": "test_id_4",
        }

        result = await analyze_fragment(fragment, 1, 1)
        assert result is None
