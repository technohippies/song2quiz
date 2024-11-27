"""Tests for parenthetical analysis task."""
from src.tasks.lyrics_analysis.parentheticals import analyze_parentheticals

def test_analyze_parentheticals_with_adlib():
    """Test analyzing parentheticals with ad-lib."""
    lyrics = "Money on my mind (yeah)"
    result = analyze_parentheticals(lyrics)
    
    assert "line_without_parentheses" in result
    assert "parentheticals" in result
    assert result["line_without_parentheses"] == "Money on my mind"
    assert result["parentheticals"] == ["yeah"]

def test_analyze_parentheticals_with_context():
    """Test analyzing parentheticals with context lines."""
    lyrics = "Started from the bottom (now we here)"
    result = analyze_parentheticals(lyrics)
    
    assert "line_without_parentheses" in result
    assert "parentheticals" in result
    assert result["line_without_parentheses"] == "Started from the bottom"
    assert result["parentheticals"] == ["now we here"]

def test_analyze_parentheticals_no_parens():
    """Test analyzing lyrics without parentheticals."""
    lyrics = "Started from the bottom"
    result = analyze_parentheticals(lyrics)
    
    assert "line_without_parentheses" in result
    assert "parentheticals" in result
    assert result["line_without_parentheses"] == lyrics
    assert result["parentheticals"] == []
