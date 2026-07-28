"""Reusable text preprocessing shared by model training and inference."""

import html
import re
import unicodedata
from dataclasses import dataclass

URL_TOKEN = "urltoken"
EMAIL_TOKEN = "emailtoken"
PHONE_TOKEN = "phonetoken"

URL_PATTERN = re.compile(r"\b(?:https?://|www\.)[^\s<]+", flags=re.IGNORECASE)
EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])",
    flags=re.UNICODE,
)
PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?62|0)(?:[\s().-]*\d){8,13}(?!\w)",
    flags=re.UNICODE,
)
HTML_TAG_PATTERN = re.compile(r"<[^>]*>")
TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class PreprocessedText:
    """Inspectable output from the canonical preprocessing pipeline."""

    original: str
    cleaned: str
    tokens: tuple[str, ...]


def _replace_control_characters(text: str) -> str:
    return "".join(
        " " if unicodedata.category(character).startswith("C") else character for character in text
    )


def _replace_punctuation(text: str) -> str:
    return "".join(
        character if character.isalnum() or character.isspace() else " " for character in text
    )


def clean_text(text: str) -> str:
    """Normalize and clean Indonesian text without stemming or stopword removal."""

    cleaned = unicodedata.normalize("NFKC", text).lower()
    cleaned = URL_PATTERN.sub(f" {URL_TOKEN} ", cleaned)
    cleaned = EMAIL_PATTERN.sub(f" {EMAIL_TOKEN} ", cleaned)
    cleaned = PHONE_PATTERN.sub(f" {PHONE_TOKEN} ", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = HTML_TAG_PATTERN.sub(" ", cleaned)
    cleaned = _replace_control_characters(cleaned)
    cleaned = _replace_punctuation(cleaned)
    return WHITESPACE_PATTERN.sub(" ", cleaned).strip()


def tokenize_cleaned_text(cleaned_text: str) -> list[str]:
    """Tokenize text that has already passed through :func:`clean_text`."""

    return TOKEN_PATTERN.findall(cleaned_text)


def preprocess_text(text: str) -> PreprocessedText:
    """Return both cleaned text and tokens for inspection or inference."""

    cleaned = clean_text(text)
    return PreprocessedText(
        original=text,
        cleaned=cleaned,
        tokens=tuple(tokenize_cleaned_text(cleaned)),
    )
