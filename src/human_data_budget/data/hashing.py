"""Stable normalized content hashes for pre-split overlap checks."""

import hashlib
import unicodedata


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    return " ".join(normalized.split()).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()
