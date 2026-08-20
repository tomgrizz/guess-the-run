# Run Pool 2026 — deploy notes

One static file (`index.html`, fonts embedded, no build step) plus a 2-minute Google
backend for the guess log. Until the backend is connected the page runs in **preview
mode**: guesses save only in each visitor's own browser and a banner says so.

## 1. Create the guess log (Google Sheet + Apps Script)

1. Create a new Google Sheet (name it anything, e.g. `run-pool-entries`).
2. In the Sheet: **Extensions → Apps Script**. Delete the placeholder code and paste the
   entire contents of `apps_script_backend.gs`. Save.
3. **Deploy → New deployment → Web app**:
   - *Execute as*: **Me**
   - *Who has access*: **Anyone** (required so teammates can submit without logging in)
   - Deploy, authorize with your account, and copy the **Web app URL**
     (looks like `https://script.google.com/macros/s/AKfycb.../exec`).

Entries land in an `entries` tab: `ts | name | gan | cre | received`. The site shows the
latest entry per name; the sheet keeps the full history (handy for the tie-breaker —
earliest `ts` wins).

## 2. Connect the site

Open `index.html`, find the `CONFIG` block near the bottom, and paste the URL:

```js
var CONFIG = {
  SCRIPT_URL: "https://script.google.com/macros/s/AKfycb.../exec",
  CLOSE_ISO:  "2026-09-01T03:59:00Z"   // Aug 31 2026, 11:59 pm ET — edit to move the deadline
};
```

That's the only edit the file needs. (Model numbers are frozen 2026-08-19 on purpose —
fair-pool rules — and live in the `MODEL`/`HISTORY` constants beside `CONFIG`.)

## 3. Host it

Any static host works; simplest is GitHub Pages:

1. Push `site/` to a repo (or copy `index.html` into a `docs/` folder of an existing one).
2. Repo **Settings → Pages → Deploy from branch**, pick the branch/folder.
3. Share the URL with the team. Nobody needs a login of any kind.

A work web server or a shared drive won't work for the *log* unless it serves over
http(s) — `file://` pages still run, but in preview mode per-browser.

## Running the pool

- **Test first**: submit a test entry, check it appears in the Sheet, delete the row.
- **Close of entries** is automatic at `CLOSE_ISO` (form disables, tile says "locked").
- **Judging**: when official technician-validated season totals are in, score each
  person's latest pre-deadline entry: `abs(gan − actual_gan) + abs(cre − actual_cre)`,
  lowest wins, ties to earliest timestamp. Thirty seconds with the Sheet sorted by `ts`.
- **Reveal**: the board is public the whole time by design (team decision, Aug 2026).

## Later (planned, not built)

A live run-count tile fed from the salmonid-cv daily counter output — the footer already
promises it. When the 2026 dailies start, wire a small JSON export into the page or ask
Claude to extend `doGet` with a `counts` feed.
