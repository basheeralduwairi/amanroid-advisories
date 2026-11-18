#!/usr/bin/env python3
"""Validate public emergency playbook metadata and country contact datasets."""
from __future__ import annotations

import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from common import load_json, parse_timestamp

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = {"JO", "SA", "AE", "PS", "IQ", "EG", "KW", "QA", "BH", "OM", "LB", "SY", "YE", "LY", "TN", "DZ", "MA", "SD", "MR", "SO", "DJ", "KM"}


def validate() -> list[str]:
    errors: list[str] = []
    schema = load_json(ROOT / "schemas/emergency.schema.json")
    validator = Draft202012Validator(schema)
    manifest = load_json(ROOT / "emergency/manifest.json")
    try:
        parse_timestamp(manifest.get("updated_at"), "emergency manifest updated_at")
    except ValueError as error:
        errors.append(str(error))
    entries = manifest.get("countries", [])
    if {entry.get("code") for entry in entries} != COUNTRIES:
        errors.append("emergency manifest must contain all 22 countries")
    playbooks = load_json(ROOT / "emergency/playbooks.json")
    if playbooks.get("schema_version") != 1 or not playbooks.get("playbooks"):
        errors.append("emergency playbooks must contain schema version 1 and entries")
    for entry in entries:
        path = ROOT / str(entry.get("dataset_path", ""))
        if not path.is_file():
            errors.append(f"missing emergency dataset for {entry.get('code')}")
            continue
        document = load_json(path)
        for error in validator.iter_errors(document):
            errors.append(f"{path.relative_to(ROOT)}: {'/'.join(str(item) for item in error.path)} {error.message}")
        if document.get("country_code") != entry.get("code"):
            errors.append(f"{path.relative_to(ROOT)} country_code mismatch")
        if document.get("coverage_status") != entry.get("coverage_status"):
            errors.append(f"{path.relative_to(ROOT)} coverage_status mismatch")
        for contact in document.get("contacts", []):
            if contact.get("publication_status") != "approved":
                errors.append(f"unapproved emergency contact: {contact.get('contact_id')}")
    return sorted(set(errors))


if __name__ == "__main__":
    failures = validate()
    if failures:
        for error in failures:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("Valid emergency guidance datasets")
