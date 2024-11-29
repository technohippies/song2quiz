"""API-related constants."""

# OpenRouter Models
# See https://openrouter.ai/docs for available models
DEFAULT_MODEL = ["google/gemini-flash-1.5-8b"]
FALLBACK_MODEL = [
    "nvidia/llama-3.1-nemotron-70b-instruct"
]  # Fallback for content blocks

OPENROUTER_MODELS = {
    "default": ["google/gemini-flash-1.5-8b"],
    "fallback": FALLBACK_MODEL,
    "vocabulary": ["google/gemini-flash-1.5-8b"],  # Fast model for parallel processing
    "translation": ["google/gemini-flash-1.5-8b"],  # Good for translation tasks
    "enhance_lyrics": ["google/gemini-flash-1.5-8b"],  # Creative writing
    "analysis": ["google/gemini-flash-1.5-8b"],  # Detailed analysis tasks
}

MODEL_COSTS = {
    "google/gemini-flash-1.5-8b": {
        "input_cost": 0.0000375,  # Per token
        "output_cost": 0.00015,
    },
    "nvidia/llama-3.1-nemotron-70b-instruct": {
        "input_cost": 0.0002,
        "output_cost": 0.0004,
    },
}
