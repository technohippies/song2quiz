"""Tests for semantic units analysis tasks."""
import pytest
from src.tasks.lyrics_analysis.semantic_units import analyze_fragment
from src.constants.lyrics_analysis.rhetorical import SemanticUnitType, SemanticLayer

@pytest.mark.asyncio
async def test_analyze_fragment_single_unit():
    """Test that analyze_fragment correctly processes a line with a single semantic unit."""
    # Test input
    fragment = {
        "original": "Audemars that's losing time",
        "id": "test_id_1"
    }
    
    # Run analysis
    result = await analyze_fragment(fragment, 1, 1)
    
    # Verify structure and content
    assert result is not None
    assert "semantic_units" in result
    assert len(result["semantic_units"]) == 1  # One semantic unit
    
    unit = result["semantic_units"][0]
    # Check required fields
    assert "id" in unit
    assert "text" in unit
    assert "type" in unit
    assert "meaning" in unit
    assert "layers" in unit
    
    # Check types
    assert isinstance(unit["id"], str)
    assert isinstance(unit["text"], str)
    assert unit["type"] in [t.value for t in SemanticUnitType]
    assert isinstance(unit["meaning"], str)
    assert isinstance(unit["layers"], list)
    assert all(layer in [l.value for l in SemanticLayer] for layer in unit["layers"])

@pytest.mark.asyncio
async def test_analyze_fragment_multiple_units():
    """Test that analyze_fragment correctly processes a line with multiple semantic units."""
    fragment = {
        "original": "what she order? Fish fillet?",
        "id": "test_id_2"
    }
    
    result = await analyze_fragment(fragment, 1, 1)
    
    assert result is not None
    assert "semantic_units" in result
    assert len(result["semantic_units"]) == 2  # Should identify two units
    
    # Check each unit
    for unit in result["semantic_units"]:
        assert all(key in unit for key in ["id", "text", "type", "meaning", "layers"])
        assert unit["type"] in [t.value for t in SemanticUnitType]
        assert all(layer in [l.value for l in SemanticLayer] for layer in unit["layers"])

@pytest.mark.asyncio
async def test_analyze_fragment_no_semantic_units():
    """Test that analyze_fragment correctly handles lines without semantic units."""
    fragment = {
        "original": "[Verse 1: Artist Name]",
        "id": "test_id_3"
    }
    
    result = await analyze_fragment(fragment, 1, 1)
    
    assert result is not None
    assert "semantic_units" in result
    assert len(result["semantic_units"]) == 0  # Should have no semantic units

@pytest.mark.asyncio
async def test_analyze_fragment_error_handling():
    """Test that analyze_fragment handles errors gracefully."""
    # Test with invalid input
    fragment = {
        "wrong_key": "This should fail",
        "id": "test_id_4"
    }
    
    result = await analyze_fragment(fragment, 1, 1)
    assert result is None  # Should return None on error
