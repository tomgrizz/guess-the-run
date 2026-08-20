# Guess the Run — Chinook Run Pool 2026

**Live site: https://tomgrizz.github.io/guess-the-run/**

The Lake Ontario assessment team's pool on the fall 2026 Chinook return to two fishway
counters: the Ganaraska (Corbett Dam) and the Credit (Streetsville). A forecast model has
made its call for each river; teammates click a level on the charts to cast a ballot,
fine-tune it in the boxes, and submit. Closest combined call to the official season totals
wins a plushie from [Freshwater Conservation Canada](https://freshwaterconservationcanada.myshopify.com/).

> A personal project and informal data exercise — not a peer-reviewed model and not an
> official product of any agency.

## How it works

- **Entries close 11:59 pm ET, August 31, 2026.** One ballot per person; resubmitting under
  the same name replaces the earlier one (latest before close counts).
- **Scoring:** `abs(your Ganaraska − actual) + abs(your Credit − actual)` against the official
  published season total for each counter. Lowest total wins; ties go to the earlier ballot.
- The model plays too (18,000 / 8,800). The bands on the charts are its typical past miss
  (±21% Ganaraska, ±45% Credit) and double that.
- Ballots are logged to a private Google Sheet via an Apps Script web app; the board and the
  chart tick-marks show everyone's calls. The page is public and needs no login.

## Repo contents

| File | What it is |
|---|---|
| `index.html` | The whole site — single self-contained file (fonts and figures embedded). |
| `apps_script_backend.gs` | The guess-log backend, pasted into a Google Apps Script bound to the Sheet. |

## Maintenance notes

- **Updating the page:** edit/replace `index.html` and push (or use *Add file → Upload files*
  on github.com); GitHub Pages rebuilds in a minute or two. Hard-refresh (Ctrl+Shift+R) to
  bypass the browser cache.
- **Config** lives near the bottom of `index.html`: `CONFIG.SCRIPT_URL` (the Apps Script
  web-app URL) and `CONFIG.CLOSE_ISO` (the entry deadline, in UTC).
- **Judging:** open the Sheet's `entries` tab, take each entrant's last row before the
  deadline, score as above.
- Forecast numbers are intentionally frozen at 2026-08-19 (fair-pool rule); they come from a
  cohort-based ensemble model built on the counter, ageing, and environmental data. The full
  analysis lives in a separate (private) report.
- Planned: a live run-count overlay on the charts once the September run starts.

*No lake whitefish appear anywhere in this repository. Cool fish only.*
