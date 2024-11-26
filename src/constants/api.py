"""API-related constants."""

# OpenRouter Models
# See https://openrouter.ai/docs for available models
DEFAULT_MODEL = "google/gemini-flash-1.5-8b"
FREE_MODEL = "google/gemini-flash-1.5-8b"  # Free model for testing

OPENROUTER_MODELS = {
    "default": DEFAULT_MODEL,
    "test": FREE_MODEL,  # Use free model for testing
    "vocabulary": "google/gemini-flash-1.5-8b",  # Best for linguistic analysis
    "translation": "google/gemini-flash-1.5-8b",  # Good for translation tasks
    "enhance_lyrics": "google/gemini-flash-1.5-8b",  # Creative writing
    "analysis": "google/gemini-flash-1.5-8b"  # Detailed analysis tasks
}
