"""Tests for vocabulary analysis tasks."""
import pytest
from src.tasks.lyrics_analysis.vocabulary import analyze_fragment

@pytest.mark.asyncio
async def test_analyze_fragment():
    """Test that analyze_fragment correctly processes a line with vocabulary terms."""
    # Test input
    fragment = {
        "text": "That whip is fire, no cap",
        "id": "test_id_1",
        "timestamp": "00:00:10",
        "annotation": None
    }
    
    # Run analysis
    result = await analyze_fragment(fragment, 1, 1)
    
    # Verify structure and content
    assert result is not None
    assert "vocabulary" in result
    assert len(result["vocabulary"]) == 1  # One entry for this fragment
    
    vocab_entry = result["vocabulary"][0]
    # Check fragment metadata
    assert vocab_entry["original"] == fragment["text"]
    assert vocab_entry["id"] == fragment["id"]
    assert vocab_entry["timestamp"] == fragment["timestamp"]
    
    # Verify vocabulary terms structure
    assert "vocabulary" in vocab_entry
    terms = vocab_entry["vocabulary"]
    assert len(terms) > 0  # Should have at least one term
    
    # Check structure of each term
    for term in terms:
        assert "term" in term
        assert "vocabulary_type" in term
        assert "definition" in term
        assert isinstance(term["term"], str)
        assert isinstance(term["vocabulary_type"], str)
        assert isinstance(term["definition"], str)

@pytest.mark.asyncio
async def test_analyze_fragment_no_vocabulary():
    """Test that analyze_fragment correctly handles lines without special vocabulary."""
    fragment = {
        "text": "I love you",
        "id": "test_id_2",
        "timestamp": "00:00:20",
        "annotation": None
    }
    
    result = await analyze_fragment(fragment, 1, 1)
    assert result is None  # Should return None for lines without special vocabulary
