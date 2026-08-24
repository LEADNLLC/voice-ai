# Voicelab go-live checklist

Do these in order. The whole thing is about 20 minutes. Nothing below is optional —
each item is fixing something we watched break on a real call this week.

---

## 1. Deploy the code  (fixes ~6 separate bugs at once)

Upload the new **voice_app.py** (or `git am` the patch) and let Railway redeploy.

This one deploy carries every code fix from this week:

- **Date/time awareness** — she stops saying "Monday" on a Monday and stops offering mornings that already passed
- **Outreach safety gate** — the thing that stops another 21,983-contact mass dial
- **Fixed intro SMS** — your approved copy, no AI writing it, no more "end"
- **No more "there" cards** — placeholder names become the real name or phone
- **3-a-day cadence + auto pipeline stages**
- **Never speaks a raw `{{variable}}`**

⚠️ **None of this is live until you deploy.** Every "she said Monday again / said today again" issue is this file sitting undeployed.

---

## 2. Set the Railway variables  (the code needs these to switch on)

Railway → your service → **Variables**. Add or confirm:

```
GHL_TIMEZONE=America/Denver          ← makes the date/time correct. THE important one.
CALLING_ENABLED=true                 ← global kill switch. Flip to false to stop everything instantly.
REQUIRED_LEAD_TAGS=english,spanish   ← only tagged ad leads get called. Stops mass dials.
SEQUENCE_PIPELINE_NAME=Solar Leads Client
SATURDAY_OK=true
SUNDAY_OK=false
EARLIEST_OFFER_HOURS=2               ← soonest slot she'll offer (no "6pm" at 5pm)
BYPASS_CALLING_HOURS=false           ← ⚠️ set false before real volume, or she calls at 3am
```

After it boots, the log's first call should print the date variables and
`✅ Outreach approved` / `🛑 OUTREACH BLOCKED` lines. If you see those, the gate is on.

---

## 3. Delete the bad GHL trigger  (stops the mass dial at the source)

GHL → Automation → the workflow with two triggers → **delete the "Contact Created —
No filters applied" trigger.** Keep **"Contact Tag → english"** and add a matching
**"Contact Tag → spanish"** trigger.

The code gate in step 2 is the backstop; this is the actual fix. Do both.

---

## 4. Paste the new prompt into Retell  (the whole call script)

Retell → the Hailey solar agent → **General Prompt** → paste all of
**hailey-PROD-prompt.md**, FIELD 2 section.

This is the version with: answer-questions-don't-book-over-them, the assumptive close,
second-home handling, "sound human", and two-real-clock-times scheduling.

---

## 5. Change the Retell voice settings  (fixes the 1800ms dead air)

Same agent, **Speech / Voice settings**. This is what's causing the "Hearing what?"
and the split greetings. No prompt edit can touch it.

| Setting | Set to |
|---|---|
| **Responsiveness** | **0.7** (she starts talking too soon over slow speakers) |
| **Interruption Sensitivity** | **0.5** (a one-word "hello?" splits her greeting) |
| **Voice Speed** | **0.9** |
| **Denoising** | **remove noise + background speech** |
| **Reminder frequency** | 15s+ or off |

If there's a **"Dynamically adjust based on user input"** checkbox by Responsiveness,
turn it on.

⚠️ Interruption Sensitivity does NOT work in Retell's Test Playground — only on live
dials. Judge it on a real call.

---

## 6. One test call to yourself, and check the log

Call a test number and confirm, in the Railway log:

- `🧮 Retell vars: first_name=... address=... has_address=yes` — variables render
- the date line shows the real day/time
- she says a real clock time and the correct day (not "Monday" if it's Monday)
- a contact WITHOUT the english/spanish tag shows `🛑 OUTREACH BLOCKED`

If all four are true, everything from this week is live and working.

---

## Still outstanding after this (not blockers, but real)

- **A2P 10DLC registration on +17206054003** — texts still get filtered by carriers
  until this clears. The intro SMS now routes through GHL's registered number as a
  workaround, but register the Retell number properly when you can.
- **Rotate the exposed keys** — the Twilio token and Retell key were in a public
  commit earlier. Rotate them.
- **Rename the Retell agent** from "Paige Outbound (copy)" to something you'll
  recognize.
- **Clean up duplicate GHL workflows** — there are 150+, many overlapping SMS bots.
  Worth a pass so one lead has exactly one sender.
