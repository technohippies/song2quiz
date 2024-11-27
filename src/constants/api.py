"""API-related constants."""

# OpenRouter Models
# See https://openrouter.ai/docs for available models
DEFAULT_MODEL = ["google/gemini-flash-1.5-8b"]
FALLBACK_MODEL = ["nvidia/llama-3.1-nemotron-70b-instruct"]  # Fallback for content blocks

OPENROUTER_MODELS = {
    "default": ["google/gemini-flash-1.5-8b"],
    "fallback": FALLBACK_MODEL,
    "vocabulary": ["google/gemini-flash-1.5-8b"],  # Fast model for parallel processing
    "translation": ["google/gemini-flash-1.5-8b"],  # Good for translation tasks
    "enhance_lyrics": ["google/gemini-flash-1.5-8b"],  # Creative writing
    "analysis": ["google/gemini-flash-1.5-8b"]  # Detailed analysis tasks
}
