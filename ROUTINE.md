# Morning routine — build today's brief

You are producing Dean's daily brief. Follow these steps exactly, in order.
The page is read on a phone on the commute; quality and accuracy beat volume.

## 0. Setup and guard
```bash
TODAY=$(TZ=America/New_York date +%F)
git pull --rebase origin main
```
- If `data/$TODAY.json` already exists, **stop** — today's brief is done (this routine may be
  scheduled twice around daylight-saving changes; only the first run should do anything).

## 1. Read context
- `interests.md` — the profile. Its **Learned from feedback** section overrides defaults.
- `feedback/*.json` from the last 30 days. Each has items marked `done` (Dean used it) or
  `nope` (Dean didn't want it), with title, section and source. Look for patterns
  (a show, a guest type, a source, a topic) rather than reacting to single items.
- `data/*.json` from the last 7 days — **never repeat** an item (same URL or same story).

## 2. Gather candidates
```bash
python3 gather.py > /tmp/candidates.md
```
Read `/tmp/candidates.md`. Then run web searches to fill what feeds can't cover.
Restrict to the last ~36 hours unless noted:
- **WSJ** (no RSS, and the search tool can't filter to wsj.com): search for
  "Wall Street Journal" + economy / markets / Fed / business / tech. Link wsj.com URLs when
  results include them; otherwise a reputable syndication of the WSJ story is fine.
- **Fed people:** latest from **Kevin Warsh**, **Jerome Powell**, **Austan Goolsbee**
  — speeches, interviews, testimony, op-eds, podcast appearances (last 72h). Gather it, but
  remember the one-Fed-item cap in step 3; extra Fed material goes into that item's `deeper`.
- **AI & the new thing:** model and tool launches, what builders are excited about (Hacker
  News front page is a good signal), notable AI-and-society stories.
- **Business stories:** how companies actually work — strategy, competition, founders'
  decisions, surprising second-order effects (NYT Business, Economist Business, WSJ).
- **Wildcard:** one excellent piece *outside* Dean's lanes (science, history, design, maths,
  culture) — high-signal, e.g. a top Hacker News thread or a standout longread.
- **Macro:** what moved markets yesterday; data released yesterday or due today.
- **Y Combinator:** important news only (batch/Demo Day, program or policy changes,
  big YC-company raises/exits, partner essays).
- **Karpathy:** new posts, talks, videos, repos, notable threads (last 7 days).
- **New cool thing on YouTube:** what tool/technique/build in AI or tech is taking off
  this week, and 1–2 *smaller* creators' videos demoing it (last 7 days). Link the video.
- **Podcasts:** if any podcast feed failed, search for its latest episode. Also check for
  Warsh/Powell/Goolsbee/Karpathy guesting on other shows this week.
- **This week:** this week's economic calendar (CPI, jobs, FOMC, minutes, GDP, major
  earnings) and anything Dean should expect in the next 7 days.

**Accuracy rules — non-negotiable**
- Only use URLs you actually saw in the feed output or search results. Never construct or
  guess a URL. If you can't find a real link, drop the item.
- Prefer the original article/episode page over aggregators. For an audio-only podcast
  link (`.mp3`), search for the episode's page (show site, Apple Podcasts, Spotify) and use
  that if found; otherwise the .mp3 is acceptable.
- Don't state facts you didn't read. Summaries come from what the source says.

## 3. Choose
Buckets follow Dean's interests; **format is a tag, not a section**. Target a ~5-minute skim,
**13–16 items total**:
| Section key | Title | Count | What belongs |
|---|---|---|---|
| `lead` | The lead | 2–3 | What Dean would be embarrassed not to know today, from **at least 2 different buckets**. Each needs a `why`. |
| `markets` | Markets & macro | 2–3 | Rates, inflation, growth, energy, trade, markets. The Fed lives here. |
| `ai` | AI & the new thing | 2–3 | Karpathy, model/tool launches, builders' demos, smaller YouTubers showing the new cool thing. |
| `startups` | Startups & YC | 2 | Important YC news, notable YC-company raises/exits, founder or partner essays. |
| `business` | Business stories | 2–3 | How companies work. Acquired and How I Built This usually land here. |
| `wildcard` | Wildcard | 1 | One great pick outside the usual lanes. |

**Blend rules (hard limits)**
- **At most one Fed-specific item per day** across all buckets (including the lead), unless
  it's an FOMC decision day, minutes day, or a major speech/testimony from Warsh, Powell or
  Goolsbee — then at most two. Fold other Fed remarks into that item's `deeper`/`related`.
