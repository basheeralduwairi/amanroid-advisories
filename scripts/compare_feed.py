#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_json


def ids(value: object) -> set[str]:
    advisories = value.get("advisories", []) if isinstance(value, dict) else []
    return {item.get("id") for item in advisories if isinstance(item, dict) and item.get("id")}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare candidate IDs with the public feed")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--feed", type=Path, default=Path("advisories.json"))
    args = parser.parse_args()
    candidate_ids = ids(load_json(args.candidate))
    feed_ids = ids(load_json(args.feed))
    print(f"new: {len(candidate_ids - feed_ids)}")
    for identifier in sorted(candidate_ids - feed_ids):
        print(f"+ {identifier}")
    print(f"already-present: {len(candidate_ids & feed_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
