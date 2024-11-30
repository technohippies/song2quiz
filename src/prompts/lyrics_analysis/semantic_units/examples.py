"""Example semantic unit analyses for prompting."""

EXAMPLES = [
    {
        "text": "I'm living life in the fast lane",
        "analysis": {
            "semantic_units": [
                {
                    "text": "living life in the fast lane",
                    "type": "IDIOM",
                    "meaning": "Living a risky or hectic lifestyle",
                    "layers": ["LITERAL", "METAPHORICAL"],
                    "annotation": "Common idiom referring to a fast-paced, risky lifestyle",
                }
            ]
        },
    },
    {
        "text": "Started from the bottom now we here",
        "analysis": {
            "semantic_units": [
                {
                    "text": "Started from the bottom",
                    "type": "METAPHOR",
                    "meaning": "Began from a humble or difficult position",
                    "layers": ["LITERAL", "METAPHORICAL", "CULTURAL"],
                    "annotation": "References the journey from poverty or obscurity to success",
                },
                {
                    "text": "now we here",
                    "type": "PHRASE",
                    "meaning": "We have achieved success or reached a better position",
                    "layers": ["LITERAL", "CULTURAL"],
                    "annotation": "Contrasts current success with past struggles",
                },
            ]
        },
    },
]
