from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_candidate import validate as validate_candidate  # noqa: E402
from validate_feed import validate as validate_feed  # noqa: E402
from validate_multicountry import validate_manifest  # noqa: E402
from sync_country_feeds import COUNTRIES, check as check_country_sync  # noqa: E402
from validate_security_data import validate_indicators, validate_manifest as validate_security_manifest, validate_organizations  # noqa: E402


def advisory(review_status="approved"):
    return {
        "id": "AMANROID-2026-11-001",
        "title": "تحذير اختباري موثق",
        "summary": "هذا سجل اختبار غير منشور.",
        "description": "وصف اختباري لا يمثل حملة حقيقية.",
        "category": "phishing",
        "severity": "medium",
        "status": "recently_reported",
        "confidence": "medium",
        "targeted_entities": ["مستخدمون في الأردن"],
        "channels": ["رسائل نصية"],
        "indicators": [{"kind": "domain", "value": "example[.]invalid", "defanged": True}],
        "prevention": ["لا تشارك رمز التحقق."],
        "victim_actions": ["تواصل مع الجهة الرسمية."],
        "sources": [{
            "name": "مصدر اختبار",
            "url": "https://example.invalid/advisory",
            "published_at": "2026-11-16T10:00:00Z",
            "evidence_summary": "مصدر اختبار واضح.",
        }],
        "published_at": "2026-11-16T10:00:00Z",
        "updated_at": "2026-11-16T10:00:00Z",
        "last_observed_at": "2026-11-16T10:00:00Z",
        "review_due_at": "2026-12-16T10:00:00Z",
        "review_status": review_status,
    }


def feed(items=None):
    return {
        "schema_version": 1,
        "feed_name": "مركز التحذيرات الأمنية — AmanRoid",
        "language": "ar",
        "country": "JO",
        "feed_version": 1,
        "updated_at": "2026-11-17T14:26:17Z",
        "advisories": items or [],
    }


class PipelineTests(unittest.TestCase):
    def write(self, path: Path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def test_empty_feed_is_valid(self):
        self.assertEqual(validate_feed(ROOT / "advisories.json", ROOT / "schema.json"), [])

    def test_valid_approved_feed_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feed.json"
            self.write(path, feed([advisory()]))
            self.assertEqual(validate_feed(path, ROOT / "schema.json"), [])

    def test_duplicate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feed.json"
            item = advisory()
            self.write(path, feed([item, dict(item)]))
            self.assertTrue(any("duplicate" in error for error in validate_feed(path, ROOT / "schema.json")))

    def test_unapproved_public_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feed.json"
            self.write(path, feed([advisory("draft")]))
            self.assertTrue(any("approved" in error for error in validate_feed(path, ROOT / "schema.json")))

    def test_unsafe_source_and_clickable_indicator_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feed.json"
            item = advisory()
            item["sources"][0]["url"] = "http://unsafe.invalid"
            item["indicators"][0]["value"] = "https://unsafe.invalid"
            self.write(path, feed([item]))
            errors = validate_feed(path, ROOT / "schema.json")
            self.assertTrue(any("HTTPS" in error for error in errors))
            self.assertTrue(any("clickable" in error for error in errors))

    def test_future_advisory_date_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feed.json"
            item = advisory()
            item["updated_at"] = "2026-11-18T00:00:00Z"
            self.write(path, feed([item]))
            self.assertTrue(any("after feed.updated_at" in error for error in validate_feed(path, ROOT / "schema.json")))

    def test_candidate_duplicate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            item = advisory("draft")
            item["published_at"] = None
            self.write(path, {"advisories": [item, dict(item)]})
            self.assertTrue(any("duplicate" in error for error in validate_candidate(path)))

    def test_approval_is_explicit_and_updates_feed(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            candidate = advisory("draft")
            self.write(folder / "candidate.json", {"advisories": [candidate]})
            self.write(folder / "feed.json", feed())
            command = [
                sys.executable, str(ROOT / "scripts/publish_approved.py"),
                "--candidates", str(folder / "candidate.json"),
                "--feed", str(folder / "feed.json"),
                "--approve", candidate["id"],
                "--reviewer", "Test reviewer",
                "--updated-at", "2026-11-17T14:26:17Z",
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(validate_feed(folder / "feed.json", ROOT / "schema.json"), [])
            self.assertEqual(json.loads((folder / "feed.json").read_text())["advisories"][0]["review_status"], "approved")

    def test_no_approval_flag_does_not_publish(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/publish_approved.py"), "--candidates", "missing.json", "--feed", "advisories.json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_manifest_contains_all_supported_countries_with_only_jordan_active(self):
        manifest = json.loads((ROOT / "countries.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {entry["code"] for entry in manifest["countries"]},
            {code for code, _ in COUNTRIES},
        )
        self.assertEqual(
            [entry["code"] for entry in manifest["countries"] if entry["enabled"]],
            ["JO"],
        )
        self.assertEqual(validate_manifest(ROOT / "countries.json"), [])

    def test_country_feeds_are_empty_or_migrated_without_duplicates(self):
        self.assertEqual(check_country_sync(), [])
        self.assertEqual(
            json.loads((ROOT / "feeds/jo.json").read_text(encoding="utf-8")),
            json.loads((ROOT / "advisories.json").read_text(encoding="utf-8")),
        )
        for code, _ in COUNTRIES:
            if code == "JO":
                continue
            feed_path = ROOT / f"feeds/{code.lower()}.json"
            self.assertEqual(json.loads(feed_path.read_text(encoding="utf-8"))["advisories"], [])
        self.assertEqual(
            json.loads((ROOT / "feeds/regional.json").read_text(encoding="utf-8"))["advisories"],
            [],
        )

    def test_public_security_data_is_valid_and_has_no_unreviewed_indicators(self):
        self.assertEqual(validate_indicators(), [])
        self.assertEqual(validate_organizations(), [])
        self.assertEqual(validate_security_manifest(), [])

    def test_security_validator_rejects_unapproved_public_indicator(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            data = {
                "schema_version": 1,
                "feed_name": "test",
                "language": "ar",
                "updated_at": "2026-11-18T00:00:00Z",
                "indicators": [{
                    "id": "AMANROID-URL-2026-001",
                    "indicator_type": "domain",
                    "value": "example.test",
                    "category": "phishing",
                    "confidence": "high",
                    "approval_status": "draft",
                    "withdrawn": False,
                    "evidence_source": "https://example.invalid/evidence"
                }]
            }
            self.write(folder / "data.json", data)
            errors = []
            for item in data["indicators"]:
                if item["approval_status"] != "approved":
                    errors.append(f"public indicator must be approved: {item['id']}")
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
