# Connecting SignalWire +1 (720) 686-4625 to Retell via SIP

Goal: Hailey dials Denver leads from a Denver number.

**Scope note:** this sets up **outbound** (Retell → SignalWire → the lead). That is what
your dialer needs. Inbound (someone calling the 720 back) is a separate step, covered at
the end. Do outbound first and confirm it works before touching inbound.

---

## Part 1 — SignalWire: get the three values Retell is asking for

### 1a. Find your SIP domain (this is the Termination URI)

SignalWire Dashboard → left nav → **SIP** (sometimes under *Resources* → *SIP*).

**Your SIP domain is:**

```
leadn-llc-b79dfe08c385.sip.signalwire.com
```

Note the hash. SignalWire appends a unique suffix to the space name, so it is NOT the
plain `leadn-llc.sip.signalwire.com` you might expect. Using the short form gives a 404
at the trunk with no useful error.

Copy it exactly. No `sip:` prefix, no username, no port.

### 1b. Create a SIP credential

Dashboard → **Resources** → **+ Add** → **SIP Credential**
(older UI: *SIP* → *SIP Credentials* → *New*)

On the **URI** screen, the domain half is already fixed on the right of the box. Type
**only the name part** into the field — letters, numbers and dashes:

```
retell-outbound
```

That makes the full SIP address `retell-outbound@leadn-llc-b79dfe08c385.sip.signalwire.com`.

Then on the same endpoint:

- **Password**: generate a strong one — SignalWire shows it once
- **Caller ID**: set to **+17206864625**

That caller ID field matters. If it is blank or set to another number, SignalWire may
stamp a different caller ID on the outbound leg and your Denver local presence quietly
disappears — the whole point of this exercise.

Write down the username and password. You will type them into Retell in Part 2.

### 1c. Confirm the number is on this project

Open **+1 (720) 686-4625** → confirm it is in the same Project as the SIP credential.
Its ID is `60420756-af67-478a-adcf-f8e2f4ee2b33`. If the number lives in a different
Project than the credential, authentication succeeds but the caller ID is rejected.

---

## Part 2 — Retell: fill in the form you have open

| Field | Value |
|---|---|
| **Phone Number** | `+17206864625` — already correct |
| **Termination URI** | `leadn-llc-b79dfe08c385.sip.signalwire.com` — domain only, **no** `retell-outbound@` |
| **SIP Trunk User Name** | the credential username from 1b, e.g. `retell-outbound` |
| **SIP Trunk Password** | the password from 1b |
| **Nickname** | `Denver 720 - SignalWire` |

The field hint "NOT Retell SIP server uri" is telling you not to paste
`sip.retellai.com` here. That address is where SignalWire sends calls **to** Retell
(inbound, Part 5). This field is the opposite direction.

Username and password are marked "encouraged" but treat them as required — without
them SignalWire authenticates by IP, which means whitelisting Retell's IP ranges instead,
and that is more moving parts for no benefit.

Save.

---

## Part 3 — Bind the right agent

Still in Retell, open the newly added `+1 (720) 686-4625`:

- **Outbound Call Agent** → your **Hailey solar agent**, `agent_51e1e8bbc32e11ce5d2f313d5b`

Do **not** leave it on "Paige Outbound (copy) (copy)" the way the 702 was. The app now
sends `override_agent_id`, so the override wins — but the number's default is the safety
net for any call that goes out without one, and you want that net to be Hailey.

---

## Part 4 — Point the app at it

Railway → Variables:

```
HAILEY_PHONE_NUMBER=+17206864625     # calls  -> Denver, SIP-trunked
SMS_PHONE_NUMBER=+17027105676        # texts  -> Retell-native (A2P pending)
```

Keep these different. **A SIP-trunked number is voice-only** — Retell cannot send SMS
over a trunk. The code now reads them separately (it used to ignore `SMS_PHONE_NUMBER`
entirely and text from the call number, which would have broken texting the moment you
switched the call number over).

The phone pool already routes `303` and `720` area codes and the `CO` state fallback to
`+17206864625`, so Denver leads get the Denver caller ID automatically.

---

## Part 5 — Inbound (optional, do it after outbound works)

Right now, calling the 720 back reaches SignalWire and stops. To send those to Retell:

SignalWire → the number → **Edit Settings** → handle calls with a **LaML Webhook** or
**LaML Bin**, returning:

```xml
<Response>
  <Dial>
    <Sip>sip:+17206864625@sip.retellai.com</Sip>
  </Dial>
</Response>
```

Then bind an **inbound** agent to the number in Retell. If nobody calls back today, skip
this — outbound is what the dialer needs.

---

## Part 6 — Test

Trigger one call and watch the Railway logs:

```
✅ USING SOLAR CLIENT AGENT: agent_51e1e8bbc32e11ce5d2f313d5b
✅ USING HAILEY NUMBER: +17206864625
   📡 Retell: 201
```

Then check the handset. What you are looking for is a **Denver caller ID actually
ringing** — that is the thing the 702 never managed.

If it fails, check in this order:

| Symptom | Cause |
|---|---|
| Retell 401/403 at trunk | wrong SIP username/password |
| Retell 404 at trunk | wrong Termination URI — re-read it from 1a |
| Connects but shows the wrong caller ID | Caller ID not set on the SIP credential (1b) |
| `201` then silence again | not a trunk problem — run `retell_diagnose.py --call <id>` |

The last row matters. If a Denver number also returns `201` and never rings, the caller
ID was never the cause, and the answer is in `disconnection_reason`.

---

## Why this is worth doing

Your current outbound is a Las Vegas number calling Denver homeowners, and before that
it was Rhode Island. Local presence is consistently one of the largest levers on answer
rate for cold outbound. You already own the right number — it has been sitting in
SignalWire since Aug 17 doing nothing.

Two things it does **not** fix: SMS still needs A2P 10DLC on the Retell-native number,
and if calls are being suppressed for a reason other than caller ID, this won't change
it. Run the diagnostic on that last `call_id` either way, so you know which problem you
actually have.
