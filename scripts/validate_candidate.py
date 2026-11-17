#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import CATEGORIES, CONFIDENCE, REVIEW_STATUSES, SEVERITIES, STATUSES, ID_PATTERN, load_json, reject_executable_text, validate_source_url, walk_strings


REQUIRED = {
    "id", "title", "summary", "description", "category", "severity", "status",
    "confidence", "targeted_entities", "channels", "indicators", "prevention",
    "victim_actions", "sources", "updated_at", "last_observed_at", "review_due_at",
    "review_status",
}


def validate(path: Path) -> list[str]:
    try:
        document = load_json(path)
    except (OSError, json.JSONDecodeError) as error:
        return [str(error)]
    advisories = document.get("advisories") if isinstance(document, dict) else document
    if not isinstance(advisories, list):
        return ["candidate file must be an array or an object with advisories[]"]
    errors: list[str] = []
    ids: set[str] = set()
    for index, advisory in enumerate(advisories):
        prefix = f"advisories[{index}]"
        if not isinstance(advisory, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = REQUIRED - advisory.keys()
        errors.extend(f"{prefix} missing {field}" for field in sorted(missing))
        identifier = advisory.get("id")
        if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier):
            errors.append(f"{prefix}.id is not a permanent AmanRoid identifier")
        elif identifier in ids:
            errors.append(f"duplicate advisory identifier: {identifier}")
        ids.add(identifier)
        for key, allowed in (("category", CATEGORIES), ("severity", SEVERITIES), ("status", STATUSES), ("confidence", CONFIDENCE), ("review_status", REVIEW_STATUSES)):
            if advisory.get(key) not in allowed:
                errors.append(f"{prefix}.{key} is unsupported")
        sources = advisory.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{prefix}.sources must contain at least one source")
        else:
            for source_index, source in enumerate(sources):
                if not isinstance(source, dict):
                    errors.append(f"{prefix}.sources[{source_index}] must be an object")
                    continue
                try:
                    validate_source_url(source.get("url"), f"{prefix}.sources[{source_index}].url")
                except ValueError as error:
                    errors.append(str(error))
        for field, value in walk_strings(advisory, prefix):
            try:
                reject_executable_text(value, field)
            except ValueError as error:
                errors.append(str(error))
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a local, non-public candidate file")
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    errors = validate(args.candidate)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Valid candidate file: {args.candidate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
