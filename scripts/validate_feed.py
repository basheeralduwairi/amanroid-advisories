#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import (
    CATEGORIES,
    MAX_FEED_BYTES,
    REVIEW_STATUSES,
    SEVERITIES,
    STATUSES,
    CONFIDENCE,
    load_json,
    parse_timestamp,
    reject_executable_text,
    validate_source_url,
    walk_strings,
)


def validate(path: Path, schema_path: Path) -> list[str]:
    errors: list[str] = []
    if path.stat().st_size > MAX_FEED_BYTES:
        errors.append(f"feed exceeds {MAX_FEED_BYTES} bytes")
    try:
        document = load_json(path)
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot parse {path}: {error}"]
    if not isinstance(document, dict):
        return ["feed root must be an object"]

    try:
        import jsonschema
        from jsonschema import FormatChecker

        schema = load_json(schema_path)
        validator = jsonschema.Draft202012Validator(schema, format_checker=FormatChecker())
        errors.extend(error.message for error in validator.iter_errors(document))
    except ImportError:
        errors.append("jsonschema is required; install requirements-dev.txt")
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"cannot load schema: {error}")

    try:
        feed_updated = parse_timestamp(document.get("updated_at"), "updated_at")
    except ValueError as error:
        errors.append(str(error))
        feed_updated = None
    advisories = document.get("advisories", [])
    identifiers: set[str] = set()
    if isinstance(advisories, list):
        for index, advisory in enumerate(advisories):
            prefix = f"advisories[{index}]"
            if not isinstance(advisory, dict):
                errors.append(f"{prefix} must be an object")
                continue
            identifier = advisory.get("id")
            if identifier in identifiers:
                errors.append(f"duplicate advisory identifier: {identifier}")
            identifiers.add(identifier)
            if advisory.get("review_status") != "approved":
                errors.append(f"{prefix}.review_status must be approved for public feed")
            if advisory.get("category") not in CATEGORIES:
                errors.append(f"{prefix}.category is unsupported")
            if advisory.get("severity") not in SEVERITIES:
                errors.append(f"{prefix}.severity is unsupported")
            if advisory.get("status") not in STATUSES:
                errors.append(f"{prefix}.status is unsupported")
            if advisory.get("confidence") not in CONFIDENCE:
                errors.append(f"{prefix}.confidence is unsupported")
            for key in ("published_at", "updated_at", "last_observed_at", "review_due_at"):
                try:
                    value = parse_timestamp(advisory.get(key), f"{prefix}.{key}")
                    if feed_updated and key != "review_due_at" and value > feed_updated:
                        errors.append(f"{prefix}.{key} cannot be after feed.updated_at")
                except ValueError as error:
                    errors.append(str(error))
            if feed_updated:
                try:
                    due = parse_timestamp(advisory.get("review_due_at"), f"{prefix}.review_due_at")
                    if due < feed_updated:
                        errors.append(f"{prefix}.review_due_at is before feed.updated_at")
                except ValueError:
                    pass
            sources = advisory.get("sources", [])
            if not isinstance(sources, list) or not sources:
                errors.append(f"{prefix}.sources must contain at least one source")
            else:
                for source_index, source in enumerate(sources):
                    if isinstance(source, dict):
                        try:
                            validate_source_url(source.get("url"), f"{prefix}.sources[{source_index}].url")
                        except ValueError as error:
                            errors.append(str(error))
                        try:
                            source_date = parse_timestamp(
                                source.get("published_at"),
                                f"{prefix}.sources[{source_index}].published_at",
                            )
                            if feed_updated and source_date > feed_updated:
                                errors.append(f"{prefix}.sources[{source_index}].published_at is in the future")
                        except ValueError as error:
                            errors.append(str(error))
            for indicator_index, indicator in enumerate(advisory.get("indicators", [])):
                if isinstance(indicator, dict):
                    if indicator.get("defanged") is not True:
                        errors.append(f"{prefix}.indicators[{indicator_index}] must be defanged")
                    value = indicator.get("value", "")
                    if isinstance(value, str) and ("http://" in value.lower() or "https://" in value.lower()):
                        errors.append(f"{prefix}.indicators[{indicator_index}] contains a clickable URL")

    for field, value in walk_strings(document):
        try:
            reject_executable_text(value, field)
        except ValueError as error:
            errors.append(str(error))
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the public AmanRoid advisory feed")
    parser.add_argument("--feed", type=Path, default=Path("advisories.json"))
    parser.add_argument("--schema", type=Path, default=Path("schema.json"))
    args = parser.parse_args()
    errors = validate(args.feed, args.schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Valid public feed: {args.feed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
