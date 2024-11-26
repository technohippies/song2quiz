"""Example inputs and outputs for vocabulary analysis."""

EXAMPLES = [
    {
        "input": "I'm finna pull up in that new whip",
        "output": {
            "vocabulary": [
                {
                    "term": "finna",
                    "vocabulary_type": "aave",
                    "definition": "Going to; about to",
                    "usage_notes": "Contraction of 'fixing to'",
                    "variants": ["finna'", "fixing to", "fin to"],
                    "domain": "general speech"
                },
                {
                    "term": "pull up",
                    "vocabulary_type": "phrasal_verb",
                    "definition": "To arrive somewhere, typically in a vehicle",
                    "usage_notes": "Often used to indicate arrival at a location",
                    "variants": ["pulling up", "pulled up"],
                    "domain": "general speech"
                },
                {
                    "term": "whip",
                    "vocabulary_type": "slang",
                    "definition": "Car, vehicle",
                    "usage_notes": "Common in hip-hop when referring to vehicles",
                    "variants": ["whippin'", "whips"],
                    "domain": "automotive/street"
                }
            ]
        }
    },
    {
        "input": "Got them J's on with the Chi-town flow",
        "output": {
            "vocabulary": [
                {
                    "term": "J's",
                    "vocabulary_type": "slang",
                    "definition": "Jordan brand sneakers",
                    "usage_notes": "Popular reference to Air Jordan sneakers",
                    "variants": ["Jordans", "Air Jordans", "Jordan's"],
                    "domain": "fashion/sneakers"
                },
                {
                    "term": "Chi-town",
                    "vocabulary_type": "colloquialism",
                    "definition": "Chicago, Illinois",
                    "usage_notes": "Common nickname for Chicago",
                    "variants": ["Chi", "The Chi", "Chitown"],
                    "domain": "geography/culture"
                }
            ]
        }
    },
    {
        "input": "Yesterday, all my troubles seemed so far away",
        "output": {
            "vocabulary": []  # Example of standard English with no special terms to analyze
        }
    }
]
