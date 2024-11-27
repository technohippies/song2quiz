"""Example inputs and outputs for semantic units analysis."""

EXAMPLES = [
    # Example 1: Single semantic unit
    {
        "input": "Audemars that's losing time",
        "output": {
            "semantic_units": [
                {
                    "id": "a4fd2be2",
                    "text": "Audemars that's losing time",
                    "type": "CULTURAL_REFERENCE",
                    "meaning": "A luxury watch that is not keeping accurate time",
                    "layers": [
                        "LITERAL",
                        "CULTURAL",
                        "FIGURATIVE"
                    ]
                }
            ]
        }
    },
    
    # Example 2: Two semantic units (question and answer)
    {
        "input": "what she order? Fish fillet?",
        "output": {
            "semantic_units": [
                {
                    "id": "b5ef3cd1",
                    "text": "what she order?",
                    "type": "PHRASE",
                    "meaning": "Questioning what a woman ordered at a restaurant",
                    "layers": [
                        "LITERAL",
                        "CULTURAL"
                    ]
                },
                {
                    "id": "c6gh4ef2",
                    "text": "Fish fillet?",
                    "type": "CULTURAL_REFERENCE",
                    "meaning": "A basic menu item at fast-food restaurants",
                    "layers": [
                        "LITERAL",
                        "CULTURAL",
                        "PERSONAL"
                    ]
                }
            ]
        }
    },

    # Example 3: Three semantic units with connecting words shown in relationship
    {
        "input": "Crown on my head but I'm king of the hill, every day I'm grinding I'm on to the mill",
        "output": {
            "semantic_units": [
                {
                    "id": "d7hi5fg3",
                    "text": "Crown on my head",
                    "type": "METAPHOR",
                    "meaning": "Wearing a crown, symbol of royalty",
                    "layers": [
                        "LITERAL",
                        "FIGURATIVE"
                    ]
                },
                {
                    "id": "e8ij6gh4",
                    "text": "I'm king of the hill",
                    "type": "IDIOM",
                    "meaning": "Being at the top position or most dominant",
                    "layers": [
                        "LITERAL",
                        "FIGURATIVE",
                        "CULTURAL"
                    ]
                },
                {
                    "id": "f9jk7hi5",
                    "text": "every day I'm grinding I'm on to the mill",
                    "type": "DOUBLE_MEANING",
                    "meaning": "Constantly working hard",
                    "layers": [
                        "LITERAL",
                        "FIGURATIVE",
                        "CULTURAL"
                    ]
                }
            ]
        }
    },

    # Example 4: Not a semantic unit (technical directions)
    {
        "input": "[Verse 1: Artist Name] [Produced by Producer Name]",
        "output": {
            "semantic_units": []  # Empty because these are technical annotations, not meaningful units
        }
    }
]

# Note: Example 4 shows that technical metadata, credits, or structural markers 
# should not be analyzed as semantic units as they don't contribute to the 
# meaning or interpretation of the lyrics themselves.

# Note: Connecting words like 'but', 'and', 'so' are not included in the semantic units themselves.
# The relationships between units will be documented in manually added annotations.