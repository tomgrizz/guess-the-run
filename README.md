# Guess the Run — Chinook Run Pool 2026

**Live site: https://tomgrizz.github.io/guess-the-run/**

The Lake Ontario assessment team's pool on the fall 2026 Chinook return to two fishway
counters: the Ganaraska (Corbett Dam) and the Credit (Streetsville). A forecast model has
made its call for each river; teammates click a level on the charts to cast a ballot,
fine-tune it in the boxes, and submit. Closest combined call to the official season totals
wins a plushie from [Freshwater Conservation Canada](https://freshwaterconservationcanada.myshopify.com/).

> A personal project and informal data exercise — not a peer-reviewed model

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
| `scripts/fetch_counts.py` | Pulls the raw counter numbers from riverwatcherdaily.is into `data/`. |
| `.github/workflows/update-counts.yml` | Runs that script twice a day and commits the result. |
| `data/counts.json` | What the page reads for the live counter line, readouts and tables (fall run only: the season starts Aug 1, and the table's whole-year row is swapped for a since-Aug-1 row). |
| `data/counts_daily.csv` | Running record of raw daily up/down counts and water temperature (2023–25 falls seeded for calibration). |

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

## Live counts

The black line on the charts, the "Live counter" readouts and the Up / Down / Up−Down tables come from
the Vaki RiverWatcher pages — Ganaraska `www.riverwatcherdaily.is?I=133`, Credit `?I=143`. The counter
id lives in an ASP.NET session cookie, and the page embeds the table at the bottom (`jsonSummary`) and
the daily series behind the bar graph (`jsonOverView`) in hidden inputs; `scripts/fetch_counts.py`
reads both (asking for Jan 1 → today via the Redraw postback) and writes `data/counts.json` and
`data/counts_daily.csv`.

- **Schedule:** `.github/workflows/update-counts.yml` runs at 10:15 and 23:05 UTC (≈ 6:15 am and
  7:05 pm ET), commits when the numbers changed, and GitHub Pages republishes. Run it any time from the
  repo's *Actions* tab → *Update live counts* → *Run workflow*. The script stops itself after Dec 1
  (`--until`). Edit the two `cron:` lines to change the cadence.
- **Requirements:** Actions enabled on the repo (default) — the workflow carries its own
  `contents: write` permission, so no token setup is needed.
- **Run locally:** `pip install requests beautifulsoup4 lxml` then `python scripts/fetch_counts.py`
  (`--season-start 2026-08-01` is the default; the season total and the plotted line start there).
- **What the numbers are:** the counter's raw, unclassified counts — every species, net of fish that
  went back down, no technician review. They are context, not the official Chinook totals the pool is
  scored on. Calibration from the same source, Aug 1–Nov 30 raw net vs. the official Chinook count:
  Ganaraska 24,150 → 28,294 (2023), 22,639 → 19,514 (2024), 22,231 → 17,638 (2025);
  Credit 8,457 → 7,938, 7,466 → 6,501, 11,312 → 9,748. So official ≈ 0.79–1.17× raw on the
  Ganaraska and 0.86–0.94× on the Credit.
- The page fails quietly if `data/counts.json` is missing or unreachable (e.g. opened from disk):
  the charts simply show no live line.

*No lake whitefish appear anywhere in this repository. Cool fish only.*
