"""Test script for OpenRouter API."""
import asyncio
import json
import logging

from src.services.openrouter import OpenRouterClient

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_api():
    """Test a simple API call."""
    try:
        client = OpenRouterClient(task_type="vocabulary")

        # Simple test prompt
        prompt = """Analyze ONLY the non-standard vocabulary in this lyric and return a raw JSON object:
'I'm finna pull up in that new whip'

IMPORTANT:
1. Do not include basic English words like "new"
2. Do not wrap the response in markdown code blocks
3. Return only the raw JSON"""

        system_prompt = """You are an expert linguist specializing in vocabulary analysis. You MUST follow these rules exactly:

1. Return ONLY a raw JSON object - no markdown, no ```json blocks, no additional text
2. Only analyze non-standard vocabulary terms that would need explanation
3. Skip basic English words like "new" - only include terms that have special cultural or linguistic significance
4. Use ONLY these vocabulary types (no other types allowed):
   - "proper_noun" - for names (e.g., "Jay-Z")
   - "brand" - for products (e.g., "Gucci")
   - "slang" - for informal terms (e.g., "flex")
   - "aave" - for AAVE terms (e.g., "finna")
   - "vernacular" - for dialect terms (e.g., "ting")
   - "colloquialism" - for informal terms (e.g., "gonna")
   - "acronym" - for abbreviated terms (e.g., "GOAT")
   - "compound" - for combined words (e.g., "mic-drop")
   - "portmanteau" - for blended words (e.g., "brunch")
   - "idiom" - for phrases with special meaning
   - "phrasal_verb" - for verb phrases (e.g., "pull up")
   - "neologism" - for new words
   - "wordplay" - for creative word use

The response must be this exact JSON structure with no wrapping:
{
  "vocabulary": [
    {
      "term": string,
      "vocabulary_type": string (must be one from the list above),
      "definition": string,
      "usage_notes": string,
      "variants": array of strings
    }
  ]
}"""

        logger.info("Making API call...")
        result = await client.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1024
        )

        logger.info(f"Raw result: {json.dumps(result, indent=2)}")
        return result

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_api())
    if result:
        print("\nSuccess! Result:")
        print(json.dumps(result, indent=2))
    else:
        print("\nFailed to get response")
