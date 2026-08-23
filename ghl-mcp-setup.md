# Connecting GoHighLevel to Claude

There is no GoHighLevel connector in Claude's built-in directory, but **HighLevel ships
its own MCP server** and it is added as a custom connector.

## Setup (about two minutes)

1. In Claude, go to **Settings → Connectors → Add custom connector**
2. Server URL:
   ```
   https://services.leadconnectorhq.com/mcp/anthropic/v2
   ```
3. Sign in to HighLevel and authorize the LEADN sub-account
4. Start a new chat — the tools load there, not in an existing one

**Auth:** OAuth (the sign-in flow above) is the recommended path and gives broader scope
than the alternative. If you would rather scope it tightly, create a **Private Integration
Token** under Settings → Private Integrations, pick only the scopes you want, and pass it
as `Bearer pit-your-token`.

## What it exposes

Six tools over roughly 625 operations across 40 domains — contacts, conversations,
opportunities, calendars, payments:

| Tool | Does |
|---|---|
| `search` | find records by name, email, phone, tag |
| `fetch` | pull a full record |
| `search_operations` | find an API operation by intent |
| `describe_operation` | inspect its inputs before running |
| `execute_operation` | run it within your authorized scopes |
| `list_locations` | list sub-accounts (needed if you run more than one) |

## What this actually unlocks for voicelab

Several open items in this build are things I currently have to guess at from logs. With
the connector on I could look directly:

- **The second workflow still sending `agent_type: Roofing`** — find it and read the
  webhook body instead of inferring it from a Railway log line
- **`ILLINOIS - VIRTUAL` calendar** — confirm the exact name and ID rather than
  name-matching at runtime
- **`Appointment Set` pipeline stage** — verify the stage exists in pipeline
  `QcJSeWfA1T1xjAIP8SE4` and is spelled the way the code expects
- **A booked appointment end to end** — check that Hailey's booking actually landed on the
  calendar with the right timezone, on a real contact
- **Address data quality** — see how many contacts have `"124 Main Street"` vs `"124 Main"`,
  which is the thing making her say "Street" out loud
- **Custom fields** — confirm `agent_type`, `contact_id`, `state` are mapped the way the
  webhook expects

## This does not replace the API integration in voice_app.py

Two separate things:

- **`voice_app.py` → GHL API** is how the app books appointments and moves opportunities
  at runtime. That works and needs no change.
- **GHL MCP → Claude** is how *I* read and debug your CRM in this conversation. It runs
  only when you ask, from your machine's session.

Adding one does not affect the other.

## Sources
- https://help.gohighlevel.com/support/solutions/articles/155000008360-highlevel-mcp-multi-account-support-for-claude
- https://weblystudio.com/blog/connect-claude-to-gohighlevel/
