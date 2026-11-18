#!/usr/bin/env python3
"""Validate the static official-organization directory and all country files."""
from __future__ import annotations

import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from common import load_json, parse_timestamp

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = {"JO", "SA", "AE", "PS", "IQ", "EG", "KW", "QA", "BH", "OM", "LB", "SY", "YE", "LY", "TN", "DZ", "MA", "SD", "MR", "SO", "DJ", "KM"}


def validate() -> list[str]:
    errors: list[str] = []
    schema = load_json(ROOT / "schemas/directory.schema.json")
    validator = Draft202012Validator(schema)
    manifest = load_json(ROOT / "directory/manifest.json")
    if manifest.get("schema_version") != 1:
        errors.append("directory manifest schema_version must be 1")
    try:
        parse_timestamp(manifest.get("updated_at"), "directory manifest updated_at")
    except ValueError as error:
        errors.append(str(error))
    entries = manifest.get("countries")
    if not isinstance(entries, list) or {item.get("code") for item in entries} != COUNTRIES:
        errors.append("directory manifest must contain all 22 countries")
        entries = entries if isinstance(entries, list) else []
    ids: set[str] = set()
    for entry in entries:
        code = entry.get("code")
        path = ROOT / str(entry.get("dataset_path", ""))
        if code not in COUNTRIES or not path.is_file():
            errors.append(f"missing directory dataset for {code}")
            continue
        document = load_json(path)
        for error in validator.iter_errors(document):
            errors.append(f"{path.relative_to(ROOT)}: {'/'.join(str(item) for item in error.path)} {error.message}")
        if document.get("country_code") != code:
            errors.append(f"{path.relative_to(ROOT)} country_code mismatch")
        if document.get("coverage_status") != entry.get("coverage_status"):
            errors.append(f"{path.relative_to(ROOT)} coverage_status mismatch")
        for organization in document.get("organizations", []):
            identifier = organization.get("organization_id")
            if identifier in ids:
                errors.append(f"duplicate organization identifier: {identifier}")
            ids.add(identifier)
            if organization.get("publication_status") != "approved":
                errors.append(f"unapproved organization in public directory: {identifier}")
    return sorted(set(errors))


if __name__ == "__main__":
    failures = validate()
    if failures:
        for error in failures:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("Valid official organization directory")
