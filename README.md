# 001: Open RedZone — open-source RedZone-style multiview

**Question:** Can a self-hosted page do RedZone's core trick — a grid of user-supplied stream boxes with an autopilot that jumps the main stage to whichever game is closest to scoring — using only free/open sources?

## Approach
One zero-dependency HTML file (hls.js from CDN only). Boxes = any HLS (.m3u8) or embeddable URL (YouTube etc.), persisted to localStorage. ESPN's free browser-facing scoreboard API (`site.web.api.espn.com`) polled every 15s provides live scores, red-zone flags, down/distance. An "excitement score" (red zone +60, one-score game +25, 4th down +20…) ranks live games; autopilot swaps the main stage when a threshold is hit. Manual click/keys 1–9 always win, autopilot pauses 2 min.

## Verdict: VALIDATED

### What worked
- HLS playback via hls.js — streams attach and play on stage + grid simultaneously (verified: currentTime advancing)
- ESPN live data — real 2026 week's scores flowed into the ticker; red-zone flags, down/distance per game
- Manual override + 2-min autopilot pause — verified via keyboard swap test
- localStorage persistence across reloads
- **Source packs** — paste any M3U playlist URL, browse/search channels, tap to box. Verified with iptv-org sports pack (429 channels, 236 sports keyword hits)
- **CORS-unlocking proxy** (`server.py`) — rewrites manifests + segments through `/proxy?url=`, made the CORS-blocked beIN SPORTS XTRA playable (verified: playhead advancing on stage)
- **DOM-diff render** — streams survive 15s ESPN polls (verified: playhead 42→77→82s across two poll cycles without restart)

### What didn't
- `site.api.espn.com` hard-fails from browser contexts (fetch blocked) — **must** use `site.web.api.espn.com`
- Many pack channels are dead/geo-blocked/HEVC (e.g. ESPN8 The Ocho is `hvc1` HEVC — `manifestIncompatibleCodecsError` in hls.js). Channel health in the pack list is a real-build feature.
- Some channels block cross-origin fetches (beIN) — solved by the local proxy; a purely static deployment can't fix these.

### Surprises
- ESPN exposes `situation.isRedZone`, `down`, `distance`, `possession` per live game on the free endpoint — the "brain" needs zero scraping or paid API.
-ESPN scoreboard returns finals even off-game-day, so the ticker is never empty.

### Recommendation for the real build
- Next.js + TypeScript (local-first-web-app skill patterns), boxes in IndexedDB, grid layout engine
- Brain as a separate module with pluggable providers (ESPN NFL now; CFB/other sports later — same API shape)
- Add per-box latency/audio-ducking: mute all, unmute stage only, "solo audio" on manual pick
- Realistic stream sources: HDHomeRun → HLS proxy, YouTube live embeds, or scoreboard-only mode

## Run it
```bash
python3 server.py 8790   # from this dir — static files + CORS-unlocking HLS proxy
# open http://localhost:8790 → 📦 SOURCE PACKS (pre-filled with iptv-org sports) → tap channels to box them
```
