# voicelab — routing is fixed; the failure moved downstream

## ✅ What's now working

```
📥 agent_type resolved: 'solar'
🔍 AGENT TYPE RECEIVED: 'solar'
✅ USING SOLAR CLIENT AGENT: agent_51e1e8bbc32e11ce5d2f313d5b
📞 [OUTBOUND] Calling +17026721251 for All Access (Solar)...
   📡 Retell: 201
   ✅ Call initiated: call_86d368e9dd27d9901ff4f8eb034
```

Solar agent, correct ID, correct company, `201`, real call_id. The routing work is
done — the override is gone, `RETELL_API_KEY` is set, GHL is sending `solar`.

**But 201 does not mean the phone rang.** It means Retell accepted the request and
queued it. Whether it actually dialed is recorded on the call object afterwards. That's
the next thing to look at, and it's a Retell/carrier question now, not a code question.

---

## 🔍 Step 1 — Ask Retell what happened to that call

```bash
export RETELL_API_KEY=your_key
python3 retell_diagnose.py --call call_86d368e9dd27d9901ff4f8eb034 --number +17027105676
```

Read-only. It pulls `call_status` + `disconnection_reason` and interprets them, then
checks whether `+17027105676` is actually on the account and has an outbound agent bound.

What the answer will tell you:

| What comes back | What it means |
|---|---|
| `dial_failed` | Carrier refused the dial. Almost always the FROM number — not provisioned, or no outbound agent attached. |
| `marked_as_spam` / `scam_detected` | Carrier suppressed it silently. **This is the classic "201 but no ring."** |
| `dial_no_answer` | It genuinely rang. If your handset never lit up, the carrier dropped it late. |
| still `registered` after a minute | It never dialed at all. Look at the number. |
| `ended` with a duration | It connected — different problem entirely. |

---

## 🚩 Step 2 — The SMS 404 is a real clue

```
❌ Retell SMS failed: 404
   {"message":"Item not found in a2p-application with phoneNumber=+17027105676"}
```

`+17027105676` has no A2P 10DLC registration in Retell. Strictly, A2P governs **SMS
only** — its absence does not block voice, so this doesn't by itself explain the missing
ring. But it does tell you the number was recently added and isn't fully provisioned,
which makes a voice-side provisioning gap plausible too. The `--numbers` check above
distinguishes the two: if the number isn't listed, that's your answer for both.

To fix texting, register the number for A2P 10DLC in Retell (Phone Numbers → the number
→ A2P / 10DLC registration). It's a carrier process — typically a few business days.
Until it clears, the NEPQ intro text will keep 404ing. Calls don't depend on it.

---

## 🚩 Step 3 — `state` is being sent as `"solar"`

```
'customData': {..., 'agent_type': 'solar', 'state': 'solar'}
```

The `state` field got the agent type copied into it. It should be the lead's state —
`CO`. This is the same bug as the original hardcoded `"roofing"`, just with a new value.
In GHL, set `state` = **Contact.State**.

The `CO` you see elsewhere in the payload is under `location` — that's your Littleton
business address, not the lead's.

Also `'address': 'undefined'` — a literal string, meaning the GHL merge field didn't
resolve. The parsed line confirms it arrived empty. That's why Hailey's opener falls back
to the no-address variant.

---

## Note on the second webhook

Two different contacts appear in that log: `InUW9teQILIbiXwXuHos` (the one that got the
201) and `TN1FNDkvwYw5R6NO6tJZ` a minute later, with `tags: ''` — no `english` tag. Both
are the same phone. The second almost certainly hit the active-sequence guard from the
first, which is expected behavior, not a bug. Clear it between tests:

```bash
python3 clear_stuck_sequence.py --phone 7026721251 --apply
```

---

## Most likely answer, stated plainly

A brand-new 702 number, with no traffic history and no completed registration, dialing a
702 cell. Carrier spam filtering suppresses exactly this pattern, and it presents exactly
this way: API says success, handset never rings, no missed call.

If `retell_diagnose.py` comes back `marked_as_spam` or a clean `dial_no_answer`, that's
confirmed, and the fix is the thing I flagged at the very start — **get a 303 or 720
Denver number** and complete its registration. You need it for answer rates on Denver
leads anyway; this would just make it urgent rather than optimizational. The pool slots
are already stubbed in `RETELL_PHONE_POOL` and `RETELL_STATE_FALLBACK`.

Run the diagnostic and paste the output — I'll read it with you.

---

## Still outstanding

- **Rotate the exposed Twilio token** if you haven't. Still public in commit `3031a57`.
- **Railway volume.** `DB_PATH` is `~/voice.db` on container disk. No volume = every
  deploy wipes leads, calls, and sequences.
