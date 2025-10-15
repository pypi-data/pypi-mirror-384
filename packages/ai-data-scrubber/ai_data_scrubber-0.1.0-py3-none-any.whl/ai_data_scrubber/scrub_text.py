#!/usr/bin/env python3
"""
Text Scrubbing Script

This script removes personal information (names, addresses, email addresses)
from text files to clean sensitive documents like resumes.
Uses spaCy NER for improved name detection.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple
import spacy
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global spaCy model instance
SPACY_MODEL = "en_core_web_lg"
_nlp = None


def get_spacy_model():
    """Get or load spaCy model for NER."""
    global _nlp

    if _nlp is None:
        try:
            _nlp = spacy.load(SPACY_MODEL)
            logger.info(f"Loaded spaCy model: {SPACY_MODEL}")
        except OSError:
            raise RuntimeError(
                f"spaCy model '{SPACY_MODEL}' not found. "
                f"Install it with: python -m spacy download {SPACY_MODEL}"
            )

    return _nlp


def create_regex_patterns() -> List[Tuple[str, str]]:
    """Create regex patterns for detecting personal information."""
    patterns = [
        # Email addresses
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
        # URLs
        (r'\bhttps?://[^\s<>"{}|\\^`\[\]]+', "[URL]"),
        (r'\bwww\.[^\s<>"{}|\\^`\[\]]+', "[URL]"),
        (
            r'\b[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.[A-Za-z]{2,}(?:/[^\s<>"{}|\\^`\[\]]*)?',
            "[URL]",
        ),
        # Phone numbers (various formats)
        (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]"),
        (r"\(\d{3}\)\s*\d{3}[-.]?\d{4}\b", "[PHONE]"),
        (r"\(\d{3}\)\s+\d{3}[-.]?\d{4}\b", "[PHONE]"),
        (r"\b\d{3}\s\d{3}\s\d{4}\b", "[PHONE]"),
        (r"\(\d{3}\)\s*\d{3}\s\d{4}\b", "[PHONE]"),
        # US Street Addresses (must end with street type to avoid false positives)
        (
            r"\b\d+\s+(?:N|S|E|W|NE|NW|SE|SW|North|South|East|West|Northeast|Northwest|Southeast|Southwest)?\s*[A-Za-z]+(?:\s+[A-Za-z]+)*\s+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd|court|ct|place|pl|way|circle|cir|terrace|ter|parkway|pkwy|highway|hwy|expressway|expy|freeway|fwy|real)(?:\s+(?:N|S|E|W|NE|NW|SE|SW|North|South|East|West|Northeast|Northwest|Southeast|Southwest))?\b",
            "[ADDRESS]",
        ),
        # Additional address pattern for cases without directional prefixes
        (
            r"\b\d+\s+[A-Za-z]+(?:\s+[A-Za-z]+)*\s+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd|court|ct|place|pl|way|circle|cir|terrace|ter|parkway|pkwy|highway|hwy|expressway|expy|freeway|fwy|real)(?:\s+(?:N|S|E|W|NE|NW|SE|SW|North|South|East|West|Northeast|Northwest|Southeast|Southwest))?\b",
            "[ADDRESS]",
        ),
        # Address pattern for ordinal numbers (1st, 2nd, 3rd, 4th, 5th, etc.)
        (
            r"\b\d+\s+\d+(?:st|nd|rd|th)\s+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd|court|ct|place|pl|way|circle|cir|terrace|ter|parkway|pkwy|highway|hwy|expressway|expy|freeway|fwy|real)(?:\s+(?:N|S|E|W|NE|NW|SE|SW|North|South|East|West|Northeast|Northwest|Southeast|Southwest))?\b",
            "[ADDRESS]",
        ),
        # Address pattern for directional prefix + ordinal numbers (E 5th Avenue, N 1st Street, etc.)
        (
            r"\b\d+\s+(?:N|S|E|W|NE|NW|SE|SW|North|South|East|West|Northeast|Northwest|Southeast|Southwest)\s+\d+(?:st|nd|rd|th)\s+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd|court|ct|place|pl|way|circle|cir|terrace|ter|parkway|pkwy|highway|hwy|expressway|expy|freeway|fwy|real)(?:\s+(?:N|S|E|W|NE|NW|SE|SW|North|South|East|West|Northeast|Northwest|Southeast|Southwest))?\b",
            "[ADDRESS]",
        ),
        # Address pattern for directional prefix + street name (S Broadway, N Main, etc.)
        (
            r"\b\d+\s+(?:N|S|E|W|NE|NW|SE|SW|North|South|East|West|Northeast|Northwest|Southeast|Southwest)\s+[A-Za-z]+(?:\s+[A-Za-z]+)*\b",
            "[ADDRESS]",
        ),
        # Apartment/Unit numbers
        (
            r"\b(?:apt|apartment|unit(?![a-z])|suite(?![a-z])|ste(?![a-z])|#)\s*[A-Za-z0-9]+\b",
            "[UNIT]",
        ),
        # ZIP codes
        (r"\b\d{5}(?:-\d{4})?\b", "[ZIP_CODE]"),
        # US License plates (capital letters + digits only, like ARY6056 or A1BC12, 5-8 characters)
        (r"\b(?=.*[A-Z])(?=.*\d)[A-Z\d]{5,8}\b", "[LICENSE_PLATE]"),
    ]
    return patterns


def scrub_with_spacy(text: str) -> str:
    """Use spaCy NER to scrub names only."""
    nlp = get_spacy_model()

    # Process the text with spaCy
    doc = nlp(text)

    # Create a list of spans to replace
    replacements = []

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            replacements.append((ent.start_char, ent.end_char, "[NAME]"))

    # Sort replacements by start position (reverse order to avoid index shifting)
    replacements.sort(key=lambda x: x[0], reverse=True)

    # Apply replacements
    result = text
    for start, end, replacement in replacements:
        result = result[:start] + replacement + result[end:]

    return result


def scrub_text(text: str) -> str:
    """Scrub personal information in text."""
    logger.debug(f"Starting text scrubbing (text length: {len(text)} characters)")

    # Get regex patterns for structured data (including addresses)
    patterns = create_regex_patterns()

    # Apply regex patterns first (for emails, phones, SSNs, addresses, etc.)
    replacements_made = 0
    for pattern, replacement in patterns:
        if replacement == "[LICENSE_PLATE]":
            # License plate pattern should be case-sensitive
            before_count = len(re.findall(pattern, text))
            text = re.sub(pattern, replacement, text)
            replacements_made += before_count
        else:
            # Other patterns can be case-insensitive
            before_count = len(re.findall(pattern, text, flags=re.IGNORECASE))
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            replacements_made += before_count

    logger.debug(f"Applied regex patterns: {replacements_made} replacements made")

    # Use spaCy for names only
    logger.debug("Applying spaCy NER for name detection")
    text = scrub_with_spacy(text)
    logger.debug("Text scrubbing completed")

    return text


def scrub_file(input_file: str, output_file: str = None) -> None:
    """Process a single file and save scrubbed version."""
    if output_file is None:
        # Create output filename with _scrubbed suffix
        input_path = Path(input_file)
        output_file = str(
            input_path.parent / f"{input_path.stem}_scrubbed{input_path.suffix}"
        )

    try:
        # Read input file
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

        logger.info(f"Processing {input_file}...")

        # Scrub content
        scrubbed_content = scrub_text(content)

        # Write output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(scrubbed_content)

        logger.info(f"Scrubbed content saved to {output_file}")

    except FileNotFoundError:
        logger.error(f"File {input_file} not found.")
    except Exception as e:
        logger.error(f"Error processing {input_file}: {e}")


def main():
    """Command line interface for the scrubbing script."""
    parser = argparse.ArgumentParser(
        description="Scrub personal information from text files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input_file", help="Input file to scrub")

    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Output file (default: input_file_scrubbed.ext)",
    )

    args = parser.parse_args()

    # Validate input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Input file '{args.input_file}' does not exist.")
        sys.exit(1)

    if not input_path.is_file():
        logger.error(f"'{args.input_file}' is not a file.")
        sys.exit(1)

    # Process the file
    scrub_file(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
