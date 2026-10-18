#!/usr/bin/env python3
"""Build an XMLTV guide (guide.xml) for MBC Mauritius TV channels from mbc.mu."""
import re
import sys
import time
import datetime as dt
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup

# (xmltv id, display name, slug on mbc.mu)
# The xmltv id must match the tvg-id in your m3u playlist.
CHANNELS = [
    ("MBC1.mu", "MBC 1", "mbc-1"),
    ("MBC2.mu", "MBC 2", "mbc-2"),
    ("MBC3.mu", "MBC 3", "mbc-3"),
    ("MBC4.mu", "MBC 4", "mbc-4"),
    ("MBC5.mu", "MBC 5", "mbc-5"),
    ("MBC11.mu", "MBC 11", "mbc-11"),
    ("MBC16.mu", "MBC 16", "mbc-16"),
]
DAYS = 7
URL = "https://www.mbc.mu/programme/{slug}"
DATE_PARAM = "date"  # query parameter for the day picker; adjust if needed
MU = dt.timezone(dt.timedelta(hours=4))  # Mauritius, no DST
TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*$")
ID_RE = re.compile(r"/programme/(\d+)/ical")
UA = {"User-Agent": "Mozilla/5.0 (compatible; mbc-epg-builder)"}


def parse_day(html, day):
    """Return [(start_datetime, title, prog_id)] for one page, sorted by start."""
    soup = BeautifulSoup(html, "html.parser")
    seen, items = set(), []
    for a in soup.find_all("a", href=ID_RE):
        pid = ID_RE.search(a["href"]).group(1)
        if pid in seen:
            continue
        seen.add(pid)
        t = a.find_previous(string=TIME_RE)
        title = a.get_text(" ", strip=True)
        if not t or not title:
            continue
        h, m = map(int, TIME_RE.match(t).groups())
        start = dt.datetime.combine(day, dt.time(h % 24, m), tzinfo=MU)
        items.append((start, title, pid))
    items.sort(key=lambda x: x[0])
    return items


def fmt(d):
    return d.strftime("%Y%m%d%H%M%S %z")


def main():
    today = dt.datetime.now(MU).date()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<tv generator-info-name="mbc-mu-epg">']
    for cid, name, _ in CHANNELS:
        out.append(f'<channel id="{cid}"><display-name>{escape(name)}</display-name></channel>')

    total = 0
    for cid, name, slug in CHANNELS:
        first_ids = None
        for i in range(DAYS):
            day = today + dt.timedelta(days=i)
            try:
                r = requests.get(URL.format(slug=slug), params={DATE_PARAM: day.isoformat()},
                                 headers=UA, timeout=30)
                r.raise_for_status()
            except requests.RequestException as e:
                print(f"WARN {name} {day}: {e}", file=sys.stderr)
                continue
            items = parse_day(r.text, day)
            ids = {p for _, _, p in items}
            if i == 0:
                first_ids = ids
            elif ids and ids == first_ids:
                print(f"WARN {name} {day}: same programmes as today - "
                      f"the '{DATE_PARAM}' parameter is probably wrong", file=sys.stderr)
                break
            print(f"{name} {day}: {len(items)} programmes")
            end_of_day = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(0, 0), tzinfo=MU)
            for n, (start, title, _) in enumerate(items):
                stop = items[n + 1][0] if n + 1 < len(items) else end_of_day
                if stop <= start:
                    continue
                out.append(f'<programme start="{fmt(start)}" stop="{fmt(stop)}" channel="{cid}">'
                           f'<title>{escape(title)}</title></programme>')
                total += 1
            time.sleep(1)

    out.append("</tv>")
    if total == 0:
        print("ERROR: no programmes parsed; not writing guide.xml", file=sys.stderr)
        sys.exit(1)
    with open("guide.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Wrote guide.xml with {total} programmes")


if __name__ == "__main__":
    main()
