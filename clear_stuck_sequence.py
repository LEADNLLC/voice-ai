#!/usr/bin/env python3
"""Clear a stuck 'active' row in call_sequences so a lead can be re-enrolled.

This is what produces the "Sequence already active for this lead" block
(voice_app.py: schedule_call_sequence -> line ~3884, and the API handlers
that surface the same message).

Usage:
    python3 clear_stuck_sequence.py --list
    python3 clear_stuck_sequence.py --phone 7025551234
    python3 clear_stuck_sequence.py --phone 7025551234 --apply

Runs a dry run by default. Nothing is written until you pass --apply.
Point it at the live DB with --db or the DB_PATH env var.
"""
import argparse
import os
import re
import sqlite3
import sys

DEFAULT_DB = os.environ.get("DB_PATH", os.path.expanduser("~/voice.db"))


def digits(value):
    """Last 10 digits, so +1 / dashes / parens all compare equal."""
    return re.sub(r"\D", "", value or "")[-10:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB, help=f"SQLite path (default {DEFAULT_DB})")
    ap.add_argument("--phone", help="Lead phone; any format, matched on last 10 digits")
    ap.add_argument("--list", action="store_true", help="Show all active sequences and exit")
    ap.add_argument("--apply", action="store_true", help="Actually write the change")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        sys.exit(f"❌ No database at {args.db}\n   Set --db or DB_PATH to the live file.")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    rows = c.execute(
        "SELECT id, lead_id, phone, first_name, agent_type, status, current_day, "
        "calls_made, created_at FROM call_sequences WHERE status = 'active'"
    ).fetchall()

    if args.list or not args.phone:
        if not rows:
            print("No active sequences.")
        else:
            print(f"{len(rows)} active sequence(s):\n")
            for r in rows:
                print(f"  id={r['id']:<5} {r['phone']:<16} {r['first_name'] or '(no name)':<14} "
                      f"agent={r['agent_type'] or '-':<8} day={r['current_day']} "
                      f"calls={r['calls_made']}  created={r['created_at']}")
        if not args.phone:
            print("\nRe-run with --phone <number> to clear one.")
        conn.close()
        return

    target = digits(args.phone)
    if len(target) != 10:
        sys.exit(f"❌ '{args.phone}' doesn't look like a 10-digit US number.")

    matches = [r for r in rows if digits(r["phone"]) == target]
    if not matches:
        print(f"No active sequence for {args.phone}. Nothing to clear.")
        conn.close()
        return

    print(f"Matched {len(matches)} active sequence(s) for {args.phone}:\n")
    for r in matches:
        print(f"  id={r['id']}  {r['phone']}  {r['first_name'] or '(no name)'}  "
              f"agent={r['agent_type']}  day={r['current_day']}  calls={r['calls_made']}")

    if not args.apply:
        print("\n🔍 Dry run — nothing written. Re-run with --apply to clear.")
        conn.close()
        return

    ids = [r["id"] for r in matches]
    c.executemany(
        "UPDATE call_sequences SET status = 'cancelled' WHERE id = ?",
        [(i,) for i in ids],
    )
    conn.commit()
    print(f"\n✅ Cleared {c.rowcount if c.rowcount != -1 else len(ids)} sequence(s): {ids}")
    print("   The lead can now be re-enrolled.")
    conn.close()


if __name__ == "__main__":
    main()
