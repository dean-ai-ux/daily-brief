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
  — speeches, interviews, testimony, op-eds, podcast appearances (last 72h).
- **Macro:** what moved markets yesterday; data released yesterday or due today.
- **Y Combinator:** important news only (batch/Demo Day, program or policy changes,
  big YC-company raises/exits, partner essays).
- **Karpathy:** new posts, talks, videos, repos, notable threads (last 7 days).
- **New cool thing on YouTube:** what tool/technique/build in AI or tech is taking off
  this week, and 1–2 *smaller* creators' videos demoing it (last 7 days). Link the video.
- **Podcasts:** if any podcast feed failed, search for its latest episode. Also check for
  Warsh/Powell/Goolsbee/Karpathy guesting on other shows this week.
- **On the radar:** this week's economic calendar (CPI, jobs, FOMC, minutes, GDP, major
  earnings) and anything Dean should expect in the next 7 days.

**Accuracy rules — non-negotiable**
- Only use URLs you actually saw in the feed output or search results. Never construct or
  guess a URL. If you can't find a real link, drop the item.
- Prefer the original article/episode page over aggregators. For an audio-only podcast
  link (`.mp3`), search for the episode's page (show site, Apple Podcasts, Spotify) and use
  that if found; otherwise the .mp3 is acceptable.
- Don't state facts you didn't read. Summaries come from what the source says.

## 3. Choose
Target ~5-minute skim, **12–18 items total**:
| Section key | Title | Count | What belongs |
|---|---|---|---|
| `top` | Top of mind | 3–5 | The developments that matter most to Dean today (macro, Fed, YC, industry, AI). Each needs a `why`. |
| `fed` | Fed watch | 0–3 | Anything Powell, Warsh or Goolsbee said/wrote, plus key Fed releases. Omit the section if nothing new. |
| `listen` | Listen | 1–3 | Podcast episodes worth the commute. Odd Lots only when the guest clears the bar (Goolsbee-level). |
| `watch` | Watch | 1–3 | Karpathy when there's something new; 1–2 "new cool thing" videos from smaller YouTubers. |
| `read` | Read | 3–5 | Best articles from WSJ, The Economist, NYT (others fine). Mix of news and one longer read. |

Rank by: matches interests.md → feedback patterns → genuine importance → novelty.
A story in `top` should not also appear in `read`.

## 4. Write `data/$TODAY.json`
The page is a dashboard: each item shows as one compact row, and tapping it opens a detail
panel with the summary, why it matters, **Go deeper** bullets and **Related** links. The
click-in is where Dean learns more, so fill `deeper` and `related` for every `top` and `fed`
item and wherever else you have good material.
```json
{
  "date": "2026-10-12",
  "generated": "2026-10-12T07:31:00-04:00",
  "lede": "One or two sentences (≤ 45 words): the shape of the morning in plain English.",
  "feedback_note": "Optional, one line: how yesterday's marks changed today's picks. Omit if none.",
  "snapshot": [
    {"label": "10-yr Treasury", "value": "5.29%", "note": "Oct 8 · near 2002 high", "url": "https://…"}
  ],
  "sections": [
    {"key": "top", "items": [
      {
        "id": "nobel-hall-woodford",
        "title": "Headline in sentence case (≤ 80 chars; it's clamped to 2 lines)",
        "url": "https://…",
        "source": "NYT",
        "meta": "Optional: '6 min read' / '58 min · guest: Austan Goolsbee' / 'YouTube · 14 min'",
        "summary": "Two sentences max: what happened.",
        "why": "One sentence: why it matters to Dean. Required in top; optional elsewhere.",
        "deeper": ["2–4 short factual bullets of context, numbers, history or what to watch next."],
        "related": [{"title": "Source: headline", "url": "https://…"}]
      }
    ]},
    {"key": "fed", "items": []},
    {"key": "listen", "items": []},
    {"key": "watch", "items": []},
    {"key": "read", "items": []}
  ],
  "radar": [
    {"when": "Wed Oct 14", "what": "September CPI, 8:30am ET"}
  ]
}
```
- `snapshot`: 3–4 market/macro tiles (e.g. 10-yr yield, oil, S&P 500, Fed funds, next big
  data print). **Only numbers you read in a source today, with the as-of date in `note`.**
  If you can't source a number, leave that tile out. `url` optional.
- `deeper`: at most 5 strings. `related`: at most 4 links, each `{"title", "url"}`, from
  URLs you actually saw. Both optional; omit rather than pad.
- `id`: short kebab-case, unique within the day (3–60 chars, a–z 0–9 -).
- `generated`: current ET time with offset (`TZ=America/New_York date -Iseconds`).
- Allowed item fields only: id, title, url, source, meta, summary, why, deeper, related.
- Plain text everywhere (no markdown, no HTML). Tight, specific, no hype.

## 5. Render and check
```bash
python3 render.py data/$TODAY.json
```
If it fails, fix the JSON and re-run. Don't edit `template.html` or `render.py` in a
routine run.

## 6. Learn
If the last 30 days of feedback show a **clear new pattern** (e.g. 3+ ✗ on the same kind of
item), add one dated line under **Learned from feedback** in `interests.md`, e.g.
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
