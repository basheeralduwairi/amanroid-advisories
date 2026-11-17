#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from common import load_json, save_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Increment feed_version after an editorial change")
    parser.add_argument("--feed", type=Path, default=Path("advisories.json"))
    parser.add_argument("--updated-at")
    args = parser.parse_args()
    feed = load_json(args.feed)
    if not isinstance(feed, dict):
        parser.error("feed root must be an object")
    feed["feed_version"] = int(feed.get("feed_version", 0)) + 1
    feed["updated_at"] = args.updated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    save_json(args.feed, feed)
    print(f"feed_version={feed['feed_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
