"""Example inputs and outputs for vocabulary analysis.

The examples below demonstrate what terms should and should not be included
in the vocabulary analysis.
"""

EXAMPLES = [
    {
        "input": "That whip is fire, no cap",
        "output": {
            "vocabulary": [
                {
                    "term": "whip",
                    "vocabulary_type": "slang",
                    "definition": "A car or vehicle",
                    "usage_notes": "Common in hip-hop and urban slang",
                    "variants": ["whips"],
                    "domain": "automotive/slang",
                },
                {
                    "term": "cap",
                    "vocabulary_type": "slang",
                    "definition": "A lie or to lie",
                    "usage_notes": "Used in phrases like 'no cap' meaning 'no lie'",
                    "variants": ["capping", "capped"],
                    "domain": "general speech",
                },
            ]
        },
    },
    {
        "input": "Finna cop some Yeezys",
        "output": {
            "vocabulary": [
                {
                    "term": "finna",
                    "vocabulary_type": "aave",
                    "definition": "Going to; about to",
                    "usage_notes": "Contraction of 'fixing to'",
                    "variants": ["fixing to", "fin to"],
                    "domain": "general speech",
                },
                {
                    "term": "cop",
                    "vocabulary_type": "slang",
                    "definition": "To acquire or purchase something",
                    "usage_notes": "Informal term for buying",
                    "variants": ["copped", "copping"],
                    "domain": "commerce",
                },
                {
                    "term": "Yeezys",
                    "vocabulary_type": "brand",
                    "definition": "A line of shoes by Kanye West and Adidas",
                    "usage_notes": "Popular sneaker brand",
                    "variants": ["Yeezy"],
                    "domain": "fashion",
                },
            ]
        },
    },
    {
        "input": "I don't know what that means",
        "output": {
            "vocabulary": []  # Skip common contractions like don't, won't, I'm
        },
    },
    {
        "input": "The hands is to the ceiling",
        "output": {
            "vocabulary": []  # Skip basic nouns like 'hands', 'ceiling' even if used non-standardly
        },
    },
    {
        "input": "No one knows what it means, but it's provocative",
        "output": {
            "vocabulary": []  # Skip standard English words like 'provocative' even if sophisticated
        },
    },
    {
        "input": "Gets the people going",
        "output": {
            "vocabulary": []  # Skip common verb phrases and basic English verbs
        },
    },
    {
        "input": "I have a feeling about this",
        "output": {
            "vocabulary": []  # Skip common emotional/mental state words like 'feeling'
        },
    },
]
