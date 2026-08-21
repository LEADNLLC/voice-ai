# Telnyx → Retell: Denver number via elastic SIP trunking

**Yes, this works — and it's a documented path.** Retell publishes a Telnyx guide, which
is exactly what SignalWire lacked. Telnyx's model is FQDN-based: you tell Telnyx to trust
`sip.retellai.com`, and Retell authenticates with credentials. That is precisely the
"external platform terminates through us" pattern SignalWire never exposed in your
dashboard, which is why we hit `404 Domain unavailable` there and will not here.

---

## Part 1 — Telnyx

### 1a. Buy a Denver number
Telnyx → Numbers → Search → area code **720** or **303**. Buy it.

### 1b. Create a SIP Connection — type **FQDN**

Telnyx → **SIP Connections** → Create.
**Select FQDN as the type.** Not IP-based, not credential-only — FQDN.

### 1c. Add Retell as the FQDN

Inside the connection, add:

| Field | Value |
|---|---|
| FQDN | `sip.retellai.com` |
| DNS record type | **SRV** |

SRV, not A. Getting this wrong is a silent failure.

### 1d. Set outbound authentication credentials

In the connection's outbound settings, create a **username and password**. Write both
down — they go into Retell in Part 2, and the username is needed twice.

### 1e. Create an outbound voice profile

Telnyx → **Outbound Voice Profiles** → create one, then select it on this connection.
Without a profile attached, outbound calls are rejected.

### 1f. Codecs and transport

| Setting | Value |
|---|---|
| Codecs | `G722, G711U, G711A` |
| Transport | **TCP** |

TCP is what Retell recommends, and it matches what you already had set.

### 1g. Assign the number
Attach your new 720 number to this SIP Connection.

---

## Part 2 — Retell

Phone Numbers → **+** → **Connect to your number via SIP trunking**

| Field | Value |
|---|---|
| **Phone Number** | your new Telnyx 720, E.164 (`+1720XXXXXXX`) |
| **Termination URI** | your region's Telnyx FQDN from **https://sip.telnyx.com/** (e.g. `sip.telnyx.com`) |
| **SIP Trunk User Name** | the username from 1d |
| **SIP Trunk Password** | the password from 1d |
| **Outbound Transport** | TCP |
| **Nickname** | `Denver 720 - Telnyx` |

**Check https://sip.telnyx.com/ for the right regional FQDN** rather than assuming
`sip.telnyx.com`. Telnyx runs regional endpoints and the wrong one behaves exactly like
the SignalWire failure did.

### ⚠️ The gotcha that will cost you an hour

Retell's Telnyx guide requires a **custom SIP header** on outbound calls:

```
X-Telnyx-Username: <your username from 1d>
```

Telnyx uses it to match the INVITE to your connection. Without it you get authentication
failures that look like credential problems but aren't.

If the import dialog has no custom-headers field, it can be set per call — the
`create-phone-call` API takes a `custom_sip_headers` object, and I can wire that into
`voice_app.py` in about two minutes. Say the word and I'll add it.

---

## Part 3 — Point the app at it

Railway → Variables:

```
HAILEY_PHONE_NUMBER=+1720XXXXXXX      # the Telnyx Denver number
RETELL_PHONE_NUMBER=+1720XXXXXXX
SMS_PHONE_NUMBER=+17027105676         # unchanged - trunk is voice only
```

Then in Retell, on the new number:
- **Outbound Call Agent** → your Hailey solar agent
- **Agent Level Webhook URL** → `https://www.voicelab.live/webhook/retell`

---

## Part 4 — Test

Trigger one call. In Railway you want:

```
✅ USING SOLAR CLIENT AGENT: agent_51e1e8bbc32e11ce5d2f313d5b
✅ USING HAILEY NUMBER: +1720XXXXXXX
   📡 Retell: 201
```

Then in Retell → Call History, the row should show a real duration instead of
`invalid_destination` / `not_connected`.

| If it fails | Look at |
|---|---|
| 404 again | Termination URI — wrong regional FQDN |
| 401 / 403 | credentials from 1d, or the missing `X-Telnyx-Username` header |
| Connects, wrong caller ID | number not attached to the connection (1g) |
| Rejected outbound | no outbound voice profile attached (1e) |

Telnyx's own call logs will show the INVITE arriving and why it was refused — far more
visibility than we ever got from SignalWire.

---

## Honest comparison

| | Buy in Retell | Telnyx trunk |
|---|---|---|
| Setup time | ~2 min | ~20 min |
| Moving parts | 0 | 6 |
| Documented by Retell | native | ✅ dedicated guide |
| SMS on that number | ✅ | ❌ voice only |
| Per-minute cost | Retell's rate | usually cheaper |
| Carrier control | none | full |

Telnyx is the right answer if you want carrier control and better per-minute pricing at
volume, and it is genuinely supported — not the dead end SignalWire turned out to be.
Buying inside Retell is still faster if tonight's goal is simply to see Hailey ring a
phone and book an appointment.

Either beats where you are now.
