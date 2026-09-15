# 📺 Idea: TV Guide ("what's on right now")

**Status:** SHIPPED 9/15/26 (commit 4c00edc) — but pivoted from this plan.
**Stacks on top of:** mode strip + dead-link scanner (both shipped).

## The idea

A GUIDE button that scans what's playing **right now** across your channels and
hands you a tappable list — tap a listing and it becomes a box. RedZone-style
"jump to the action," but for everything.

## How (no build step, fits the one-file philosophy)

1. **tvg-id** — iptv-org M3U entries already carry `tvg-id="..."` attributes.
   Extend `parseM3U()` to capture them alongside name/url.
2. **XMLTV EPG** — iptv-org publishes per-channel guide data as XMLTV at
   `https://iptv-org.github.io/epg/guides/<country>.xml.gz`. Fetch through
   `server.py` (new `/epg` endpoint that gunzips + streams, since the browser
   can't be trusted to do cross-origin gzipped XML cleanly).
3. **Now/next board** — parse programmes, show everything airing in the current
   window: channel, show title, start–end, progress bar. Tap → `boxes.push()`.
4. **Fallback** — free-channel EPG coverage is spotty (~40–60% of channels).
   Channels without guide data still list as "no data — play anyway."

## Open questions

- One country guide or auto-detect from the pack (iptv-org has per-country feeds)?
- Cache the EPG in `sessionStorage` — files are big, don't refetch every open.

## Why it's last

EPG data quality is the risk. Modes and the scanner are deterministic; the
guide depends on third-party data existing. Ship 1+2 first, guide after.
