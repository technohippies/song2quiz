"""JSON schemas for lyrics analysis validation."""
from typing import List

from .linguistic import CEFRLevel, GrammaticalTense, SentenceType
from .rhetorical import RhetoricalDevice, SemanticLayer

# Validation Schema
ANALYSIS_SCHEMA = {
    "type": "object",
    "required": [
        "original",
        "standardized_american_english",
        "proper_nouns",
        "content_analysis",
        "clean_version",
        "grammar_patterns",
        "semantic_units",
        "is_parenthetical", 
    ],
    "properties": {
        "original": {"type": "string"},
        "standardized_american_english": {"type": "string"},
        "is_parenthetical": {"type": "boolean"},
        "standardized_american_english_without_parens": {
            "type": "string",
            "description": "Only present when is_parenthetical is true"
        },
        "proper_nouns": {
            "type": "array",
            "items": {"type": "string"}
        },
        "content_analysis": {
            "type": "object",
            "required": ["themes", "cultural_references", "difficulty_level"],
            "properties": {
                "themes": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "cultural_references": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "difficulty_level": {
                    "type": "string",
                    "enum": [level.value for level in CEFRLevel]
                }
            }
        },
        "grammar_patterns": {
            "type": "object",
            "required": ["tense", "sentence_type", "structures"],
            "properties": {
                "tense": {
                    "type": "string",
                    "enum": [tense.value for tense in GrammaticalTense]
                },
                "sentence_type": {
                    "type": "string",
                    "enum": [stype.value for stype in SentenceType]
                },
                "structures": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "rhetorical_analysis": {
            "type": "object",
            "required": ["devices", "semantic_layers"],
            "properties": {
                "devices": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["type", "text", "explanation"],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [device.value for device in RhetoricalDevice]
                            },
                            "text": {"type": "string"},
                            "explanation": {"type": "string"}
                        }
                    }
                },
                "semantic_layers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["layer", "meaning", "context"],
                        "properties": {
                            "layer": {
                                "type": "string",
                                "enum": [layer.value for layer in SemanticLayer]
                            },
                            "meaning": {"type": "string"},
                            "context": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
}
