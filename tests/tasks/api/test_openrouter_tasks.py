"""Test OpenRouter tasks."""
import asyncio
import os
import pytest
from unittest.mock import patch, AsyncMock

from src.tasks.api.openrouter_tasks import complete_openrouter_prompt

@pytest.fixture
def mock_openrouter_response():
    """Mock successful OpenRouter API response"""
    return {
        "id": "test-id",
        "model": "test-model",
        "created": 1234567890,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": '{"test_prompt": "This is a test prompt."}'
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings to provide API key"""
    with patch('src.utils.settings') as mock_settings:
        # Use real API key from env if available, otherwise use test key
        api_key = os.getenv('OPENROUTER_API_KEY', 'test-key')
        print(f"Using API key: {api_key[:8]}...")  # Print first 8 chars for debugging
        mock_settings.OPENROUTER_API_KEY = api_key
        yield mock_settings

@pytest.mark.asyncio
async def test_complete_prompt_success():
    """Test complete_prompt with mocked response."""
    mock_response = {
        "id": "test-id",
        "choices": [{
            "message": {
                "content": """{"vocabulary": [{"term": "test", "vocabulary_type": "noun", "definition": "def", "usage_notes": "notes", "variants": ["tests"]}]}""",
                "role": "assistant"
            },
            "finish_reason": "stop"
        }]
    }
    
    with patch("src.services.openrouter.OpenRouterClient.complete", 
               new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = mock_response
        
        result = await complete_openrouter_prompt(
            formatted_prompt="Test prompt",
            system_prompt="You are a test assistant",
            task_type="default",
            temperature=0.7,
            max_tokens=512
        )
        
        # Should return parsed JSON
        assert isinstance(result, dict)
        assert "vocabulary" in result
        assert len(result["vocabulary"]) == 1
        assert result["vocabulary"][0]["term"] == "test"

@pytest.mark.asyncio
async def test_complete_prompt_invalid_json():
    """Test handling of non-JSON response."""
    mock_response = {
        "id": "test-id",
        "choices": [{
            "message": {
                "content": "not a json response",
                "role": "assistant"
            },
            "finish_reason": "stop"
        }]
    }
    
    with patch("src.services.openrouter.OpenRouterClient.complete", 
               new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = mock_response
        
        result = await complete_openrouter_prompt(
            formatted_prompt="Test prompt",
            system_prompt="You are a test assistant",
            task_type="default",
            max_tokens=100
        )
        
        # Should return raw response if JSON parsing fails
        assert result == mock_response

@pytest.mark.asyncio
async def test_complete_prompt_error():
    """Test error handling and retries."""
    with patch("src.services.openrouter.OpenRouterClient.complete", 
               new_callable=AsyncMock) as mock_complete:
        mock_complete.side_effect = RuntimeError("API Error")
        
        with pytest.raises(RuntimeError, match="API Error"):
            await complete_openrouter_prompt(
                formatted_prompt="Test prompt",
                system_prompt="You are a test assistant",
                task_type="default",
                max_tokens=100
            )
        
        # Verify the mock was called 4 times (1 initial + 3 retries)
        assert mock_complete.call_count == 4

@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_prompt_integration():
    """Test complete_prompt with actual API call."""
    try:
        async with asyncio.timeout(10):  # Longer timeout for actual API call
            result = await complete_openrouter_prompt(
                formatted_prompt="What is 1+1?",
                system_prompt="You are a helpful math tutor. Provide only the numerical answer.",
                task_type="default",  
                temperature=0.1,
                max_tokens=100
            )
            
            # Verify we get a valid vocabulary response
            assert isinstance(result, dict)
            assert "vocabulary" in result
            assert len(result["vocabulary"]) > 0
            assert "term" in result["vocabulary"][0]
            
    except asyncio.TimeoutError:
        pytest.fail("API call timed out")