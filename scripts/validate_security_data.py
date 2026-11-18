#!/usr/bin/env python3
"""Validate the public, non-sensitive URL security data files."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

from common import load_json, parse_timestamp, validate_source_url

ROOT = Path(__file__).resolve().parents[1]
SECURITY = ROOT / "security"
SCHEMAS = ROOT / "schemas"
ID_PATTERN = re.compile(r"^AMANROID-URL-[0-9]{4}-[0-9]{3,}$")
COUNTRIES = {"ALL", "JO", "SA", "AE", "PS", "IQ", "EG", "KW", "QA", "BH", "OM", "LB", "SY", "YE", "LY", "TN", "DZ", "MA", "SD", "MR", "SO", "DJ", "KM"}


def schema_errors(document: object, schema_path: Path) -> list[str]:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [error.message for error in validator.iter_errors(document)]


def validate_indicators() -> list[str]:
    path = SECURITY / "url-indicators.json"
    document = load_json(path)
    errors = [f"url-indicators.json: {error}" for error in schema_errors(document, SCHEMAS / "url-indicators.schema.json")]
    identifiers: set[str] = set()
    for indicator in document.get("indicators", []):
        identifier = indicator.get("id")
        if identifier in identifiers:
            errors.append(f"duplicate indicator identifier: {identifier}")
        identifiers.add(identifier)
        if not ID_PATTERN.fullmatch(identifier or ""):
            errors.append(f"invalid indicator identifier: {identifier}")
        if indicator.get("approval_status") != "approved" or indicator.get("withdrawn") is True:
            errors.append(f"public indicator must be approved and not withdrawn: {identifier}")
        value = indicator.get("value", "")
        if any(ord(character) < 0x20 for character in value):
            errors.append(f"indicator contains control characters: {identifier}")
        if indicator.get("indicator_type") == "exact_url":
            parsed = urlsplit(value)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                errors.append(f"exact_url must be an HTTPS URL without credentials: {identifier}")
        elif "/" in value or ":" in value or "@" in value:
            errors.append(f"hostname/domain indicator must not contain URL syntax: {identifier}")
        for key in ("first_observed_at", "last_observed_at", "expires_at", "review_due_at"):
            if key in indicator:
                try:
                    parse_timestamp(indicator[key], f"{identifier}.{key}")
                except ValueError as error:
                    errors.append(str(error))
        try:
            validate_source_url(indicator.get("evidence_source"), f"{identifier}.evidence_source")
        except ValueError as error:
            errors.append(str(error))
    return errors


def validate_organizations() -> list[str]:
    path = SECURITY / "trusted-organizations.json"
    document = load_json(path)
    errors = [f"trusted-organizations.json: {error}" for error in schema_errors(document, SCHEMAS / "trusted-organizations.schema.json")]
    identifiers: set[str] = set()
    domains: set[str] = set()
    for organization in document.get("organizations", []):
        identifier = organization.get("organization_id")
        if identifier in identifiers:
            errors.append(f"duplicate organization identifier: {identifier}")
        identifiers.add(identifier)
        for country in organization.get("countries", []):
            if country not in COUNTRIES:
                errors.append(f"unsupported organization country: {identifier}/{country}")
        for domain in organization.get("official_domains", []):
            if domain != domain.lower() or domain.startswith(".") or domain.endswith(".") or ".." in domain:
                errors.append(f"non-canonical official domain: {identifier}/{domain}")
            if domain in domains:
                errors.append(f"duplicate official domain: {domain}")
            domains.add(domain)
        try:
            validate_source_url(organization.get("verification_source"), f"{identifier}.verification_source")
        except ValueError as error:
            errors.append(str(error))
        for key in ("verified_at", "review_due_at"):
            try:
                parse_timestamp(organization.get(key), f"{identifier}.{key}")
            except ValueError as error:
                errors.append(str(error))
    return errors


def validate_manifest() -> list[str]:
    path = SECURITY / "security-data-manifest.json"
    document = load_json(path)
    errors = [f"security-data-manifest.json: {error}" for error in schema_errors(document, SCHEMAS / "security-data-manifest.schema.json")]
    for field in ("indicators_path", "trusted_organizations_path"):
        relative = document.get(field)
        if not isinstance(relative, str) or relative.startswith("/") or ".." in relative:
            errors.append(f"unsafe manifest path: {field}")
        elif not (ROOT / relative).is_file():
            errors.append(f"manifest path does not exist: {relative}")
    return errors


def main() -> int:
    errors = validate_indicators() + validate_organizations() + validate_manifest()
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Valid public security data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
