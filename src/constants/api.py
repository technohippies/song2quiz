"""API-related constants."""

# OpenRouter Models
# See https://openrouter.ai/docs for available models
DEFAULT_MODEL = ["google/gemini-flash-1.5-8b"]
FALLBACK_MODEL = ["nvidia/llama-3.1-nemotron-70b-instruct"]  # Fallback for content blocks
FREE_MODEL = ["google/gemini-flash-1.5-8b"]  # Free model for testing

OPENROUTER_MODELS = {
    "default": [
        "google/gemini-pro",
        "anthropic/claude-2",
        "meta-llama/llama-2-70b-chat"
    ],
    "fallback": FALLBACK_MODEL,
    "test": FREE_MODEL,  # Use free model for testing
    "vocabulary": [
        "google/gemini-flash-1.5-8b",  # Fast model for parallel processing
        "google/gemini-pro",
        "anthropic/claude-2"
    ],
    "translation": ["google/gemini-flash-1.5-8b"],  # Good for translation tasks
    "enhance_lyrics": ["google/gemini-flash-1.5-8b"],  # Creative writing
    "analysis": ["google/gemini-flash-1.5-8b"]  # Detailed analysis tasks
}
