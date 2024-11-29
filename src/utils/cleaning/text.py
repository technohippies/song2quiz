"""Core text cleaning utilities."""

import json
import logging
import re
from typing import Any, Dict, List, Tuple, Union

from ftfy import fix_text
from ftfy.fixes import uncurl_quotes

from src.constants.lyrics_analysis.linguistic import ParentheticalType

logger = logging.getLogger(__name__)


class TextCleaningError(Exception):
    """Custom exception for text cleaning errors."""

    pass


def classify_parenthetical(content: str) -> ParentheticalType:
    """Classify the type of parenthetical content.

    Args:
        content: The text inside parentheses to classify

    Returns:
        ParentheticalType enum value
    """
    content = content.lower().strip()

    # Common ad-libs
    if any(adlib in content for adlib in ["yeah", "uh", "oh", "ay", "woo", "hey"]):
        return ParentheticalType.ADLIB

    # Background vocals often have descriptive terms
    if any(
        term in content
        for term in ["backing", "background", "vocals", "harmonies", "chorus"]
    ):
        return ParentheticalType.BACKGROUND

    # Sound effects often describe sounds
    if any(term in content for term in ["sound", "noise", "sfx", "effect", "beat"]):
        return ParentheticalType.SOUND_EFFECT

    # Action descriptions
    if any(term in content for term in ["repeat", "fade", "stops", "starts", "plays"]):
        return ParentheticalType.OTHER

    # Repetition markers
    if any(term in content for term in ["x2", "x3", "x4", "repeat", "times"]):
        return ParentheticalType.REPETITION

    # Check for alternate lyrics (often OR or alternative phrasings)
    if " or " in content or "alt" in content:
        return ParentheticalType.ALTERNATE

    # Check for translations (often has foreign words)
    if ":" in content or "means" in content or "translation" in content:
        return ParentheticalType.TRANSLATION

    # Clarifications often explain context
    if any(
        term in content for term in ["referring", "means", "i.e.", "aka", "meaning"]
    ):
        return ParentheticalType.CLARIFICATION

    return ParentheticalType.OTHER


