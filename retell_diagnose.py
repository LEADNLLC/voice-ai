#!/usr/bin/env python3
"""Ask Retell why a call that returned 201 never rang.

A 201 from /v2/create-phone-call only means Retell accepted and queued the call.
Whether it actually dialed is recorded on the call object afterwards, in
call_status + disconnection_reason. This pulls that, plus the state of the
outbound number, and interprets the result.

Usage:
    export RETELL_API_KEY=your_key
    python3 retell_diagnose.py --call call_86d368e9dd27d9901ff4f8eb034
    python3 retell_diagnose.py --numbers
    python3 retell_diagnose.py --call <id> --number +17027105676

Nothing is modified. Read-only GETs.
"""
import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    sys.exit("Need requests:  pip3 install requests")

BASE = "https://api.retellai.com"

# What each disconnection_reason actually means for "the phone never rang"
REASONS = {
    "dial_failed": (
        "The carrier refused the dial outright. The call never reached the network.",
        "Almost always the FROM number: not fully provisioned, not attached to an\n"
        "     outbound-capable agent, or removed from the account. Check --numbers below.",
    ),
    "dial_busy": ("Destination returned busy.", "Try a different test handset."),
    "dial_no_answer": (
        "It DID ring and nobody picked up.",
        "If your phone never lit up, the carrier likely silently dropped it —\n"
        "     see the spam-labeling note at the bottom.",
    ),
    "marked_as_spam": (
        "The carrier flagged the caller ID as spam and suppressed the call.",
        "This is the classic silent no-ring. Needs SHAKEN/STIR attestation or a\n"
        "     different number. A brand-new number with no traffic history is prime for this.",
    ),
    "scam_detected": (
        "Carrier scam-blocked the caller ID.",
        "Same remedy as marked_as_spam.",
    ),
    "error_retell": ("Retell-side internal error.", "Retry; if it repeats, open a Retell support ticket."),
    "invalid_destination": ("Destination number rejected as invalid.", "Check E.164 formatting on the TO number."),
    "user_hangup": ("Callee hung up.", "The call connected — this is not a routing failure."),
    "agent_hangup": ("Agent ended the call.", "The call connected."),
    "voicemail_reached": ("Went to voicemail.", "The call connected."),
    "inactivity": ("Ended on silence timeout.", "The call connected."),
}


def get(path, key):
    r = requests.get(f"{BASE}{path}", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    return r.status_code, (r.json() if r.text.strip().startswith(("{", "[")) else r.text)


def show_call(call_id, key):
    print(f"\n{'='*70}\n  CALL  {call_id}\n{'='*70}")
    code, body = get(f"/v2/get-call/{call_id}", key)
    if code != 200:
        print(f"❌ HTTP {code}: {body}")
        if code == 401:
            print("\n   → The key in RETELL_API_KEY is wrong or revoked.")
        elif code == 404:
            print("\n   → No such call on THIS account. If you rotated keys or have more\n"
                  "     than one Retell account, the call may live on the other one.")
        return

    status = body.get("call_status")
    reason = body.get("disconnection_reason")

    for label, val in [
        ("call_status", status),
        ("disconnection_reason", reason),
        ("from_number", body.get("from_number")),
        ("to_number", body.get("to_number")),
        ("agent_id", body.get("agent_id")),
        ("direction", body.get("direction")),
        ("duration_ms", body.get("duration_ms")),
        ("start / end", f"{body.get('start_timestamp')} → {body.get('end_timestamp')}"),
    ]:
        print(f"  {label:<22} {val}")

    if body.get("transcript"):
        print(f"  {'transcript':<22} {len(body['transcript'])} chars (call connected and talked)")

    print(f"\n{'-'*70}\n  DIAGNOSIS\n{'-'*70}")

    if status == "ended" and body.get("duration_ms"):
        print("  ✅ This call connected and ran. Not a routing problem.")
    elif status in ("registered",):
        print("  ⏳ Still 'registered' — Retell queued it but hasn't dialed yet, or it\n"
              "     died before dialing. Re-run in ~30s; if it stays here, it never dialed.")
    elif status == "not_connected":
        print("  ❌ Never connected — Retell tried to dial and the network refused.")
    elif status == "error":
        print("  ❌ Retell errored on this call.")

    if reason:
        meaning, remedy = REASONS.get(reason, ("Unrecognized reason.", "Check Retell's call detail page."))
        print(f"\n  reason: {reason}")
        print(f"     {meaning}")
        print(f"  → {remedy}")
    elif status != "ended":
        print("\n  No disconnection_reason set. That usually means it never got far enough\n"
              "  to dial at all — point the finger at the FROM number.")


def show_numbers(key, want=None):
    print(f"\n{'='*70}\n  PHONE NUMBERS ON THIS ACCOUNT\n{'='*70}")
    code, body = get("/list-phone-numbers", key)
    if code != 200:
        print(f"❌ HTTP {code}: {body}")
        return
    if not body:
        print("  (none) — this account owns no numbers. That alone explains a failed dial.")
        return

    found = False
    for n in body:
        num = n.get("phone_number")
        mark = ""
        if want and num == want:
            found = True
            mark = "   <-- the number your app is calling FROM"
        print(f"\n  {num}{mark}")
        print(f"     type            {n.get('phone_number_type')}")
        print(f"     outbound agent  {n.get('outbound_agent_id') or '⚠️  NONE SET'}")
        print(f"     inbound agent   {n.get('inbound_agent_id') or '(none)'}")
        if n.get("last_modification_timestamp"):
            print(f"     modified        {n.get('last_modification_timestamp')}")

    if want and not found:
        print(f"\n  🚨 {want} is NOT on this account.")
        print("     Your app dials FROM a number Retell doesn't own here. Retell may accept\n"
              "     the request (201) and then fail to dial. This would explain both the\n"
              "     silent no-ring AND the a2p-application 404 on SMS.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--call", help="call_id from your logs")
    ap.add_argument("--number", help="outbound number to check, E.164")
    ap.add_argument("--numbers", action="store_true", help="list all numbers")
    ap.add_argument("--key", default=os.environ.get("RETELL_API_KEY", ""))
    args = ap.parse_args()

    if not args.key:
        sys.exit("❌ No key. Do:  export RETELL_API_KEY=your_key")
    if not (args.call or args.numbers or args.number):
        sys.exit("Nothing to do. Pass --call and/or --numbers.")

    if args.call:
        show_call(args.call, args.key)
    if args.numbers or args.number:
        show_numbers(args.key, args.number)

    print(f"\n{'='*70}")
    print("  If the number checks out and the reason is marked_as_spam / dial_no_answer,")
    print("  the carrier is suppressing a brand-new Vegas number calling a Vegas cell.")
    print("  A 303/720 Denver number plus SHAKEN/STIR attestation is the durable fix.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
