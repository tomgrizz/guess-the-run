#!/usr/bin/env python3
"""Fetch the live fish-counter numbers for the Run Pool site.

Source: Vaki RiverWatcher Daily
    Ganaraska (Corbett Dam)   https://www.riverwatcherdaily.is/?I=133
    Credit (Streetsville)     https://www.riverwatcherdaily.is/?I=143

How the site works: `?I=<id>` stores the counter in an ASP.NET session cookie and
redirects to /Migration. That page embeds two JSON blobs in hidden inputs:
    jsonSummary   the table at the bottom of the page
                  (Today / Yesterday / Last 7 days / Last 30 days / This year,
                   with Up / Down / Up-Down)
    jsonOverView  the daily series behind the bar graph
                  (Time, CountUp, CountDown, Temp; count rows and temperature rows
                   are separate entries)
A "Redraw" postback with ISO dates selects the window; we ask for Jan 1 -> today.

These are the counter's RAW, unclassified numbers: every species, not technician
validated. Net = up - down. They are context for the pool, not the official totals.

Writes  data/counts.json        read by index.html
        data/counts_daily.csv   running record, one row per river-day (counts + temp)

Run     python scripts/fetch_counts.py [--season-start 2026-08-01] [--until 2026-12-01]
Needs   requests, beautifulsoup4, lxml
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE = "https://www.riverwatcherdaily.is"
COUNTERS = {
    "gan": {"id": 133, "expect": "Ganaraska"},
    "cre": {"id": 143, "expect": "Credit"},
}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) run-pool-counts/1.0"}
ET = ZoneInfo("America/Toronto")
ROOT = Path(__file__).resolve().parents[1]
P = "ctl00$ContentPlaceHolder1$"          # ASP.NET control-name prefix
PID = "ctl00_ContentPlaceHolder1_"        # ...and the matching element-id prefix


def to_int(v) -> int:
    try:
        return int(str(v).strip() or 0)
    except ValueError:
        return 0


def hidden(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("input", id=PID + name)
    return (tag.get("value") or "") if tag else ""


def form_fields(soup: BeautifulSoup) -> dict[str, str]:
    """Every input in the ASP.NET form (viewstate included) except the submit buttons."""
    out = {}
    for inp in soup.find("form").find_all("input"):
        n = inp.get("name")
        if n and inp.get("type") != "submit":
            out[n] = inp.get("value") or ""
    return out


def get_with_retry(sess: requests.Session, method: str, url: str, **kw) -> requests.Response:
    last = None
    for attempt in range(3):
        try:
            r = sess.request(method, url, timeout=60, **kw)
            r.raise_for_status()
            return r
        except requests.RequestException as e:      # noqa: PERF203
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{method} {url} failed after 3 attempts: {last}")


def parse_overview(soup: BeautifulSoup) -> dict[str, dict]:
    """Daily rows keyed by ISO date: {'up': int, 'down': int (positive), 'temp': float|None}."""
    raw = hidden(soup, "jsonOverView")
    rows = json.loads(raw).get("Table1", []) if raw else []
    days: dict[str, dict] = {}
    for r in rows:
        d = days.setdefault(r["Time"], {"up": 0, "down": 0, "temp": None, "counted": False})
        if r.get("CountUp", "") != "" or r.get("CountDown", "") != "":
            d["up"] += to_int(r.get("CountUp"))
            d["down"] += abs(to_int(r.get("CountDown")))
            d["counted"] = True
        if r.get("Temp", "") != "":
            try:
                d["temp"] = round(float(r["Temp"]), 2)
            except ValueError:
                pass
    return days


def parse_summary(soup: BeautifulSoup) -> list[dict]:
    raw = hidden(soup, "jsonSummary")
    rows = json.loads(raw) if raw else []
    return [{"label": r.get("Text", ""), "up": to_int(r.get("Up")),
             "down": to_int(r.get("Down")), "net": to_int(r.get("Netto"))} for r in rows]


def fetch_counter(key: str, cfg: dict, today: dt.date) -> dict:
    sess = requests.Session()
    sess.headers.update(UA)
    r = get_with_retry(sess, "GET", f"{BASE}/?I={cfg['id']}")
    soup = BeautifulSoup(r.text, "lxml")
    name = hidden(soup, "hfRiverName")
    if cfg["expect"].lower() not in name.lower():
        raise RuntimeError(f"{key}: expected a {cfg['expect']} page, got {name!r}")

    # Ask for the whole year so the season-to-date sum never depends on the default window.
    fields = form_fields(soup)
    fields[P + "fromDayInput"] = f"{today.year}-01-01"
    fields[P + "toDayInput"] = today.isoformat()
    fields[P + "btnRedraw"] = "Redraw"
    try:
        p = get_with_retry(sess, "POST", f"{BASE}/Migration", data=fields)
        soup2 = BeautifulSoup(p.text, "lxml")
        if str(today.year) in hidden(soup2, "GraphTitle") and hidden(soup2, "jsonOverView"):
            soup = soup2
        else:
            print(f"  {key}: redraw postback did not return the requested window; using default view")
    except RuntimeError as e:
        print(f"  {key}: redraw postback failed ({e}); using default view")

    days = parse_overview(soup)
    summary = parse_summary(soup)
    counted = {d: v for d, v in days.items() if v["counted"]}
    return {"key": key, "id": cfg["id"], "name": name, "days": days, "counted": counted,
            "summary": summary, "title": hidden(soup, "GraphTitle")}


def build_json(results: dict, today: dt.date, season_start: str, fetched_utc: str, previous: dict | None) -> dict:
    out = {
        "updated": fetched_utc,
        "as_of": today.isoformat(),
        "season_start": season_start,
        "source": BASE,
        "note": ("Raw RiverWatcher counter numbers: every species, net = up - down, not technician "
                 "validated. Context only; the pool is scored on the official Chinook totals."),
    }
    for key, cfg in COUNTERS.items():
        res = results.get(key)
        if res is None:                                   # keep yesterday's data, flag it
            prev = (previous or {}).get(key)
            if prev:
                prev = dict(prev, stale=True)
                out[key] = prev
            continue
        counted = res["counted"]
        season_days = sorted(d for d in counted if d >= season_start)
        s_up = sum(counted[d]["up"] for d in season_days)
        s_down = sum(counted[d]["down"] for d in season_days)
        # The site's table, fall-run only: the "This year" row (spring steelhead included)
        # is replaced by the season-to-date row summed from the daily series.
        start_lbl = dt.date.fromisoformat(season_start).strftime("%b %d").replace(" 0", " ")
        summary = [r for r in res["summary"] if r["label"].strip().lower() != "this year"]
        summary.append({"label": f"Fall run, since {start_lbl}", "up": s_up, "down": s_down,
                        "net": s_up - s_down})
        out[key] = {
            "counter_id": res["id"],
            "name": res["name"],
            "url": f"{BASE}/?I={res['id']}",
            "window": res["title"],
            "last_day": max(counted) if counted else None,
            "summary": summary,
            "season": {"up": s_up, "down": s_down, "net": s_up - s_down, "days": len(season_days)},
            "daily": [[d, counted[d]["up"], counted[d]["down"]] for d in season_days],
        }
    return out


def dump_json(data: dict, path: Path) -> None:
    """Pretty JSON with each daily row on its own line (small, diff-friendly)."""
    def enc(obj, ind=0):
        pad = " " * ind
        if isinstance(obj, dict):
            items = [f'{pad}  {json.dumps(k)}: {enc(v, ind + 2)}' for k, v in obj.items()]
            return "{\n" + ",\n".join(items) + f"\n{pad}}}"
        if isinstance(obj, list):
            if obj and all(isinstance(x, list) for x in obj):          # daily rows
                return "[\n" + ",\n".join(f"{pad}  {json.dumps(x)}" for x in obj) + f"\n{pad}]"
            if obj and all(isinstance(x, dict) for x in obj):           # summary rows
                return "[\n" + ",\n".join(f"{pad}  {json.dumps(x)}" for x in obj) + f"\n{pad}]"
            return json.dumps(obj)
        return json.dumps(obj)
    path.write_text(enc(data) + "\n", encoding="utf-8")


def update_csv(results: dict, today: dt.date, path: Path) -> None:
    cols = ["river", "date", "up", "down", "net", "temp_c"]
    rows: dict[tuple, dict] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[(r["river"], r["date"])] = r
    for key, res in results.items():
        if res is None:
            continue
        # this year's rows are replaced wholesale (the site can revise past days)
        for k in [k for k in rows if k[0] == key and k[1].startswith(str(today.year))]:
            del rows[k]
        for d, v in res["days"].items():
            rows[(key, d)] = {"river": key, "date": d,
                              "up": v["up"] if v["counted"] else "",
                              "down": v["down"] if v["counted"] else "",
                              "net": (v["up"] - v["down"]) if v["counted"] else "",
                              "temp_c": "" if v["temp"] is None else v["temp"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for k in sorted(rows):
            w.writerow({c: rows[k].get(c, "") for c in cols})


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch RiverWatcher counts for the Run Pool site")
    ap.add_argument("--season-start", default=None,
                    help="ISO date; daily rows and the season total start here (default Aug 1 of this year)")
    ap.add_argument("--until", default=None,
                    help="ISO date; after this the script exits without touching files (default Dec 1)")
    ap.add_argument("--out", default=str(ROOT / "data"), help="output directory (default data/)")
    a = ap.parse_args()

    now_utc = dt.datetime.now(dt.timezone.utc)
    today = now_utc.astimezone(ET).date()
    season_start = a.season_start or f"{today.year}-08-01"
    until = dt.date.fromisoformat(a.until) if a.until else dt.date(today.year, 12, 1)
    if today > until:
        print(f"{today} is past --until {until}; season over, nothing to do.")
        return 0

    out_dir = Path(a.out)
    json_path, csv_path = out_dir / "counts.json", out_dir / "counts_daily.csv"
    previous = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else None

    results, failures = {}, []
    for key, cfg in COUNTERS.items():
        try:
            res = fetch_counter(key, cfg, today)
            results[key] = res
            s = res["counted"]
            season = [d for d in s if d >= season_start]
            print(f"  {key}: {res['name']} | {res['title']} | days with fish {len(s)} | "
                  f"since {season_start}: up {sum(s[d]['up'] for d in season)} "
                  f"down {sum(s[d]['down'] for d in season)} | last day {max(s) if s else None}")
            for row in res["summary"]:
                print(f"      {row['label']:<13} up {row['up']:>6}  down {row['down']:>6}  net {row['net']:>6}")
        except Exception as e:                            # noqa: BLE001
            print(f"  {key}: FAILED - {e}")
            results[key] = None
            failures.append(key)

    if len(failures) == len(COUNTERS):
        print("Both counters failed; leaving files untouched.")
        return 1

    data = build_json(results, today, season_start, now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), previous)
    out_dir.mkdir(parents=True, exist_ok=True)
    dump_json(data, json_path)
    update_csv(results, today, csv_path)
    print(f"wrote {json_path} and {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
