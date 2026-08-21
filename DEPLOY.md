# voicelab — why that test didn't dial

Your log shows the new code **is** live (the outbound number printed as `+17027105676`).
Two things blocked the call, and one of them was my miss.

---

## 1. The 401 — `RETELL_API_KEY` isn't set in Railway

```
❌ Retell SMS failed: 401
   {"message":"The authorization header must be in the format of 'Bearer <YOUR-API-KEY>'"}
   📡 Retell: 401
```

Retell isn't rejecting a *wrong* key — it's saying the header is *malformed*. The code
sends `Authorization: Bearer {RETELL_API_KEY}`, and with that variable empty the header
goes out as a bare `Bearer ` with nothing after it. That's the exact failure mode of
deploying after the hardcoded fallback was removed but before the variable was set.

**Fix:** Railway → your service → Variables → add `RETELL_API_KEY` = your rotated key,
then redeploy. Nothing else in this file matters until that's set — every call and text
will 401 regardless of routing.

Verify with the Retell key that's actually live now (if you rotated, use the new one).

---

## 2. My miss — a hidden override was forcing solar back to roofing

This is on me. When I made the first pass I fixed the two routing sites in `make_call`,
but there was a **third** override sitting upstream in the GHL webhook handler that I
didn't catch:

```python
agent_type = _cd.get('agent_type') or d.get('agent_type') or 'roofing'
if agent_type == 'solar':
    print("⚠️  agent_type 'solar' received but solar agent is disabled - forcing roofing")
    agent_type = 'roofing'          # <-- stomped whatever GHL sent
```

Added during the June ToS-block, never removed. It intercepted `solar` **before** routing
ever ran — so even with GHL fixed and my earlier patch deployed, you'd still have landed
on the roofing agent. Removed now.

While in there I also fixed a related trap. Your payload sends **`'agent_type': 'Roofing'`**
— capital R — but every branch compares against exact lowercase `'solar'` / `'roofing'`.
So had you simply set GHL to `Solar`, it would have missed the solar branch *and* the
roofing branch and fallen through to the **Paige demo agent** on a live lead, with no
error. The handler now normalizes with `.strip().lower()`, and the fallback branch logs
loudly instead of dialing a demo agent in silence.

Verified across the casings GHL actually sends:

| GHL sends | resolves to | agent |
|---|---|---|
| `Solar` | `solar` | `agent_51e1e8bbc32e11ce5d2f313d5b` ✅ |
| `solar` | `solar` | `agent_51e1e8bbc32e11ce5d2f313d5b` ✅ |
| `Roofing` | `roofing` | `agent_50ac8943...` (Bulldog — correct, separate client) |
| missing/empty | `solar` | `agent_51e1e8bbc32e11ce5d2f313d5b` ✅ |

I also flipped the default from `roofing` to `solar`, so a payload missing the field
lands on solar rather than dialing your roofing client's agent.

---

## 3. GHL is still sending `Roofing`

```
'customData': {'action': 'sequence', ..., 'agent_type': 'Roofing'}
```

Set it to `solar` in **both** webhook workflows. Casing no longer matters after the fix
above, but the *value* still has to change.

Also still missing from `customData`: **`state`**. Your payload has `location.state: 'CO'`
(that's your business address, not the lead's) but no lead-level state field. Add
`state` = Contact.State.

`contact_id` looks correct now — `jrkqQPsQHDuX2VCFVvHT` is a real contact ID, not the
account owner ID. That one's done.

---

## Do these in order

1. **Set `RETELL_API_KEY` in Railway.** Nothing works until this is done.
2. **Upload the new `voice_app.py`** (override removal + normalization).
3. **GHL, both workflows:** `agent_type` → `solar`, add `state` → Contact.State.
4. **Clear the stuck sequence** — your test contact now has an active row:
   `python3 clear_stuck_sequence.py --phone 7026721251 --apply`
5. **Re-test.** You want to see exactly this:

```
📥 agent_type resolved: 'solar'
🔍 AGENT TYPE RECEIVED: 'solar'
✅ USING SOLAR CLIENT AGENT: agent_51e1e8bbc32e11ce5d2f313d5b
✅ USING HAILEY NUMBER: +17027105676
📡 Retell: 201
```

`📡 Retell: 201` is the one that means a call actually left. `401` = step 1 not done.
If you see `⚠️⚠️ UNRECOGNIZED agent_type`, GHL is sending something unexpected — the
line prints the value it got.

---

## Still outstanding from before

**Rotate the exposed Twilio token and Retell key** if you haven't. They were public in
`LEADNLLC/voice-ai` and remain in commit `3031a57` regardless of the current file.

**Check for a Railway volume.** `DB_PATH` is `~/voice.db` — SQLite on container disk.
With no volume mounted, every deploy wipes leads, call history, and sequences. You're
about to deploy again.

**Denver local presence.** You're dialing Denver leads from a Vegas number. The 303/720
slots are stubbed and commented in `RETELL_PHONE_POOL` and `RETELL_STATE_FALLBACK`.
