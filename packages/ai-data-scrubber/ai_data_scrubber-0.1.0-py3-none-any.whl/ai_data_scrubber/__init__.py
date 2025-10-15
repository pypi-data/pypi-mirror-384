"""AI Data Scrubber - Remove PII from text before uploading to LLMs.

This package provides tools to remove personal information like names, addresses,
email addresses, phone numbers, and URLs from text documents.
"""

from .scrub_text import scrub_text, scrub_file

__version__ = "0.1.0"
__all__ = ["scrub_text", "scrub_file"]

