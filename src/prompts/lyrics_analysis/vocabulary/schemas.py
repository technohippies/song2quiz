"""JSON schemas for vocabulary analysis responses."""

from typing import Dict

VOCABULARY_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "vocabulary": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["term", "vocabulary_type", "definition"],
                "properties": {
                    "term": {"type": "string"},
                    "vocabulary_type": {
                        "type": "string",
                        "enum": [
                            "proper_noun",
                            "brand",
                            "slang",
                            "aave",
                            "vernacular",
                            "colloquialism",
                            "acronym",
                            "compound",
                            "portmanteau",
                            "idiom",
                            "phrasal_verb",
                            "neologism",
                            "wordplay",
                        ],
                    },
                    "definition": {"type": "string"},
                    "usage_notes": {"type": "string"},
                    "variants": {"type": "array", "items": {"type": "string"}},
                    "see_also": {"type": "array", "items": {"type": "string"}},
                    "etymology": {"type": "string"},
                    "register": {"type": "string"},
                    "domain": {"type": "string"},
                },
            },
        }
    },
    "required": ["vocabulary"],
}

SCHEMAS: Dict[str, dict] = {"vocabulary_response": VOCABULARY_RESPONSE_SCHEMA}
