from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List
import os

from src.config import load_config, get_feeds
from src.state import load_state, save_state, utc_now_iso
from src.feeds import fetch_feed
from src.fetch import fetch_html, extract_text_from_html, find_pdf_links, download_pdf
from src.pdf_text import extract_pdf_text
from src.scoring import score_item
from src.digest import is_digest_time, build_digest_md, format_window


def stable_item_id(item) -> str:
    # Prefer GUID; else link; else title hash fallback
    return (item.guid or item.link or item.title).strip()


def make_excerpt(full_text: str, terms: List[str], max_len: int = 220) -> str:
    if not full_text:
        return ""
    low = full_text.lower()
    for t in terms:
        i = low.find(t.lower())
        if i != -1:
            start = max(0, i - 120)
            end = min(len(full_text), i + 120)
            snippet = full_text[start:end].strip()
            return " ".join(snippet.split())
    # fallback first line-ish
    return " ".join(full_text.strip().split()[:40])


def main() -> int:
