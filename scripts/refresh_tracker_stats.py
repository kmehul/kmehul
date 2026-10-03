#!/usr/bin/env python3
"""Read the Apple Music tracker's live numbers into data/tracker.json.

- artists: names in the tracker's artists.txt (blank lines and # comments ignored)
- caught:  entries in its caught.json, one per distinct release that has been emailed

Prints GitHub Actions step outputs on stdout: changed=true|false (numbers differ from
data/tracker.json, so the cards need a rebuild) and heartbeat=true|false (.heartbeat moved
to a new month: a monthly commit keeps GitHub from disabling the hourly schedule after
60 days without repository activity). Exits non-zero, writing nothing, if the tracker
can't be read, so a network blip never zeroes the stats.

Source defaults to the tracker's main branch on GitHub; set TRACKER_SOURCE to a local
checkout to test against it.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "tracker.json"
HEARTBEAT = ROOT / ".heartbeat"
SOURCE = os.environ.get("TRACKER_SOURCE",
                        "https://raw.githubusercontent.com/kmehul/apple-music-release-tracker/main")


def fetch(name):
    if "://" not in SOURCE:
        return (Path(SOURCE) / name).read_text(encoding="utf-8")
    req = urllib.request.Request(f"{SOURCE}/{name}", headers={"User-Agent": "kmehul-profile-stats"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def main():
    try:
        artists = sum(1 for line in fetch("artists.txt").splitlines()
                      if line.strip() and not line.strip().startswith("#"))
        caught = json.loads(fetch("caught.json"))
        assert isinstance(caught, list)
    except Exception as exc:
        print(f"could not read the tracker: {exc}", file=sys.stderr)
        return 1
    stats = {"artists": artists, "caught": len(caught)}
    old = json.loads(DATA.read_text()) if DATA.exists() else None
    changed = stats != old
    if changed:
        DATA.write_text(json.dumps(stats, indent=2) + "\n")
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    heartbeat = not HEARTBEAT.exists() or HEARTBEAT.read_text().strip() != month
    if heartbeat:
        HEARTBEAT.write_text(month + "\n")
    print(f"tracker: {stats} ({'changed' if changed else 'unchanged'})", file=sys.stderr)
    print(f"changed={'true' if changed else 'false'}")
    print(f"heartbeat={'true' if heartbeat else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