- No bucket (counting its lead items) above ~30% of the day's items.
- At least **2 `listen`** and **2 `watch`** items across the whole brief. Odd Lots only when
  the guest clears the bar (Goolsbee-level).
- Every item has a `format`: `read`, `listen` or `watch`.
- An item appears once. A lead story doesn't repeat in its bucket.

Rank within each bucket by: interests.md → feedback patterns (including which buckets Dean
✓s or ✗s) → genuine importance → novelty.

## 4. Write `data/$TODAY.json`
The page is a dashboard: each item shows its full headline plus a one-line **gist**, and
tapping it opens a detail panel with the summary, why it matters, **Go deeper** bullets and
**Related** links. Lead items show their summary on the card. Filter chips (All · Read · Listen ·
Watch) use each item's `format`. The click-in is where Dean learns more, so fill `deeper` and
`related` for every lead item and wherever else you have good material.
```json
{
  "date": "2026-10-12",
  "generated": "2026-10-12T07:31:00-04:00",
  "lede": "One or two sentences (≤ 45 words): the shape of the morning in plain English.",
  "feedback_note": "Optional, one line: how yesterday's marks changed today's picks. Omit if none.",
  "snapshot": [
    {"label": "S&P 500", "value": "7,811", "note": "Fri close · +0.59%", "url": "https://…"},
    {"label": "10-yr Treasury", "value": "5.29%", "note": "Oct 8 · near 2002 high", "url": "https://…"},
    {"label": "Next up · Wed", "value": "CPI", "note": "3.6% y/y expected · 8:30am"}
  ],
  "sections": [
    {"key": "lead", "items": [
      {
        "id": "nobel-hall-woodford",
        "title": "Headline in sentence case (≤ 80 chars; shown in full)",
        "url": "https://…",
        "format": "read | listen | watch",
        "source": "NYT",
        "meta": "Optional: '6 min read' / '58 min · guest: Austan Goolsbee' / 'YouTube · 14 min'",
        "gist": "One line (≤ 100 chars): the takeaway, shown under the headline. Don't repeat the title.",
        "summary": "Two sentences max: what happened. Shown in the click-in.",
        "why": "One sentence: why it matters to Dean. Required in lead; optional elsewhere.",
        "deeper": ["2–4 short factual bullets of context, numbers, history or what to watch next."],
        "related": [{"title": "Source: headline", "url": "https://…"}]
      }
    ]},
    {"key": "markets", "items": []},
    {"key": "ai", "items": []},
    {"key": "startups", "items": []},
    {"key": "business", "items": []},
    {"key": "wildcard", "items": []}
  ],
  "radar": [
    {"when": "Wed Oct 14", "what": "September CPI, 8:30am ET"}
  ]
}
```
- `snapshot`: exactly 3 tiles, a blend — one equity index (S&P 500 or Nasdaq), one rate or
  commodity that matters today, and the next big event. `radar` renders as the "This week" strip. **Only numbers you read in a source today, with the as-of date in `note`.**
  If you can't source a number, leave that tile out. `url` optional.
- `deeper`: at most 5 strings. `related`: at most 4 links, each `{"title", "url"}`, from
  URLs you actually saw. Both optional; omit rather than pad.
- `id`: short kebab-case, unique within the day (3–60 chars, a–z 0–9 -).
- `generated`: current ET time with offset (`TZ=America/New_York date -Iseconds`).
- `gist` is required on every item in practice (the page falls back to the summary's first
  sentence, which reads worse). `format` is required.
- Allowed item fields only: id, title, url, format, source, meta, gist, summary, why, deeper, related.
- Plain text everywhere (no markdown, no HTML). Tight, specific, no hype.

## 5. Render and check
```bash
python3 render.py data/$TODAY.json
```
If it fails, fix the JSON and re-run. Don't edit `template.html` or `render.py` in a
routine run.

## 6. Learn
If the last 30 days of feedback show a **clear new pattern** (e.g. 3+ ✗ on the same kind of
item, or a bucket Dean consistently skips or finishes), add one dated line under **Learned from feedback** in `interests.md`, e.g.
`- 2026-10-14: Skips Odd Lots crypto episodes; keeps macro ones.` Don't duplicate an
existing line; at most 2 new lines per day. Never edit other sections of interests.md.

## 7. Publish
```bash
git add data/ archive/ index.html interests.md
git commit -m "brief: $TODAY — <n> items" -m "<one line on what feedback changed, if anything>"
git pull --rebase origin main && git push origin main
```
If the push is rejected (the phone may have just pushed feedback), pull --rebase and push
again, up to 3 tries.
