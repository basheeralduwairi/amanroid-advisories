#!/usr/bin/env python3
"""Generate the country manifest and deterministic country feed skeletons."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from common import load_json, save_json

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = (
    ("JO", "الأردن"), ("SA", "السعودية"), ("AE", "الإمارات"),
    ("PS", "فلسطين"), ("IQ", "العراق"), ("EG", "مصر"),
    ("KW", "الكويت"), ("QA", "قطر"), ("BH", "البحرين"),
    ("OM", "سلطنة عمان"), ("LB", "لبنان"), ("SY", "سوريا"),
    ("YE", "اليمن"), ("LY", "ليبيا"), ("TN", "تونس"),
    ("DZ", "الجزائر"), ("MA", "المغرب"), ("SD", "السودان"),
    ("MR", "موريتانيا"), ("SO", "الصومال"), ("DJ", "جيبوتي"),
    ("KM", "جزر القمر"),
)


def timestamp(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def empty_feed(code: str, updated_at: str) -> dict:
    return {
        "schema_version": 1,
        "feed_name": "مركز التحذيرات الأمنية — AmanRoid",
        "language": "ar",
        "country": code,
        "feed_version": 1,
        "updated_at": updated_at,
        "advisories": [],
    }


def build_manifest(updated_at: str) -> dict:
    return {
        "schema_version": 1,
        "config_version": 1,
        "updated_at": updated_at,
        "default_country": "JO",
        "regional_feed": "feeds/regional.json",
        "countries": [
            {
                "code": code,
                "name_ar": name,
                "enabled": code == "JO",
                "feed_path": f"feeds/{code.lower()}.json",
                "coverage_status": "active" if code == "JO" else "coming_soon",
                "last_reviewed_at": updated_at if code == "JO" else None,
            }
            for code, name in COUNTRIES
        ],
    }


def generate(updated_at: str) -> None:
    legacy = load_json(ROOT / "advisories.json")
    if not isinstance(legacy, dict) or legacy.get("country") != "JO":
        raise SystemExit("advisories.json must remain the Jordanian legacy feed")
    save_json(ROOT / "feeds/jo.json", legacy)
    for code, _ in COUNTRIES:
        if code == "JO":
            continue
        save_json(ROOT / f"feeds/{code.lower()}.json", empty_feed(code, updated_at))
    save_json(ROOT / "feeds/regional.json", empty_feed("REGIONAL", updated_at))
    save_json(ROOT / "countries.json", build_manifest(updated_at))


def check() -> list[str]:
    errors: list[str] = []
    manifest = load_json(ROOT / "countries.json")
    legacy = load_json(ROOT / "advisories.json")
    jo = load_json(ROOT / "feeds/jo.json")
    if legacy != jo:
        errors.append("advisories.json must be identical to feeds/jo.json")
    expected = {code for code, _ in COUNTRIES}
    actual = {item.get("code") for item in manifest.get("countries", [])}
    if actual != expected:
        errors.append("countries.json does not contain exactly the supported country set")
    for code, _ in COUNTRIES:
        path = ROOT / f"feeds/{code.lower()}.json"
        if not path.exists():
            errors.append(f"missing country feed: {path}")
    if not (ROOT / "feeds/regional.json").exists():
        errors.append("missing regional feed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--updated-at")
    args = parser.parse_args()
    if args.write:
        generate(timestamp(args.updated_at))
        print("Generated countries.json and country feed skeletons")
        return 0
    errors = check()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Country feeds are synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
