# voicelab — solar routing cutover

Changes are made and the file compiles clean. **Do the steps in this order** — deploying
before step 1 will take the app down, because the API key fallbacks were removed.

---

## ⚠️ Step 0 — Rotate the exposed credentials (do this first, regardless)

`LEADNLLC/voice-ai` is a **public** repo, and until now `voice_app.py` carried live
credentials as fallback defaults. Assume they are compromised — scraper bots watch
GitHub for exactly this and hit within hours.

| Credential | Where to rotate |
|---|---|
| Twilio auth token | console.twilio.com → Account → API keys & tokens → rotate |
| Retell API key | dashboard.retellai.com → API Keys → revoke + create new |

While you're in Twilio, check **Monitor → Logs → Calls** and the billing page for
traffic you don't recognize. An exposed Twilio token is normally drained via
international premium-rate calls.

Removing the keys from the current file does **not** remove them from git history —
they remain readable in commit `3031a57`. Rotation is the only real fix.

---

## Step 1 — Set the Railway variables

Railway → your service → **Variables**. These no longer have code fallbacks:

```
RETELL_API_KEY       = <your NEW rotated Retell key>
HAILEY_PHONE_NUMBER  = +17027105676
RETELL_PHONE_NUMBER  = +17027105676
SMS_PHONE_NUMBER     = +17027105676
INTERNAL_API_KEY     = <a long random string>
TWILIO_SID           = <your NEW Twilio SID>      # optional, owner SMS alerts only
TWILIO_TOKEN         = <your NEW Twilio token>    # optional, owner SMS alerts only
```

Twilio is only used for alert texts to you and is guarded by an `if` — leaving it
blank degrades quietly, it won't crash the app. `RETELL_API_KEY` is **not** optional.

---

## Step 2 — Upload the changed files

Your repo history is a single "Add files via upload" commit, so the GitHub web UI is
the path of least resistance. Drag these into the repo root:

- `voice_app.py` — the three routing/config changes
- `env.example` — documents the now-required variables
- `.gitignore` — **note the leading dot**; the old file was named `gitignore`, which
  made it completely inert. That's how the `.env` protection failed in the first place.

Delete the old `gitignore` (no dot) after uploading.

If you'd rather apply it as a patch: `git am < voicelab-solar-routing.patch`

---

## Step 3 — Clear the stuck sequence

`clear_stuck_sequence.py` clears the `call_sequences` row that produces
*"Sequence already active for this lead."* It's a dry run unless you pass `--apply`.

```bash
python3 clear_stuck_sequence.py --list                    # see what's active
python3 clear_stuck_sequence.py --phone 7025551234        # preview
python3 clear_stuck_sequence.py --phone 7025551234 --apply
```

Phone matching is on the last 10 digits, so `+1`, dashes, and parens all work.

**Run this on Railway** (`railway run python3 clear_stuck_sequence.py ...`), not
locally — see the warning below about where the database lives.

---

## Step 4 — GHL, both webhook workflows

Nothing here is code; it's all in the GHL workflow UI:

| Field | From | To |
|---|---|---|
| `agent_type` | `roofing` | `solar` |
| `contact_id` | Account.Owner.ID | **Contact.Id** |
| `state` | hardcoded `"roofing"` | **Contact.State** |

---

## Step 5 — Test

Fresh contact, real cell, tag `english`. Watch the Railway deploy logs — the routing
block prints what it picked:

```
🔍 AGENT TYPE RECEIVED: 'solar'
✅ USING SOLAR CLIENT AGENT: agent_51e1e8bbc32e11ce5d2f313d5b
✅ USING HAILEY NUMBER: +17027105676
```

If you see `agent_50ac8943...` there, GHL is still sending `roofing`.

---

## 🚩 Two things worth fixing next

**Your database is on ephemeral disk.** `DB_PATH` defaults to `~/voice.db` — SQLite on
Railway's container filesystem. Unless you've mounted a volume, **every deploy wipes
all leads, call history, and sequences.** Deploying this change would do it. Check
Railway → Settings → Volumes before you push; if there's no volume, add one mounted at
the DB's directory, or move to Railway Postgres. This is a bigger problem than the
routing bug was.

**The 702 is a Las Vegas number and you're calling Denver.** Worth correcting the
record: the number you were on before (`+1401...`) was Rhode Island, so 702 is an
improvement, but neither is local. Buy a **303 or 720** number in Retell and add it —
I left the slots stubbed and commented in both `RETELL_PHONE_POOL` and
`RETELL_STATE_FALLBACK`, so it's an uncomment-and-fill. Local presence is typically
the single biggest lever on answer rate.

---

## What changed in `voice_app.py`

| Area | Change |
|---|---|
| Solar routing (2 sites, ~L5625 and ~L18657) | `agent_50ac8943...` (roofing fallback) → `agent_51e1e8bbc32e11ce5d2f313d5b` |
| Outbound number | every `+14012989927` → `+17027105676`, incl. pool, state fallback, defaults |
| `RETELL_API_KEY` ×2, `TWILIO_SID`, `TWILIO_TOKEN`, `YOUR_TWILIO_SID` | hardcoded values → `''` |
| `INTERNAL_API_KEY` | default `'voicelab-internal-2026'` → `''`, plus a new `has_valid_internal_key()` |

That last one needed care: blanking the default alone would have created an **auth
bypass** — a request with no `X-Internal-Key` header sends `''`, which would have
compared equal to the now-empty default and passed. The new helper requires both sides
non-empty and uses `hmac.compare_digest`. The roofing agent ID is untouched.
