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
# Buckets follow Dean's interests; format (read/listen/watch) is a tag on each item.
SECTION_TITLES = {
    "lead": "The lead",
    "markets": "Markets & macro",
    "ai": "AI & the new thing",
    "startups": "Startups & YC",
    "business": "Business stories",
    "wildcard": "Wildcard",
}
# Generated print on each folder's tab strip (see PRESETS in template.html)
SECTION_ART = {"lead": "aurora", "markets": "verdant", "ai": "ember", "startups": "glacier", "business": "dusk", "wildcard": "tide"}
FORMATS = {"read": "Read", "listen": "Listen", "watch": "Watch"}
ITEM_FIELDS = {"id", "title", "url", "format", "source", "meta", "gist", "summary", "why", "deeper", "related"}
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
            if it.get("format", "read") not in FORMATS:
                fail(f"item {it['id']!r} format must be one of {list(FORMATS)}")
            if len(it.get("gist", "")) > 120:
                fail(f"item {it['id']!r} gist must be one line (≤ 120 chars)")
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


CHECK = """<button type="button" class="act act-done" aria-pressed="false" aria-label="Mark done" title="Done"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 12.5l3.5 3.5 7.5-8"/></svg></button>"""
NOPE = """<button type="button" class="act act-nope" aria-pressed="false" aria-label="Not for me" title="Not for me"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 8l8 8M16 8l-8 8"/></svg></button>"""


def gist_of(it):
    """The one-line takeaway; falls back to the summary's first sentence."""
    if it.get("gist"):
        return it["gist"]
    first = re.split(r"(?<=[.!?])\s", it["summary"], maxsplit=1)[0]
    return first


def render_row(it, lead=False):
    fmt = it.get("format", "read")
    source = " · ".join(escape(x) for x in (it.get("source"), it.get("meta")) if x)
    tag = f'<span class="fmt fmt-{fmt}">{FORMATS[fmt]}</span>'
    if lead:
        body = f'<span class="row-sum">{escape(it["summary"])}</span>'
    else:
        body = f'<span class="row-gist">{escape(gist_of(it))}</span>'
    return f"""
        <li class="row{' row-lead' if lead else ''}" data-id="{escape(it['id'], quote=True)}" data-format="{fmt}">
          {CHECK}
          <button type="button" class="row-open" aria-haspopup="dialog">
            <span class="row-title">{escape(it['title'])}</span>
            {body}
            <span class="row-src">{tag}{source}</span>
          </button>
          {NOPE}
        </li>"""


MAX_SHEETS = 4


def render_sheet(it, depth, slot):
    """A file in the folder's pocket: rises out of the top on hover, opens the item on click."""
    fmt = it.get("format", "read")
    if fmt == "read":
        face = '<span class="sheet-lines"><i></i><i></i><i></i><i></i></span>'
    else:
        face = '<canvas class="sheet-art"></canvas>'
    return (
        f'<button type="button" class="sheet sheet--{fmt}" data-id="{escape(it["id"], quote=True)}" tabindex="-1" style="--d:{depth};--s:{slot:.2f}">'
        f'{face}<span class="sheet-head"><span class="sheet-fmt">{FORMATS[fmt]}</span>'
        f'<span class="sheet-name">{escape(it["title"])}</span></span></button>'
    )


def render_folder(key, title, items):
    """A section as a folder you can open: art on the back, files in the pocket, frosted front."""
    n = len(items)
    shown = items[:MAX_SHEETS]
    # the first item sits at the front of the stack, nearest the glass
    k = len(shown)
    # fan position: -1 (left) … 1 (right); the front sheet sits in the middle-left
    slots = [0.0] if k == 1 else [(i / (k - 1)) * 2 - 1 for i in range(k)]
    sheets = "".join(render_sheet(it, depth, slots[depth]) for depth, it in reversed(list(enumerate(shown))))
    if key == "lead":
        teaser = '<ul class="f-heads">' + "".join(
            f'<li><span class="f-head-title">{escape(it["title"])}</span><span class="f-head-gist">{escape(gist_of(it))}</span></li>'
            for it in items) + "</ul>"
    else:
        teaser = f'<p class="f-teaser">{escape(items[0]["title"])}</p>'
    rows = "".join(render_row(it, lead=(key == "lead")) for it in items)
    return f"""
    <section class="cell folder card-{key}" id="{key}" data-art="{SECTION_ART[key]}" aria-labelledby="{key}-h">
      <div class="f-back" aria-hidden="true"><canvas class="f-art"></canvas><div class="f-sheen"></div></div>
      <div class="f-files" aria-hidden="true">{sheets}</div>
      <div class="f-front">
        <svg class="f-rim" aria-hidden="true"></svg>
        <button type="button" class="f-hit" aria-haspopup="dialog" aria-label="Open {escape(title, quote=True)}, {n} item{'s' if n != 1 else ''}"></button>
        <div class="f-label">
          <h2 class="f-title" id="{key}-h">{title}</h2>
          {teaser}
          <span class="f-meta" data-total="{n}">{n} item{'s' if n != 1 else ''}</span>
        </div>
      </div>
      <div class="f-list" hidden><ul class="rows">{rows}</ul></div>
    </section>"""


