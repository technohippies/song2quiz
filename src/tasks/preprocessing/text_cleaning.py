"""Prefect tasks for text cleaning operations."""
import json
import logging
from pathlib import Path

from prefect import task

from src.utils.cleaning.text import (
    TextCleaningError,
    clean_annotation_text,
    clean_fragment,
    extract_text_from_dom,
)

logger = logging.getLogger(__name__)

@task(name="process_annotations")
def process_annotations(song_path: Path) -> bool:
    """Process and clean annotations for a song."""
    try:
        input_file = song_path / "genius_annotations.json"
        if not input_file.exists():
            logger.warning(f"No annotations found at {input_file}")
            return False

        with open(input_file) as f:
            annotations = json.load(f)

        cleaned_annotations = []
        for ann in annotations:
            try:
                raw_text = extract_text_from_dom(ann['annotations'][0]['body']['dom'])
                annotation_text = clean_annotation_text(raw_text)
                fragment = clean_fragment(ann["fragment"])

                # Skip empty or very short annotations
                if len(annotation_text) < 5 or len(fragment) < 3:
                    logger.debug(f"Skipping short annotation: {fragment[:20]}...")
                    continue

                cleaned_ann = {
                    "id": ann["id"],
                    "fragment": fragment,
                    "annotation_text": annotation_text
                }
                cleaned_annotations.append(cleaned_ann)

            except TextCleaningError as e:
                logger.warning(f"Failed to clean annotation {ann['id']}: {e}")
                continue  # Skip this annotation but continue processing others

        output_file = song_path / "annotations_cleaned.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_annotations, f, ensure_ascii=False, indent=2)

        logger.info(f"Processed {len(cleaned_annotations)} annotations for {song_path.name}")
        return True

    except Exception as e:
        logger.error(f"Error processing {song_path}: {str(e)}")
        return False
