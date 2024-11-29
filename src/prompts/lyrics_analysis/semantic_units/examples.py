"""Example semantic unit analyses for prompting."""

EXAMPLES = [
    {
        "text": "I'm living life in the fast lane",
        "analysis": {
            "semantic_units": [
                {
                    "id": "1",
                    "text": "living life in the fast lane",
                    "type": "IDIOM",
                    "meaning": "Living a risky or hectic lifestyle",
                    "layers": ["LITERAL", "METAPHORICAL"],
                    "annotation": "Common idiom referring to a fast-paced, risky lifestyle"
                }
            ]
        }
    },
    {
        "text": "Started from the bottom now we here",
        "analysis": {
            "semantic_units": [
                {
                    "id": "1",
                    "text": "Started from the bottom",
                    "type": "METAPHOR",
                    "meaning": "Beginning from a difficult or disadvantaged position",
                    "layers": ["METAPHORICAL", "NARRATIVE"],
                    "annotation": "Describes a journey from hardship to success"
                },
                {
                    "id": "2",
                    "text": "now we here",
                    "type": "VERNACULAR",
                    "meaning": "Now we have achieved success",
                    "layers": ["LITERAL"],
                    "annotation": "AAVE construction emphasizing current success"
                }
            ]
        }
    }
]
