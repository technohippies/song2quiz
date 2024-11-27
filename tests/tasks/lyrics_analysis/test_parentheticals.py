"""Tests for parenthetical analysis task."""
import pytest
from src.tasks.lyrics_analysis.parentheticals import analyze_parentheticals, get_context_lines

@pytest.mark.asyncio
async def test_analyze_parentheticals_with_adlib():
    """Test analyzing parentheticals with ad-lib."""
    lyrics = "Money on my mind (yeah)"
    result = await analyze_parentheticals(lyrics)
    
    assert result["is_parenthetical"] is True
    assert result["clean"] == "Money on my mind"
    assert result["parenthetical_analysis"]["type"] == "ADLIB"
    assert result["parenthetical_analysis"]["content"] == "yeah"
    
@pytest.mark.asyncio
async def test_analyze_parentheticals_with_context():
    """Test analyzing parentheticals with context lines."""
    lyrics = "Started from the bottom (now we here)"
    context = ["Work work work work work", lyrics, "Running out of pages"]
    result = await analyze_parentheticals(lyrics, context)
    
    assert result["is_parenthetical"] is True
    assert result["clean"] == "Started from the bottom"
    assert result["parenthetical_analysis"]["type"] == "OTHER"
    assert result["parenthetical_analysis"]["content"] == "now we here"
    assert result["parenthetical_analysis"]["context"] == "\n".join(context)
    assert result["parenthetical_analysis"]["related_lyrics"] == context
    
@pytest.mark.asyncio
async def test_analyze_parentheticals_no_parens():
    """Test analyzing lyrics without parentheticals."""
    lyrics = "Started from the bottom"
    result = await analyze_parentheticals(lyrics)
    
    assert result["is_parenthetical"] is False
    assert result["clean"] == lyrics
    assert "parenthetical_analysis" not in result
    
def test_get_context_lines():
    """Test getting context lines."""
    lyrics = ["line 1", "line 2", "line 3", "line 4", "line 5"]
    
    # Test middle of list
    assert get_context_lines(lyrics, 2, window=1) == ["line 2", "line 3", "line 4"]
    
    # Test start of list
    assert get_context_lines(lyrics, 0, window=1) == ["line 1", "line 2"]
    
    # Test end of list
    assert get_context_lines(lyrics, 4, window=1) == ["line 4", "line 5"]
    
    # Test larger window
    assert get_context_lines(lyrics, 2, window=2) == ["line 1", "line 2", "line 3", "line 4", "line 5"]
