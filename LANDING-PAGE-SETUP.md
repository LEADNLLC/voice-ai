# Get the self-booking page live (you're already set up for this)

Your main site americanhomesenergy.com is already on Netlify, and Netlify already manages
your domain. So this is easy: we add a **second** Netlify site for the booking page and give it
the subdomain `report.americanhomesenergy.com`. Your main site is never touched.

Two pieces:

- **The page** — `index.html` (in the `netlify-site` folder). Static. Goes on Netlify.
- **The booking brain** — your **voice_app.py** on Railway. When someone taps *Confirm my
  visit*, the page sends the booking to your app, which books it on your real GHL calendar,
  moves the pipeline card to *Appointment Set*, and texts you. Already wired — reuses the same
  code Hailey uses.

---

## The one value I need from you

The page has to know your app's public web address (where it sends bookings). Get it here:

**Railway → your service → Settings → Networking → Public Networking.** It ends in
`.up.railway.app` (or it's your custom domain). Paste that to me and I'll bake it into the page
so there's nothing for you to edit. (If public networking isn't turned on, click **Generate
Domain** — that turns it on and gives you the URL.)

Until that's set, the page loads fine but *Confirm* shows a red retry message.

---

## Step 1 — Put the page on Netlify (a new site, ~1 min)

1. Go to **app.netlify.com**. Look for **Add new site → Deploy manually** (Netlify Drop).
2. Drag the **`netlify-site` folder** onto the drop area (the folder, not just the file).
3. Netlify makes a new site with a random name and a live `*.netlify.app` link. Open it on your
   phone and tap through — it should work end to end (once the app URL above is set).

To update later: same site → **Deploys** → drag the new folder in. Instant.

---

## Step 2 — Give it your subdomain

1. In that new Netlify site → **Domain management → Add a domain**.
2. Enter `report.americanhomesenergy.com` and add it.
3. Because your domain already lives in Netlify, it wires the DNS itself and turns on HTTPS —
   usually no GoDaddy step needed. If it asks you to confirm a record, just approve it.

Your main americanhomesenergy.com stays on its own site the whole time.

---

## Step 3 — Point traffic at it

1. **Facebook ad** — set the ad's destination URL to `https://report.americanhomesenergy.com`.
   This is the fix for the "$250, no appointments" leak.
2. **Your main site's "See my free energy report" button** — link it to the same URL, so your
   whole site funnels into the booking page too.

### Passing the name & phone through (so the page only asks for the address)

You asked for the last step to be address-only. That works when the person's name and phone
arrive with the click. Two ways, easiest first:

- **Best (keeps the phone number out of the URL):** send the GHL contact id on the link —
  `https://report.americanhomesenergy.com/?cid=CONTACT_ID`. In GHL, after the lead is captured,
  redirect to that URL with the contact id merged in. The app already knows that contact, so the
  page just needs the address.
- **Simple:** `https://report.americanhomesenergy.com/?fn=FIRST&ph=PHONE`. Works, but it does put
  the phone number in the web address.

If someone lands with **none** of that (e.g. straight from your site button), the page quietly
shows the name + phone fields again so they're never stuck. Nothing to configure for that — it's
automatic.

---

## Step 4 — Test before spending ad money

On your phone open `https://report.americanhomesenergy.com`, book a fake visit with your own
name/number, then check:

- it shows on your **GHL calendar** at the time you picked,
- the contact's card moved to **Appointment Set**,
- **you got the owner text**.

All three = you're live.

---

## What I changed on the page today

- **Same-day booking** — "Today" now appears with its remaining times, and it only offers slots
  at least ~2 hours out, so it never shows a time that already passed. Today drops off
  automatically once it's too late in the evening.
- **Address-only last step** — name + phone come from the lead link; only the address is asked
  (with a safe fallback to all fields for direct visitors).
- Branded **American Home Energy**, books straight into your **GHL calendar**.

Reminder: the booking only works once **voice_app.py is deployed** on Railway (same deploy
that's been in the checklist) and the app URL above is set in the page.
