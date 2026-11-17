#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from common import load_json, save_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Withdraw a public advisory and write a local editorial record")
    parser.add_argument("--feed", type=Path, default=Path("advisories.json"))
    parser.add_argument("--id", required=True)
    parser.add_argument("--log", type=Path, required=True, help="Non-public editorial withdrawal log")
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    feed = load_json(args.feed)
    items = feed.get("advisories", [])
    retained = []
    withdrawn = None
    for item in items:
        if isinstance(item, dict) and item.get("id") == args.id:
            withdrawn = item
        else:
            retained.append(item)
    if withdrawn is None:
        parser.error(f"public advisory not found: {args.id}")
    record = {
        "withdrawn_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reason": args.reason,
        "advisory": withdrawn,
    }
    previous = load_json(args.log) if args.log.exists() else []
    if not isinstance(previous, list):
        parser.error("withdrawal log must be an array")
    previous.append(record)
    save_json(args.log, previous)
    feed["advisories"] = retained
    feed["feed_version"] = int(feed.get("feed_version", 0)) + 1
    feed["updated_at"] = record["withdrawn_at"]
    save_json(args.feed, feed)
    print(f"Withdrawn {args.id}; editorial record written to {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