def render_week(d):
    rows = d.get("radar", [])
    if not rows:
        return ""
    lis = "".join(
        f'<li><span class="week-when">{escape(r["when"])}</span><span class="week-what">{escape(r["what"])}</span></li>'
        for r in rows
    )
    return f'<section class="cell cell-week" aria-labelledby="week-h"><h2 class="cell-label" id="week-h">This week</h2><ul class="week-list">{lis}</ul></section>'


def render_formats(d):
    counts = {f: 0 for f in FORMATS}
    for sec in d["sections"]:
        for it in sec.get("items", []):
            counts[it.get("format", "read")] += 1
    icons = {
        "read": '<path d="M5 5.5h6a2 2 0 0 1 2 2V19a2 2 0 0 0-2-2H5zM19 5.5h-6a2 2 0 0 0-2 2V19a2 2 0 0 1 2-2h6z"/>',
        "listen": '<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3.5" y="13.5" width="4" height="6" rx="1.5"/><rect x="16.5" y="13.5" width="4" height="6" rx="1.5"/>',
        "watch": '<rect x="3.5" y="5.5" width="17" height="13" rx="3"/><path d="M10.5 9.5v5l4-2.5z"/>',
    }
    btns = "".join(
        f'<button type="button" class="fmt-btn fmt-btn--{f}" data-format="{f}" aria-haspopup="dialog">'
        f'<svg viewBox="0 0 24 24" aria-hidden="true">{icons[f]}</svg><span class="fmt-label">{label}</span>'
        f'<span class="fmt-count">{counts[f]}</span></button>'
        for f, label in FORMATS.items() if counts[f]
    )
    return f'<div class="commute"><span class="commute-label">Commute mode</span><div class="fmt-btns">{btns}</div></div>'


def render_grid(d):
    """Bento: the morning's summary, numbers and week as small tiles; a folder per interest."""
    by_key = {s["key"]: s for s in d["sections"] if s.get("items")}
    note = d.get("feedback_note", "")
    lede = (
        '<section class="cell cell-lede"><h2 class="cell-label">This morning</h2>'
        f'<p class="lede">{escape(d["lede"])}</p>'
        + (f'<p class="feedback-note">{escape(note)}</p>' if note else "")
        + render_formats(d)
        + "</section>"
    )
    stats = render_snapshot(d)
    stats = f'<section class="cell cell-stats" aria-label="Markets">{stats}</section>' if stats else ""
    wildcard = render_folder("wildcard", SECTION_TITLES["wildcard"], by_key["wildcard"]["items"]) if "wildcard" in by_key else ""
    folders = "".join(render_folder(k, SECTION_TITLES[k], by_key[k]["items"]) for k in SECTION_TITLES if k in by_key and k != "wildcard")
    return f'<div class="bento">{lede}{stats}{render_week(d)}{wildcard}{folders}</div>'


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
    return "".join(tiles)


def page_data(d):
    """Item details the click-in panel needs, embedded as JSON."""
    items = []
    for sec in d["sections"]:
        for it in sec.get("items", []):
            items.append({
                "id": it["id"], "section": sec["key"], "sectionTitle": SECTION_TITLES[sec["key"]],
                "title": it["title"], "url": it["url"], "source": it.get("source", ""),
                "format": it.get("format", "read"), "meta": it.get("meta", ""), "gist": gist_of(it), "summary": it["summary"], "why": it.get("why", ""),
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
    <a class="brand" href="../index.html">Daily Brief</a><span class="top-date">ARCHIVE</span>
  </div></header>
  <main class="wrap">
    <section class="paper"><ul class="radar archive">{''.join(rows)}</ul></section>
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
