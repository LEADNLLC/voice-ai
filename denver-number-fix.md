# Getting Hailey a Denver number that actually dials

## What's actually wrong

`404 Domain unavailable` is SignalWire's SIP proxy saying **"I don't serve that domain."**
Not a credential problem, not DNS, not the URI string — all three check out.

The reason is an architecture mismatch, and it's the thing I got wrong:

> **A SIP Credential is for a device to REGISTER *to* SignalWire.**
> **A Domain App is what makes a SignalWire domain ACCEPT SIP traffic from outside.**

You created a SIP Credential (`retell-outbound`). Retell isn't a phone registering to
SignalWire — it's an external platform pushing INVITEs at a domain. SignalWire's proxy
doesn't serve `leadn-llc-b79dfe08c385.sip.signalwire.com` for that, so it 404s before
authentication is ever considered. That's why the username and password looked fine and
changed nothing.

SignalWire's own BYOC docs are explicit:

> "External carriers send SIP traffic to a custom domain via a Domain App. Domain Apps
> allow you to send SIP traffic to a custom domain and use SignalWire APIs to manage the
> incoming request."

Their API reference confirms the domain is built as `<space>-<identifier>`, and Domain
Apps carry `ip_auth_enabled` / `ip_auth` fields — meaning even once the domain exists,
Retell's IPs likely need whitelisting.

---

## ✅ Recommended: skip the trunk, buy the number inside Retell

**This is what I'd do.** In the same `+` menu where you found "Connect to your number via
SIP trunking" there's **"Buy New Number."** Search area code **720** or **303**.

Why this wins:

| | Retell-native number | SignalWire + SIP trunk |
|---|---|---|
| Denver local presence | ✅ | ✅ |
| Works immediately | ✅ | ❌ Domain App + handler + IP whitelist |
| SMS capable | ✅ (with A2P) | ❌ voice only |
| Moving parts that can break | 0 | ~5 |
| Debugging when it breaks | Retell logs | Retell logs + SignalWire logs + SIP traces |

The only reason the SignalWire number was appealing is that you already owned it. That's
sunk cost. A Retell number costs a few dollars a month and removes an entire failure
domain from a system you need running tonight.

**Steps:**
1. Retell → Phone Numbers → **+** → **Buy New Number** → area code `720` or `303`
2. Bind **Outbound Call Agent** → your Hailey solar agent
3. Set the Agent Level Webhook URL → `https://www.voicelab.live/webhook/retell`
4. Railway: `HAILEY_PHONE_NUMBER` and `RETELL_PHONE_NUMBER` → the new number
5. Leave `SMS_PHONE_NUMBER` alone until A2P clears, then move it too
6. Test call — you should get a Denver caller ID that rings

Then cancel the SignalWire number, or keep it for inbound if you want.

---

## ❌ The GHL integration will not do this

Retell's GoHighLevel integration is a **data bridge, not a telephony connection.** It does:

- Sync contacts from GHL into Retell (so the agent knows the name and pipeline status)
- Let the agent tag contacts, manage opportunities, and book into GHL calendars mid-call

It does **not** provide telephony. You cannot use a GHL/LeadConnector number as Retell's
outbound caller ID, and the integration does not initiate calls from GHL workflows — it
only reacts to call outcomes. GHL numbers are LeadConnector-managed and don't expose SIP
credentials, so there's no back door either.

Worth knowing for a different reason though: that integration could book appointments
into your GHL calendar **during** the call, instead of the post-call webhook path we
built. More reliable, since it doesn't depend on the webhook firing. But do not enable
it while the custom integration is running — you'd get double-booked appointments and
duplicate tags. One or the other.

---

## 🥈 Alternative: the Twilio 720 you already own

`TWILIO_PHONE` in your config is **+17208189512** — a Denver 720 number sitting in your
Twilio account.

This is a better fallback than SignalWire for one reason: **Retell publishes a dedicated
Twilio Elastic SIP Trunking guide.** SignalWire is "other providers work too" territory,
which is exactly why we burned an evening on it. Twilio is the documented path.

Rough shape: Twilio Console → Elastic SIP Trunking → create a trunk → set Origination to
point at `sip:sip.retellai.com;transport=tcp` → assign +17208189512 to the trunk → give
Retell the Twilio termination URI (`your-trunk.pstn.twilio.com`) with its credential list.

Only take this path if buying a Retell number is blocked for some reason. It is still
more moving parts than a native number — but far fewer unknowns than SignalWire.

⚠️ Your Twilio credentials were exposed in the public repo and I blanked them pending
rotation. Rotate the auth token before using that account for anything.

---

## If you want the SignalWire trunk anyway

It is solvable — it's just three more pieces. Do this only after calls are working via
the route above, so you're not debugging while the campaign is down.

### 1. Create a Domain App

SignalWire Dashboard → **SIP** → **Domain Apps** → **Create a Domain App**

- Give it an **identifier** (e.g. `retell`). The resulting domain follows
  `<space>-<identifier>.sip.signalwire.com`, so you'd get something like
  `leadn-llc-retell.sip.signalwire.com`. **Read the exact value off the dashboard** —
  that string, not the SIP Credential's domain, becomes Retell's Termination URI.

### 2. Whitelist Retell's IPs

Domain Apps have IP authentication. SignalWire's docs warn:

> "It's VERY important to whitelist the IPs that you want to allow through — if you do
> not select this option, anyone who has the URL could send traffic to your custom
> domain app."

Retell publishes these ranges:

```
18.98.16.120/30      (all regions)
3.42.144.0/23        (all regions)
153.57.128.0/18      (all regions)
143.223.88.0/21      (certain US traffic)
161.115.160.0/19     (certain US traffic)
```

All five. Missing the ones Retell actually egresses from looks identical to a domain
that doesn't exist.

### 3. Point the handler at PSTN

The Domain App needs a handler that takes the inbound SIP call and dials the requested
number out to PSTN — a LaML bin or SWML script doing the equivalent of
`<Dial><Number>{called number}</Number></Dial>`. Without it the INVITE is accepted and
then goes nowhere.

### 4. Then update Retell

- **Termination URI** → the Domain App domain (not the SIP Credential domain)
- Transport **TCP** is correct — Retell documents TCP as recommended
- Keep the credential username/password if the Domain App is set to require auth

### If it still 404s

Ask SignalWire support, in these words:

> "I need an external platform (Retell AI) to send SIP INVITEs into my space and have
> SignalWire terminate them to PSTN, using +17206864625 as the caller ID. I created a
> SIP Credential and INVITEs to `leadn-llc-b79dfe08c385.sip.signalwire.com` return
> 404 Domain unavailable. Should I be using a Domain App instead, and what exact
> termination URI should Retell send to?"

That question gets a precise answer in one reply. It took me several wrong turns to
work out that a Credential and a Domain App are different things — their support knows
this cold.

---

## What this does not affect

The 702 is Retell-native and dials fine. Everything else built today — agent override,
address lookup from GHL, sequence hygiene, pipeline stage moves, appointment alerts,
webhook dedupe, the timezone fix — is independent of which number you call from. Get a
working number under it and the rest is already in place.