def extract_parentheticals(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Extract and classify content in parentheses from text, including nested parentheses.

    Args:
        text: Input text containing parenthetical content

    Returns:
        Tuple of (text with parentheses removed, list of parenthetical content with type)

    Examples:
        >>> text = "Hello (yeah) and (good (morning) everyone)"
        >>> clean, parens = extract_parentheticals(text)
        >>> clean
        'Hello and everyone'
        >>> parens
        [
            {'content': 'yeah', 'type': 'ADLIB'},
            {'content': 'good (morning)', 'type': 'OTHER'}
        ]

        >>> text = "No parentheses here"
        >>> clean, parens = extract_parentheticals(text)
        >>> clean
        'No parentheses here'
        >>> parens
        []

    Raises:
        TextCleaningError: If regex fails
    """
    if not text:
        return "", []

    try:
        # Find outermost parentheses first
        parentheticals = []
        clean_text = text

        while "(" in clean_text:
            # Find the next outermost pair
            stack = []
            start = -1
            found_pair = False

            for i, char in enumerate(clean_text):
                if char == "(":
                    if not stack:
                        start = i
                    stack.append(i)
                elif char == ")":
                    if stack:
                        stack.pop()
                        if not stack:  # Found complete outermost pair
                            content = clean_text[start + 1 : i]
                            ptype = classify_parenthetical(content)
                            parentheticals.append(
                                {"content": content, "type": ptype.value}
                            )
                            clean_text = clean_text[:start] + clean_text[i + 1 :]
                            found_pair = True
                            break

            # If no complete pair was found, break to avoid infinite loop
            if not found_pair:
                logger.warning(f"Found unmatched parentheses in text: {clean_text}")
                break

        # Clean up extra whitespace and fix comma spacing
        clean_text = re.sub(r"\s+", " ", clean_text).strip()
        clean_text = re.sub(
            r"\s*,\s*", ", ", clean_text
        )  # Ensure exactly one space after comma

        return clean_text, parentheticals

    except Exception as e:
        if isinstance(e, TextCleaningError):
            raise
        raise TextCleaningError(f"Failed to extract parentheticals: {str(e)}") from e


def clean_text(text: str) -> str:
    """Clean text using ftfy and other cleaning methods."""
    try:
        text = fix_text(text)
        text = uncurl_quotes(text)
        return text
    except Exception as e:
        raise TextCleaningError(f"Failed to clean text: {str(e)}") from e


def clean_annotation_text(text: str) -> str:
    """Clean annotation text more thoroughly while preserving newlines."""
    try:
        # First handle any HTML line breaks by converting to newlines
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

        # Initial quote uncurling
        text = uncurl_quotes(text)

        # Split on all possible newline variants
        lines = re.split(r"[\n\r\u2028\u2029]+", text)
        cleaned_lines = []

        for line in lines:
            # Additional text fixes
            line = fix_text(line)

            # Handle punctuation spacing
            patterns = [
                # Fix spacing around punctuation
                (r"\s+([.,!?:;])\s*", r"\1 "),
                # Make sure contractions are tight
                (r"(\w)\s+'(\w)", r"\1'\2"),  # e.g., "don' t" -> "don't"
                (r"(\w)'\s+(\w)", r"\1'\2"),  # e.g., "don 't" -> "don't"
            ]

            for pattern, replacement in patterns:
                line = re.sub(pattern, replacement, line)

            # Clean up extra whitespace within the line only
            line = " ".join(line.split())
            cleaned_lines.append(line)

        # Join lines back together with newlines, preserving empty lines
        return "\n".join(cleaned_lines)

    except Exception as e:
        raise TextCleaningError(f"Failed to clean annotation text: {str(e)}") from e


def clean_fragment(fragment: str) -> str:
    """Clean annotation fragment while preserving newlines."""
    try:
        fragment = uncurl_quotes(fragment)
        fragment = fix_text(fragment)
        fragment = re.sub(r"\[.*?\]", "", fragment)

        lines = re.split(r"[\n\r\u2028\u2029]+", fragment)
        cleaned_lines = []
        for line in lines:
            line = " ".join(line.split())
            if line:  # Only add non-empty lines
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()
    except Exception as e:
        raise TextCleaningError(f"Failed to clean fragment: {str(e)}") from e


def extract_text_from_dom(dom: Dict[str, Any]) -> str:
    """Extract plain text from Genius DOM structure, preserving newlines."""
    try:
        text = []

        def process_node(node: Dict[str, Any]) -> None:
            if isinstance(node, str):
                text.append(node)
            elif isinstance(node, dict):
                # Add newline for block elements
                if node.get("tag") in {"p", "div", "br"}:
                    if text and not text[-1].endswith("\n"):
                        text.append("\n")

                # Process children
                if "children" in node:
                    for child in node["children"]:
                        process_node(child)

                # Add newline after block elements
                if node.get("tag") in {"p", "div"}:
                    if text and not text[-1].endswith("\n"):
                        text.append("\n")

        process_node(dom)
        return "".join(text).strip()
    except Exception as e:
        raise TextCleaningError(f"Failed to extract text from DOM: {str(e)}") from e


def clean_json_array(array_content: str) -> str:
    """Clean array content by removing explanatory text in parentheses."""
    items = []
    current_item = ""
    in_quotes = False

    for char in array_content:
        if char == '"' and (not current_item or current_item[-1] != "\\"):
            in_quotes = not in_quotes
            current_item += char
        elif char == "(" and not in_quotes:
            # Stop collecting when we hit explanatory text
            if current_item:
                items.append(current_item.strip())
            current_item = ""
        elif char == "," and not in_quotes:
            if current_item:
                items.append(current_item.strip())
            current_item = ""
        else:
            current_item += char

    if current_item:
        items.append(current_item.strip())

    # Clean each item and wrap in array
    cleaned_items = []
    for item in items:
        item = item.strip().strip('"')  # Remove quotes and whitespace
        if item:  # Only add non-empty items
            cleaned_items.append(f'"{item}"')

    return f'[{",".join(cleaned_items)}]'


def clean_json_str(json_str: str) -> str:
    """Clean JSON string by handling arrays with explanatory text."""
    # Remove explanatory text in parentheses from arrays
    json_str = re.sub(
        r"\[([^\]]*?)\]", lambda m: clean_json_array(m.group(1)), json_str
    )
    # Remove trailing commas
    json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)
    return json_str


def fix_vocabulary_json(content: str) -> str:
    """Fix common JSON issues in vocabulary responses."""
    if not content:
        return content

    # Try to find the vocabulary array
    vocab_match = re.search(r'"vocabulary":\s*(\[.*?\])', content, re.DOTALL)
    if not vocab_match:
        return content

    vocab_str = vocab_match.group(1)

    # Fix unterminated strings by adding missing quotes
    vocab_str = re.sub(
        r'("[^"]*?)\n', r'\1"', vocab_str
    )  # Fix strings broken by newlines
    vocab_str = re.sub(
        r'("[^"]*?)$', r'\1"', vocab_str
    )  # Fix strings at end of content
    vocab_str = re.sub(
        r'([{,]\s*"[^"]*?)\s*([},])', r'\1"', vocab_str
    )  # Fix unterminated property values
    vocab_str = re.sub(
        r'([{,]\s*[^"\s{},][^:}]*?):', r'"\1":', vocab_str
    )  # Fix unquoted property names

    # Fix missing quotes around property values
    vocab_str = re.sub(r':\s*([^"\s{}\[\],][^,}]*?)([,}])', r': "\1"\2', vocab_str)

    # Fix missing commas between array elements
    vocab_str = re.sub(r"}\s*{", "},{", vocab_str)
    vocab_str = re.sub(r"]\s*\[", "],[", vocab_str)

    # Fix incomplete objects by adding missing closing braces
    open_braces = vocab_str.count("{")
    close_braces = vocab_str.count("}")
    if open_braces > close_braces:
        vocab_str = vocab_str.rstrip() + ("}" * (open_braces - close_braces))

    # Fix incomplete arrays by adding missing closing brackets
    open_brackets = vocab_str.count("[")
    close_brackets = vocab_str.count("]")
    if open_brackets > close_brackets:
        vocab_str = vocab_str.rstrip() + ("]" * (open_brackets - close_brackets))

    # Fix common formatting issues
    vocab_str = vocab_str.replace("\\n", " ")  # Replace newlines in strings
    vocab_str = re.sub(r"\s+", " ", vocab_str)  # Normalize whitespace
    vocab_str = re.sub(r",\s*([}\]])", r"\1", vocab_str)  # Remove trailing commas
    vocab_str = re.sub(
        r'([{,])\s*([^"\s])', r'\1"\2', vocab_str
    )  # Add missing opening quotes

    # Fix truncated objects by ensuring required properties
    required_props = [
        "term",
        "vocabulary_type",
        "definition",
        "usage_notes",
        "variants",
    ]
    for prop in required_props:
        if f'"{prop}"' not in vocab_str.lower():
            # Add missing property before the closing brace
            vocab_str = re.sub(r"}(?=[^}]*$)", f', "{prop}": ""}}', vocab_str)

    # Validate the structure
    try:
        fixed_content = (
            content[: vocab_match.start(1)] + vocab_str + content[vocab_match.end(1) :]
        )
        json.loads(fixed_content)  # Test if valid JSON
        return fixed_content
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON structure: {str(e)}")
        try:
            # More aggressive cleaning
            vocab_str = re.sub(
                r'([^"]),([^"\s])', r'\1, "\2', vocab_str
            )  # Fix unquoted values after commas
            vocab_str = re.sub(
                r'([^"])}', r'\1"}', vocab_str
            )  # Fix missing quotes before closing braces
            vocab_str = re.sub(
                r'([^"])]', r'\1"]', vocab_str
            )  # Fix missing quotes before closing brackets
            fixed_content = (
                content[: vocab_match.start(1)]
                + vocab_str
                + content[vocab_match.end(1) :]
            )
            json.loads(fixed_content)  # Test if valid JSON
            return fixed_content
        except json.JSONDecodeError as e2:
            logger.warning(
                f"Failed to parse JSON even after aggressive cleaning: {str(e2)}"
            )
            return content


def fix_missing_prop(obj_str: str, prop: str) -> str:
    """Add missing property to a JSON object string."""
    if not re.search(f'"{prop}":', obj_str):
        if obj_str.rstrip().endswith("}"):
            return obj_str[:-1] + f', "{prop}": ""' + "}"
        return obj_str + f', "{prop}": ""' + "}"
    return obj_str + "}"


def extract_and_clean_json(content: str) -> Union[Dict[str, Any], str]:
    """Extract and clean JSON from text content."""
    if not content:
        return content

    logger.debug("=== CLEAN JSON START ===")
    logger.debug(f"Raw content type: {type(content)}")
    logger.debug(f"Raw content: {repr(content)}")

    # First try to parse as-is since it might be valid JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.debug("Initial JSON parse failed, trying to clean")

    # Try to extract JSON from markdown code blocks
    json_block_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if json_block_match:
        try:
            json_str = json_block_match.group(1).strip()
            logger.debug(f"Found JSON block: {json_str}")
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from code block: {str(e)}")

    # If no JSON block or parsing failed, try to find any JSON structure
    json_match = re.search(r"(\{[\s\S]*?\})", content)
    if json_match:
        try:
            json_str = json_match.group(1)
            logger.debug(f"Found JSON structure: {json_str}")
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON structure: {str(e)}")
            # Try one more time with more aggressive cleaning
            try:
                # Remove any non-JSON characters
                json_str = re.sub(r'[^\[\]{}",:\s\w\-\'.]', "", json_str)
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to parse JSON even after aggressive cleaning: {str(e)}"
                )

    # If we couldn't parse as JSON, try to fix common issues in vocabulary responses
    try:
        fixed_json = fix_vocabulary_json(content)
        return json.loads(fixed_json)
    except json.JSONDecodeError:
        logger.warning("Failed to fix vocabulary JSON")

    logger.debug("=== CLEAN JSON END ===")
    logger.debug(f"Cleaned content: {repr(content)}")

    # If all parsing attempts fail, return the original content
    return content
