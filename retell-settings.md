# Retell settings for Hailey

Two different settings cause the two different problems, and they pull in opposite
directions. Changing only one will not fix both.

| Setting | Set to | Fixes |
|---|---|---|
| **Interruption Sensitivity** | **0.5** (from 1) | Her greeting getting chopped when they say "hello?" |
| **Responsiveness** | **0.7** (from 1) | Her starting to talk while they're mid-sentence |
| **Denoising mode** | **remove noise + background speech** | TV, other people, road noise triggering interrupts |
| **Reminder frequency** | raise to 15s+, or disable | The "hey, just checkin' in" after she'd said goodbye |
| **Voice Speed** | 0.9 | She reads fast; the agent itself called `adjust_voice_speed` mid-call |
| **Backchannel** | on, if available | Natural "mhm" while they talk |

## Why two settings

**Interruption Sensitivity** is how easily THEY can stop YOU. Range 0 to 1.
Lower means it takes more words to interrupt her. Retell support suggests ~0.8 for
general resilience; go to **0.5** because the failure here is specifically a one-word
"hello?" splitting `"Hey, is this"` / `"Victoria?"` across four separate calls.

Do not go to 0. At 0 she will not stop when someone genuinely objects, and talking over
a real objection is worse than being chopped.

**Responsiveness** is how fast she starts after they stop. Lower means she waits longer.
This is the Victoria bug: at 0:43 she started while Victoria was still saying "it's a lot
for one per—". She had decided the turn was over during a natural pause. **0.7** gives an
older or slower speaker room to finish a thought.

If the dashboard offers **"Dynamically adjust based on user input"** next to Responsiveness,
turn it on. It adapts to how fast the person actually talks, which is exactly the Victoria
case.

## ⚠️ Interruption Sensitivity does not work in the Test Playground

Retell support has confirmed this: the setting applies on live calls but not in the Test
Agent interface. Several transcripts we reviewed came from the playground, so the
split-greeting behaviour there was never going to reflect the setting.

**Judge this one on real dials only.**

## Also confirm

- The agent has an **end call function** attached. Without it she cannot hang up — she
  just goes silent, which is what produced the dead air followed by "hey, just checkin' in".
- Rename the agent from "Paige Outbound (copy) (copy)" to **Hailey - Solar**.
- Agent-level webhook URL points at `https://www.voicelab.live/webhook/retell`.

## Sources
- https://docs.retellai.com/build/single-multi-prompt/configure-basic-settings
- https://community.retellai.com/t/interruption-sensitivity-doesnt-work/358
