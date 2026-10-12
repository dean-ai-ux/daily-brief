#!/usr/bin/env python3
"""Pull every feed in sources.json and print recent items as a compact candidate list.

Usage: python3 gather.py > /tmp/candidates.md
Stdlib only. A feed that fails is reported and skipped, never fatal.
"""
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).parent
UA = "Mozilla/5.0 (daily-brief; +https://github.com/dean-ai-ux/daily-brief)"
ATOM = "{http://www.w3.org/2005/Atom}"
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def clean(text, limit=280):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def text_of(el, *tags):
    for tag in tags:
        found = el.find(tag)
        if found is not None and (found.text or "").strip():
            return found.text
    return ""


def parse_feed(raw):
    root = ET.fromstring(raw)
    items = []
    for it in root.iter("item"):
        enclosure = it.find("enclosure")
        items.append({
            "title": text_of(it, "title"),
            # some podcast feeds (art19) have no <link>; fall back to the audio file
            "url": text_of(it, "link").strip()
            or (enclosure.get("url", "") if enclosure is not None else ""),
            "date": parse_date(text_of(it, "pubDate", "{http://purl.org/dc/elements/1.1/}date")),
            "summary": text_of(it, "description", ITUNES + "summary"),
            "duration": text_of(it, ITUNES + "duration"),
        })
    for it in root.iter(ATOM + "entry"):
        link = it.find(ATOM + "link")
        media = it.find("{http://search.yahoo.com/mrss/}group")
        items.append({
            "title": text_of(it, ATOM + "title"),
            "url": link.get("href", "") if link is not None else "",
            "date": parse_date(text_of(it, ATOM + "published", ATOM + "updated")),
            "summary": text_of(it, ATOM + "summary", ATOM + "content")
            or (text_of(media, "{http://search.yahoo.com/mrss/}description") if media is not None else ""),
            "duration": "",
        })
    return items


def fmt_duration(d):
    if not d:
        return ""
    if d.isdigit():
        return f"{round(int(d) / 60)} min"
    parts = [int(p) for p in d.split(":") if p.isdigit()]
    if len(parts) == 3:
        return f"{parts[0] * 60 + parts[1]} min"
    if len(parts) == 2:
        return f"{parts[0]} min"
    return d


def main():
    sources = json.loads((ROOT / "sources.json").read_text())["feeds"]
    now = datetime.now(timezone.utc)
    print(f"# Candidates gathered {now:%Y-%m-%d %H:%M} UTC\n")
    failures = []
    for src in sources:
        try:
            # curl rather than urllib: it uses the system cert store on macOS and Linux alike
            raw = subprocess.run(
                ["curl", "-sSfL", "--max-time", "20", "-A", UA, src["url"]],
                capture_output=True, check=True,
            ).stdout
            items = parse_feed(raw)
        except Exception as e:  # noqa: BLE001 — one bad feed must not stop the brief
            failures.append(f"{src['name']}: {e}")
            continue
        cutoff = now - timedelta(hours=src.get("window_hours", 36))
        recent = [i for i in items if i["date"] and i["date"] >= cutoff]
        recent.sort(key=lambda i: i["date"], reverse=True)
        print(f"## [{src['group']}] {src['name']} — {len(recent)} recent")
        for i in recent[:15]:
            extra = f" · {fmt_duration(i['duration'])}" if i["duration"] else ""
            print(f"- {clean(i['title'], 160)} ({i['date']:%a %b %d}{extra})")
            print(f"  {i['url']}")
            if i["summary"]:
                print(f"  > {clean(i['summary'])}")
        print()
    if failures:
        print("## Feed failures (use web search to cover these)")
        for f in failures:
            print(f"- {f}")


if __name__ == "__main__":
    sys.exit(main())
