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
