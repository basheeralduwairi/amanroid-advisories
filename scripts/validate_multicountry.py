#!/usr/bin/env python3
"""Validate the remote country manifest and every public feed."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import load_json, parse_timestamp, validate_source_url
from sync_country_feeds import COUNTRIES, check
from validate_feed import validate

ROOT = Path(__file__).resolve().parents[1]
STATUS = {"active", "coming_soon", "temporarily_unavailable"}


def validate_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    document = load_json(path)
    if document.get("schema_version") != 1:
        errors.append("countries.schema_version must be 1")
    if not isinstance(document.get("config_version"), int) or document["config_version"] < 1:
        errors.append("countries.config_version must be positive")
    try:
        parse_timestamp(document.get("updated_at"), "countries.updated_at")
    except ValueError as error:
        errors.append(str(error))
    if document.get("default_country") != "JO":
        errors.append("countries.default_country must be JO")
    regional = document.get("regional_feed")
    if not isinstance(regional, str) or not regional.startswith("feeds/") or ".." in regional:
        errors.append("countries.regional_feed must be a safe relative feed path")
    expected = {code for code, _ in COUNTRIES}
    entries = document.get("countries")
    if not isinstance(entries, list) or {item.get("code") for item in entries} != expected:
        errors.append("countries must contain exactly the supported country codes")
    else:
        for item in entries:
            code = item.get("code")
            if not isinstance(item.get("name_ar"), str) or not item["name_ar"].strip():
                errors.append(f"{code}.name_ar is required")
            if not isinstance(item.get("enabled"), bool):
                errors.append(f"{code}.enabled must be boolean")
            feed_path = item.get("feed_path")
            if not isinstance(feed_path, str) or not feed_path.startswith("feeds/") or ".." in feed_path or ":" in feed_path:
                errors.append(f"{code}.feed_path is unsafe")
            if item.get("coverage_status") not in STATUS:
                errors.append(f"{code}.coverage_status is unsupported")
            reviewed = item.get("last_reviewed_at")
            if reviewed is not None:
                try:
                    parse_timestamp(reviewed, f"{code}.last_reviewed_at")
                except ValueError as error:
                    errors.append(str(error))
            enabled = item.get("enabled") is True
            active = item.get("coverage_status") == "active"
            if enabled != active:
                errors.append(f"{code}.enabled must match active coverage_status")
            if active and reviewed is None:
                errors.append(f"{code}.last_reviewed_at is required for active coverage")
            if code == "JO" and not active:
                errors.append("Jordan must remain active")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, default=ROOT / "schema.json")
    args = parser.parse_args()
    errors = check()
    errors.extend(validate_manifest(ROOT / "countries.json"))
    identifiers: set[str] = set()
    for code, _ in COUNTRIES:
        path = ROOT / f"feeds/{code.lower()}.json"
        for error in validate(path, args.schema):
            errors.append(f"{path.relative_to(ROOT)}: {error}")
        for advisory in load_json(path).get("advisories", []):
            identifier = advisory.get("id")
            if identifier in identifiers:
                errors.append(f"duplicate advisory identifier across feeds: {identifier}")
            identifiers.add(identifier)
    regional_path = ROOT / "feeds/regional.json"
    for error in validate(regional_path, args.schema):
        errors.append(f"feeds/regional.json: {error}")
    for advisory in load_json(regional_path).get("advisories", []):
        identifier = advisory.get("id")
        if identifier in identifiers:
            errors.append(f"duplicate advisory identifier across feeds: {identifier}")
        identifiers.add(identifier)
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Valid multi-country manifest and feeds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
