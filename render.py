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
SECTION_ORDER = ["top", "fed", "listen", "watch", "read"]
SECTION_TITLES = {
    "top": "Top of mind",
    "fed": "Fed watch",
    "listen": "Listen",
    "watch": "Watch",
    "read": "Read",
}
ITEM_FIELDS = {"id", "title", "url", "source", "meta", "summary", "why"}


def fail(msg):
    sys.exit(f"render.py: {msg}")


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
            fail(f"unknown section key {sec.get('key')!r}; use one of {SECTION_ORDER}")
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
            if not it["url"].startswith(("https://", "http://")):
                fail(f"item {it['id']!r} url must be absolute")
            seen.add(it["id"])
    for r in d.get("radar", []):
        if not {"when", "what"} <= r.keys():
            fail("radar entries need 'when' and 'what'")


def render_item(sec_key, it):
    a = lambda k: escape(it.get(k, ""), quote=True)  # noqa: E731
    source = " · ".join(escape(x) for x in (it.get("source"), it.get("meta")) if x)
    why = (
        f'<p class="item-why"><span class="why-label">Why it matters</span> {a("why")}</p>'
        if it.get("why") else ""
    )
    return f"""
      <article class="item" data-id="{a('id')}" data-section="{sec_key}" data-title="{a('title')}" data-source="{a('source')}" data-url="{a('url')}">
        <div class="item-body">
          {f'<p class="item-source">{source}</p>' if source else ''}
          <h3 class="item-title"><a href="{a('url')}" target="_blank" rel="noopener">{a('title')}</a></h3>
          <div class="item-more">
            <p class="item-summary">{a('summary')}</p>
            {why}
          </div>
        </div>
        <div class="item-actions">
          <button type="button" class="act act-done" aria-pressed="false" aria-label="Mark done" title="Done">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>
          </button>
          <button type="button" class="act act-nope" aria-pressed="false" aria-label="Not for me" title="Not for me">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"/></svg>
          </button>
        </div>
      </article>"""


def render_sections(d):
    by_key = {s["key"]: s for s in d["sections"]}
    out = []
    for key in SECTION_ORDER:
        sec = by_key.get(key)
        if not sec or not sec.get("items"):
            continue
        items = "".join(render_item(key, it) for it in sec["items"])
        out.append(f"""
    <section class="section" id="{key}">
      <h2 class="section-title">{SECTION_TITLES[key]}<span class="section-count">{len(sec['items'])}</span></h2>
      {items}
    </section>""")
    return "".join(out)


def render_radar(d):
    rows = d.get("radar", [])
    if not rows:
        return ""
    lis = "".join(
        f'<li><span class="radar-when">{escape(r["when"])}</span><span class="radar-what">{escape(r["what"])}</span></li>'
        for r in rows
    )
    return f"""
    <section class="section" id="radar">
      <h2 class="section-title">On the radar</h2>
      <ul class="radar">{lis}</ul>
    </section>"""


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
        "{{WEEKDAY}}": f"{day:%A}",
        "{{DATE_LONG}}": f"{day:%B} {day.day}, {day:%Y}",
        "{{GENERATED}}": f"{gen.hour % 12 or 12}:{gen:%M}{'am' if gen.hour < 12 else 'pm'} ET",
        "{{LEDE}}": escape(d["lede"]),
        "{{SECTIONS}}": render_sections(d),
        "{{RADAR}}": render_radar(d),
        "{{FEEDBACK_NOTE}}": f'<p class="feedback-note">{escape(note)}</p>' if note else "",
        "{{LATEST_LINK}}": "" if is_latest else f'<a class="latest-link" href="{base}index.html">Today →</a>',
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
    return f"""{head}<body data-page="archive">
  <main class="wrap">
    <header class="masthead">
      <div class="masthead-row"><a class="brand" href="../index.html">Daily Brief</a></div>
      <h1 class="date-line">Archive</h1>
    </header>
    <section class="section"><ul class="radar archive">{''.join(rows)}</ul></section>
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
