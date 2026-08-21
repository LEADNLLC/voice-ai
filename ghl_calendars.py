#!/usr/bin/env python3
"""List the GHL calendars on your location, so you can confirm the exact name.

The app now resolves the booking calendar by NAME (GHL_CALENDAR_NAME). If the name
doesn't match anything, it silently falls back to GHL_CALENDAR_ID, which is the old
Solar Client Calendar. Run this once to confirm the Illinois calendar's real name.

Usage:
    export GHL_API_KEY=your_location_api_key
    export GHL_LOCATION_ID=1Kxb4wuQ087lYbcPdpNm
    python3 ghl_calendars.py
    python3 ghl_calendars.py --match "Illinois Virtual"

Read-only.
"""
import argparse
import os
import sys

try:
    import requests
except ImportError:
    sys.exit("Need requests:  pip3 install requests")

BASE = "https://services.leadconnectorhq.com"
VERSION = "2021-07-28"


def norm(s):
    return (s or "").lower().replace(" ", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=os.environ.get("GHL_API_KEY", ""))
    ap.add_argument("--location", default=os.environ.get("GHL_LOCATION_ID", "1Kxb4wuQ087lYbcPdpNm"))
    ap.add_argument("--match", default="Illinois Virtual",
                    help="name to test resolution against (default: %(default)s)")
    args = ap.parse_args()

    if not args.key:
        sys.exit("❌ No key. Do:  export GHL_API_KEY=your_location_api_key")

    r = requests.get(
        f"{BASE}/calendars/",
        headers={"Authorization": f"Bearer {args.key}", "Version": VERSION,
                 "Content-Type": "application/json"},
        params={"locationId": args.location},
        timeout=30,
    )

    if r.status_code != 200:
        print(f"❌ HTTP {r.status_code}: {r.text[:400]}")
        if r.status_code == 401:
            print("\n   → Key rejected. Use the LOCATION API key (Settings → Business Profile),\n"
                  "     not an agency key.")
        return

    cals = (r.json() or {}).get("calendars", [])
    if not cals:
        print("No calendars on this location.")
        return

    print(f"\n{len(cals)} calendar(s) on location {args.location}:\n")
    for c in cals:
        print(f"  {c.get('name')}")
        print(f"     id        {c.get('id')}")
        if c.get("calendarType"):
            print(f"     type      {c.get('calendarType')}")
        if c.get("timezone"):
            print(f"     timezone  {c.get('timezone')}   <-- the calendar's own timezone")
        print()

    # Replay exactly what ghl_resolve_calendar_id() does
    key = norm(args.match)
    table = {norm(c.get("name")): c for c in cals}
    hit = table.get(key)
    how = "exact"
    if not hit:
        for k, c in table.items():
            if key in k or k in key:
                hit, how = c, "partial"
                break

    print("-" * 62)
    if hit:
        print(f"✅ GHL_CALENDAR_NAME='{args.match}' resolves ({how}) to:")
        print(f"     \"{hit.get('name')}\"  →  {hit.get('id')}")
        if hit.get("timezone"):
            print(f"\n   That calendar's timezone is {hit['timezone']}.")
            print(f"   Set GHL_TIMEZONE to whatever timezone the times Hailey SAYS are in,")
            print(f"   which is the homeowner's local zone, not necessarily the calendar's.")
    else:
        print(f"🚨 GHL_CALENDAR_NAME='{args.match}' matches NOTHING.")
        print("   The app would fall back to GHL_CALENDAR_ID and book onto the wrong calendar.")
        print("   Copy one of the names above into GHL_CALENDAR_NAME exactly.")
    print("-" * 62 + "\n")


if __name__ == "__main__":
    main()
