"""Tests for semantic units analysis tasks."""
import pytest
from unittest.mock import AsyncMock, patch
from src.tasks.lyrics_analysis.semantic_units import analyze_fragment
from src.models.lyrics_analysis.semantic_unit import SemanticUnitsAnalysis

@pytest.mark.asyncio
async def test_analyze_fragment_single_unit():
    """Test that analyze_fragment correctly processes a line with a single semantic unit."""
    mock_response = {
        "semantic_units": [{
            "id": "1",
            "text": "Test fragment",
            "type": "DOUBLE_MEANING",
            "meaning": "Test meaning",
            "layers": ["LITERAL", "FIGURATIVE"],
            "annotation": "Test annotation"
        }]
    }
    
    with patch("src.tasks.api.openrouter_tasks.complete_openrouter_prompt", 
              new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = mock_response
        
        fragment = {
            "original": "Test fragment",
            "id": "1"
        }
        
        result = await analyze_fragment(fragment, 1, 1)
        assert result is not None
        analysis = SemanticUnitsAnalysis(**result)
        unit = analysis.semantic_units[0]
        assert unit.id == "1"

@pytest.mark.asyncio
async def test_analyze_fragment_multiple_units():
    """Test that analyze_fragment correctly processes a line with multiple semantic units."""
    mock_response = {
        "semantic_units": [
            {
                "id": "1",
                "text": "what she order",
                "type": "CULTURAL_REFERENCE",
                "meaning": "Reference to ordering at a restaurant",
                "layers": ["LITERAL"],
                "annotation": "Setup for wordplay"
            },
            {
                "id": "2",
                "text": "Fish fillet",
                "type": "WORDPLAY",
                "meaning": "McDonald's Filet-O-Fish sandwich",
                "layers": ["LITERAL", "CULTURAL"],
                "annotation": "Fast food reference"
            }
        ]
    }
    
    with patch("src.tasks.api.openrouter_tasks.complete_openrouter_prompt",
              new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = mock_response
        
        fragment = {
            "original": "what she order? Fish fillet?",
            "id": "1"
        }
        
        result = await analyze_fragment(fragment, 1, 1)
        assert result is not None
        analysis = SemanticUnitsAnalysis(**result)
        # Just check we got two units back
        assert len(analysis.semantic_units) == 2

@pytest.mark.asyncio
async def test_analyze_fragment_error_handling():
    """Test that analyze_fragment handles errors gracefully."""
    with patch("src.tasks.lyrics_analysis.semantic_units.complete_openrouter_prompt", 
              new_callable=AsyncMock) as mock_complete:
        mock_complete.side_effect = RuntimeError("API Error")
        
        fragment = {
            "original": "test line",
            "id": "test_id_4"
        }
        
        result = await analyze_fragment(fragment, 1, 1)
        assert result is None
