#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from common import load_json, parse_timestamp


def main() -> int:
    parser = argparse.ArgumentParser(description="List approved advisories due for expert review")
    parser.add_argument("--feed", type=Path, default=Path("advisories.json"))
    parser.add_argument("--as-of", help="UTC timestamp for deterministic checks")
    args = parser.parse_args()
    as_of = parse_timestamp(args.as_of, "--as-of") if args.as_of else datetime.now(timezone.utc)
    feed = load_json(args.feed)
    due = []
    for advisory in feed.get("advisories", []):
        if not isinstance(advisory, dict) or advisory.get("review_status") != "approved":
            continue
        try:
            review_due = parse_timestamp(advisory["review_due_at"], "review_due_at")
        except (KeyError, ValueError):
            continue
        if review_due <= as_of:
            due.append(advisory["id"])
    if due:
        print("\n".join(sorted(due)))
        return 1
    print("No approved advisories are overdue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
