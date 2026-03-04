from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import os
import pytz

from src.config import load_config, get_feeds
from src.state import load_state, save_state
from src.feeds import fetch_feed, FeedItem
from src.fetch import fetch_html, extract_text_from_html, find_pdf_links, download_pdf
from src.pdf_text import extract_pdf_text
from src.scoring import score_item
from src.digest import is_digest_time, build_digest_md, format_window

OUT_DIR = Path("out")


def stable_item_id(item: FeedItem) -> str:
    return (item.guid or item.link or item.title).strip()


def make_excerpt(full_text: str, preferred_terms: List[str], max_words: int = 45) -> str:
    if not full_text:
        return ""
    text = " ".join(full_text.split())
    low = text.lower()

    for t in preferred_terms:
        t = (t or "").strip()
        if not t:
            continue
        idx = low.find(t.lower())
        if idx != -1:
            start = max(0, idx - 180)
            end = min(len(text), idx + 180)
            snippet = text[start:end].strip()
            words = snippet.split()
            if len(words) > max_words:
                return " ".join(words[:max_words]) + "..."
            return snippet

    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return text


def build_preferred_terms(cfg: Dict[str, Any]) -> List[str]:
    terms: List[str] = []
    places = cfg.get("places", {})
    terms.extend(places.get("counties", []))
    terms.extend(places.get("cities", []))
    for sp in places.get("special", []):
        terms.append(sp.get("term", ""))

    terms.extend(cfg.get("reversal_indicators", []))
    terms.extend(cfg.get("precedential", {}).get("indicators", []))

    out: List[str] = []
    seen = set()
    for t in terms:
        t = (t or "").strip()
        if not t:
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def main() -> int:
    cfg = load_config()
    feeds = get_feeds(cfg)

    state = load_state()
    state.setdefault("seen", {})
    state.setdefault("processed", {})
    state.setdefault("last_digest_utc", None)

    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    tz = pytz.timezone(cfg["timezone"])
    print(
        f"now_utc={now_utc.isoformat()} "
        f"now_local={now_utc.astimezone(tz).strftime('%Y-%m-%d %H:%M %Z')}"
    )

    preferred_terms = build_preferred_terms(cfg)

    any_new = False

    # 1) Poll RSS and process newly discovered items
    for f in feeds:
        items = fetch_feed(f.court, f.url)
        for item in items:
            item_id = stable_item_id(item)
            if not item_id:
                continue

            if item_id in state["seen"]:
                continue

            any_new = True
            state["seen"][item_id] = {
                "first_seen_utc": now_utc.isoformat(),
                "court": item.court,
                "title": item.title,
                "link": item.link,
                "published_utc": item.published_utc,
            }

            html_text = ""
            pdf_text = ""
            pdf_links: List[str] = []

            try:
                html = fetch_html(item.link)
                html_text = extract_text_from_html(html)
                pdf_links = find_pdf_links(item.link, html)
            except Exception:
                html_text = ""
                pdf_links = []

            if pdf_links:
                try:
                    pdf_bytes = download_pdf(pdf_links[0])
                    pdf_text = extract_pdf_text(pdf_bytes, max_pages=3)
                except Exception:
                    pdf_text = ""

            combined_text = "\n".join(
                [item.title or "", html_text or "", pdf_text or ""]
            ).strip()

            score, reasons = score_item(item.court, combined_text, cfg)
            excerpt_source = pdf_text or html_text or combined_text
            excerpt = make_excerpt(excerpt_source, preferred_terms)

            state["processed"][item_id] = {
                "processed_utc": now_utc.isoformat(),
                "first_seen_utc": state["seen"][item_id]["first_seen_utc"],
                "court": item.court,
                "title": item.title,
                "link": item.link,
                "published_utc": item.published_utc,
                "score": score,
                "flags": reasons.get("flags", []),
                "doc_types": reasons.get("doc_types", ["Unknown"]),
                "place_hits": reasons.get("place_hits", []),
                "special_hits": reasons.get("special_hits", []),
                "reversal_hits": reasons.get("reversal_hits", []),
                "pdf_link": pdf_links[0] if pdf_links else None,
                "excerpt": excerpt,
            }

    # Save state whenever we see new items
    if any_new:
        save_state(state)
        
    
    # 2) Create digest only at digest times (or forced)
    print(f"DEBUG: FORCE_DIGEST={os.getenv('FORCE_DIGEST')}")
    force = os.getenv("FORCE_DIGEST", "").strip() == "1"
    if force or is_digest_time(cfg, now_utc):
        last_digest_utc = state.get("last_digest_utc")
        window_label = format_window(cfg, last_digest_utc, now_utc)

        digest_items: List[Dict[str, Any]] = []
        for _item_id, rec in state["processed"].items():
            first_seen = rec.get("first_seen_utc")
            if not first_seen:
                continue
            if last_digest_utc and first_seen <= last_digest_utc:
                continue
            if first_seen > now_utc.isoformat():
                continue
            if int(rec.get("score", 0)) <= 0:
                continue
            digest_items.append(rec)

        digest_items.sort(key=lambda r: int(r.get("score", 0)), reverse=True)

        md = build_digest_md(cfg, window_label, digest_items)

        # print to logs
        print(md)

        # write artifact
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = now_utc.strftime("%Y-%m-%d_%H%MUTC")
        out_path = OUT_DIR / f"digest_{ts}.md"
        out_path.write_text(md, encoding="utf-8")

        # update last digest
        state["last_digest_utc"] = now_utc.isoformat()
        save_state(state)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
