#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import load_json, save_json


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Explicitly approve selected local candidates into the public feed"
    )
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--feed", type=Path, default=Path("advisories.json"))
    parser.add_argument("--approve", action="append", required=True, help="Permanent ID; repeat for each approved record")
    parser.add_argument("--reviewer", required=True, help="Human reviewer name recorded in the command log")
    parser.add_argument("--updated-at", help="UTC timestamp; defaults to current UTC")
    args = parser.parse_args()
    if not args.reviewer.strip():
        parser.error("--reviewer cannot be empty")
    candidate_document = load_json(args.candidates)
    candidate_items = candidate_document.get("advisories", []) if isinstance(candidate_document, dict) else candidate_document
    feed = load_json(args.feed)
    if not isinstance(candidate_items, list) or not isinstance(feed, dict):
        print("candidate and feed roots are invalid", file=sys.stderr)
        return 1
    existing = {item.get("id") for item in feed.get("advisories", []) if isinstance(item, dict)}
    by_id = {item.get("id"): item for item in candidate_items if isinstance(item, dict)}
    selected = []
    for identifier in args.approve:
        if identifier in existing:
            print(f"refusing duplicate public identifier: {identifier}", file=sys.stderr)
            return 1
        item = by_id.get(identifier)
        if item is None:
            print(f"candidate not found: {identifier}", file=sys.stderr)
            return 1
        if item.get("review_status") != "draft":
            print(f"candidate {identifier} is not a draft", file=sys.stderr)
            return 1
        approved = copy.deepcopy(item)
        if not approved.get("published_at"):
            print(f"candidate {identifier} needs an explicit published_at before approval", file=sys.stderr)
            return 1
        approved["review_status"] = "approved"
        selected.append(approved)
    updated_at = args.updated_at or utc_now()
    feed["feed_version"] = int(feed.get("feed_version", 0)) + 1
    feed["updated_at"] = updated_at
    feed.setdefault("advisories", []).extend(selected)
    save_json(args.feed, feed)
    print(f"Approved {len(selected)} advisory/advisories by {args.reviewer}; feed_version={feed['feed_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
