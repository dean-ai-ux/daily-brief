# Daily Brief

Dean's morning brief, rebuilt by a Claude routine every day at 7:30am ET and served by GitHub Pages.

- **Read it:** https://dean-ai-ux.github.io/daily-brief/
- **Tune it:** edit [`interests.md`](interests.md). Plain English; the routine reads it every morning.
- **How the run works:** [`ROUTINE.md`](ROUTINE.md) — `gather.py` pulls feeds from `sources.json`, Claude
  adds web search, writes `data/<date>.json`, and `render.py` builds `index.html` + `archive/`.
- **Feedback:** ✓/✗ on the page sync to `feedback/<date>.json` (once a token is added in *Sync settings*).
