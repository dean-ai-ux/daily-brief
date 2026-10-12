#!/usr/bin/env python3
"""Render a day's brief from data/YYYY-MM-DD.json into HTML.

Usage: python3 render.py data/2026-10-12.json
Writes archive/<date>.html and archive/index.html, and index.html when <date> is the
newest brief. Validates the JSON first and exits non-zero (writing nothing) if it is malformed.
"""
import json
import re
import sys
from datetime import date, datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
REPO = "dean-ai-ux/daily-brief"
SECTION_TITLES = {
    "top": "Top of mind",
    "fed": "Fed watch",
    "listen": "Listen",
    "watch": "Watch",
    "read": "Read",
}
ITEM_FIELDS = {"id", "title", "url", "source", "meta", "summary", "why", "deeper", "related"}
SNAPSHOT_FIELDS = {"label", "value", "note", "url"}


def fail(msg):
    sys.exit(f"render.py: {msg}")


def is_url(u):
    return isinstance(u, str) and u.startswith(("https://", "http://"))


def validate(d):
    for key in ("date", "generated", "lede", "sections"):
        if key not in d:
            fail(f"missing top-level '{key}'")
    try:
        date.fromisoformat(d["date"])
        datetime.fromisoformat(d["generated"])
    except ValueError as e:
        fail(f"bad date: {e}")
    seen = set()
    for sec in d["sections"]:
        if sec.get("key") not in SECTION_TITLES:
            fail(f"unknown section key {sec.get('key')!r}; use one of {list(SECTION_TITLES)}")
        for it in sec.get("items", []):
            missing = {"id", "title", "url", "summary"} - it.keys()
            if missing:
                fail(f"item {it.get('id', it.get('title'))!r} missing {sorted(missing)}")
            extra = it.keys() - ITEM_FIELDS
            if extra:
                fail(f"item {it['id']!r} has unknown fields {sorted(extra)}")
            if not re.fullmatch(r"[a-z0-9-]{3,60}", it["id"]):
                fail(f"item id {it['id']!r} must be 3-60 chars of a-z, 0-9, '-'")
            if it["id"] in seen:
                fail(f"duplicate item id {it['id']!r}")
            if not is_url(it["url"]):
                fail(f"item {it['id']!r} url must be absolute")
            deeper = it.get("deeper", [])
            if not (isinstance(deeper, list) and all(isinstance(x, str) for x in deeper)) or len(deeper) > 5:
                fail(f"item {it['id']!r} 'deeper' must be a list of at most 5 strings")
            related = it.get("related", [])
            if not isinstance(related, list) or len(related) > 4:
                fail(f"item {it['id']!r} 'related' must be a list of at most 4 links")
            for r in related:
                if not (isinstance(r, dict) and r.keys() == {"title", "url"} and is_url(r["url"])):
                    fail(f"item {it['id']!r} related links need exactly 'title' and an absolute 'url'")
            seen.add(it["id"])
    for r in d.get("radar", []):
        if not {"when", "what"} <= r.keys():
            fail("radar entries need 'when' and 'what'")
    snap = d.get("snapshot", [])
    if len(snap) > 6:
        fail("snapshot holds at most 6 tiles")
    for s in snap:
        if not {"label", "value"} <= s.keys() or s.keys() - SNAPSHOT_FIELDS:
            fail("snapshot tiles need 'label' and 'value' (optional 'note', 'url')")
        if "url" in s and not is_url(s["url"]):
            fail("snapshot url must be absolute")


ACTS = """<div class="row-acts">
            <button type="button" class="act act-done" aria-pressed="false" aria-label="Mark done" title="Done"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></button>
            <button type="button" class="act act-nope" aria-pressed="false" aria-label="Not for me" title="Not for me"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"/></svg></button>
          </div>"""


def render_row(sec_key, it):
    source = " · ".join(escape(x) for x in (it.get("source"), it.get("meta")) if x)
    return f"""
        <li class="row" data-id="{escape(it['id'], quote=True)}">
          <button type="button" class="row-open" aria-haspopup="dialog">
            {f'<span class="row-src">{source}</span>' if source else ''}
            <span class="row-title">{escape(it['title'])}</span>
            <span class="row-sum">{escape(it['summary'])}</span>
          </button>
          {ACTS}
        </li>"""


def render_card(key, title, body, count=None):
    badge = f'<span class="card-count">{count}</span>' if count is not None else ""
    return f"""
    <section class="card card-{key}" id="{key}" aria-labelledby="{key}-h">
      <h2 class="card-title" id="{key}-h">{title}{badge}</h2>
      {body}
    </section>"""


