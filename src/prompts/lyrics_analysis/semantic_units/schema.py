"""Schema for semantic units analysis."""

from src.constants.lyrics_analysis.rhetorical import SemanticLayer, SemanticUnitType

SEMANTIC_UNITS_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Unique identifier for the lyric line"},
        "text": {
            "type": "string",
            "description": "The original text of the semantic unit",
        },
        "type": {
            "type": "string",
            "enum": [unit_type.value for unit_type in SemanticUnitType],
            "description": "The type of semantic unit",
        },
        "meaning": {
            "type": "string",
            "description": "The literal or surface meaning of the unit",
        },
        "layers": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [layer.value for layer in SemanticLayer],
            },
            "description": "Different interpretative layers of meaning",
        },
        "annotation": {
            "type": "string",
            "description": "Detailed explanation of cultural, historical, or contextual significance",
        },
    },
    "required": ["id", "text", "type", "meaning", "annotation"],
}
