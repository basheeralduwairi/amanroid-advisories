from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

MAX_FEED_BYTES = 1024 * 1024
ID_PATTERN = re.compile(r"^AMANROID-[0-9]{4}-[0-9]{2}-[0-9]{3,}$")
DATE_ONLY = re.compile(r"^20[0-9]{2}-[0-9]{2}-[0-9]{2}$")
ISO_DATE = re.compile(r"^20[0-9]{2}-[0-9]{2}-[0-9]{2}T.*Z$")
CATEGORIES = {
    "phishing", "banking_fraud", "ewallet_fraud", "impersonation",
    "malicious_apps", "account_takeover", "investment_fraud",
    "shopping_fraud", "employment_fraud", "ai_fraud", "identity_theft",
    "other",
}
SEVERITIES = {"critical", "high", "medium", "low"}
STATUSES = {"confirmed_active", "recently_reported", "suspected_active", "historical", "resolved"}
CONFIDENCE = {"high", "medium", "low"}
REVIEW_STATUSES = {"draft", "approved", "rejected", "withdrawn"}


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_timestamp(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"{field} is not a valid timestamp: {value}") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{field} must include UTC")
    return parsed


def validate_source_url(value: object, field: str = "url") -> None:
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError(f"{field} must be a bounded string")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"{field} must be an HTTPS URL without credentials")
    if any(character.isspace() for character in value) or "<" in value or ">" in value:
        raise ValueError(f"{field} contains unsafe URL characters")


def reject_executable_text(value: object, field: str) -> None:
    if not isinstance(value, str):
        return
    lowered = value.lower()
    if any(token in lowered for token in ("<script", "javascript:", "data:text/html", "onerror=")):
        raise ValueError(f"{field} contains executable content")
    if "<" in value:
        raise ValueError(f"{field} contains HTML markup")


def walk_strings(value: object, path: str = "feed"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_strings(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value