def render_grid(d):
    by_key = {s["key"]: s for s in d["sections"] if s.get("items")}
    cards = []
    for key, title in SECTION_TITLES.items():
        sec = by_key.get(key)
        if sec:
            rows = "".join(render_row(key, it) for it in sec["items"])
            cards.append(render_card(key, title, f'<ul class="rows">{rows}</ul>', len(sec["items"])))
    radar = d.get("radar", [])
    if radar:
        lis = "".join(
            f'<li><span class="radar-when">{escape(r["when"])}</span><span class="radar-what">{escape(r["what"])}</span></li>'
            for r in radar
        )
        cards.append(render_card("radar", "On the radar", f'<ul class="radar">{lis}</ul>'))
    flags = " ".join(f"has-{k}" for k in list(by_key) + (["radar"] if radar else []))
    return f'<div class="grid {flags}">{"".join(cards)}</div>'


def render_snapshot(d):
    tiles = []
    for s in d.get("snapshot", []):
        inner = (
            f'<span class="tile-label">{escape(s["label"])}</span>'
            f'<span class="tile-value">{escape(s["value"])}</span>'
            + (f'<span class="tile-note">{escape(s["note"])}</span>' if s.get("note") else "")
        )
        if s.get("url"):
            tiles.append(f'<a class="tile" href="{escape(s["url"], quote=True)}" target="_blank" rel="noopener">{inner}</a>')
        else:
            tiles.append(f'<div class="tile">{inner}</div>')
    return f'<div class="snapshot">{"".join(tiles)}</div>' if tiles else ""


def page_data(d):
    """Item details the click-in panel needs, embedded as JSON."""
    items = []
    for sec in d["sections"]:
        for it in sec.get("items", []):
            items.append({
                "id": it["id"], "section": sec["key"], "sectionTitle": SECTION_TITLES[sec["key"]],
                "title": it["title"], "url": it["url"], "source": it.get("source", ""),
                "meta": it.get("meta", ""), "summary": it["summary"], "why": it.get("why", ""),
                "deeper": it.get("deeper", []), "related": it.get("related", []),
            })
    # "</" would let item text close the <script> tag early
    return json.dumps({"items": items}, ensure_ascii=False).replace("</", "<\\/")


def render_page(d, base, is_latest):
    template = (ROOT / "template.html").read_text()
    day = date.fromisoformat(d["date"])
    gen = datetime.fromisoformat(d["generated"])
    note = d.get("feedback_note", "")
    subs = {
        "{{BASE}}": base,
        "{{DATE}}": d["date"],
        "{{REPO}}": REPO,
        "{{TITLE}}": f"Brief · {day:%a %b} {day.day}",
        "{{DATE_SHORT}}": f"{day:%a %b} {day.day}",
        "{{DATE_LONG}}": f"{day:%A, %B} {day.day}",
        "{{GENERATED}}": f"{gen.hour % 12 or 12}:{gen:%M}{'am' if gen.hour < 12 else 'pm'} ET",
        "{{LEDE}}": escape(d["lede"]),
        "{{SNAPSHOT}}": render_snapshot(d),
        "{{GRID}}": render_grid(d),
        "{{FEEDBACK_NOTE}}": f'<p class="feedback-note">{escape(note)}</p>' if note else "",
        "{{LATEST_LINK}}": "" if is_latest else f'<a class="latest-link" href="{base}index.html">Today →</a>',
        "{{DATA}}": page_data(d),
    }
    for k, v in subs.items():
        template = template.replace(k, v)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", template)
    if leftover:
        fail(f"template placeholders not filled: {leftover}")
    return template


def render_archive_index():
    rows = []
    for p in sorted((ROOT / "data").glob("*.json"), reverse=True):
        d = json.loads(p.read_text())
        day = date.fromisoformat(d["date"])
        rows.append(
            f'<li><a href="{d["date"]}.html"><span class="radar-when">{day:%a %b} {day.day}</span>'
            f'<span class="radar-what">{escape(d["lede"])}</span></a></li>'
        )
    page = (ROOT / "template.html").read_text()
    # Reuse the template's head and styles; swap the body for a plain list.
    head = page.split("<body", 1)[0].replace("{{TITLE}}", "Brief · Archive").replace("{{BASE}}", "../")
    return f"""{head}<body class="archive-page">
  <header class="top"><div class="top-row">
    <a class="brand" href="../index.html">Daily Brief</a><span class="top-date">Archive</span>
  </div></header>
  <main class="wrap">
    <section class="card"><ul class="radar archive">{''.join(rows)}</ul></section>
  </main>
</body>
</html>
"""


def main():
    if len(sys.argv) != 2:
        fail("usage: python3 render.py data/YYYY-MM-DD.json")
    d = json.loads(Path(sys.argv[1]).read_text())
    validate(d)
    newest = max(p.stem for p in (ROOT / "data").glob("*.json"))
    is_latest = d["date"] >= newest
    (ROOT / "archive").mkdir(exist_ok=True)
    (ROOT / "archive" / f"{d['date']}.html").write_text(render_page(d, "../", is_latest))
    if is_latest:
        (ROOT / "index.html").write_text(render_page(d, "", True))
    (ROOT / "archive" / "index.html").write_text(render_archive_index())
    n = sum(len(s.get("items", [])) for s in d["sections"])
    print(f"rendered {d['date']}: {n} items{' (index.html updated)' if is_latest else ''}")


if __name__ == "__main__":
    main()
