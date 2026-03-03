from __future__ import annotations
import feedparser
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timezone


@dataclass
class FeedItem:
    court: str
    title: str
    link: str
    published_utc: Optional[str]
    guid: Optional[str]


def _to_utc_iso(struct_time_obj) -> Optional[str]:
    if not struct_time_obj:
        return None
    dt = datetime(*struct_time_obj[:6], tzinfo=timezone.utc)
    return dt.replace(microsecond=0).isoformat()


def fetch_feed(court: str, url: str) -> List[FeedItem]:
    d = feedparser.parse(url)
    items: List[FeedItem] = []
    for e in d.entries:
        items.append(
            FeedItem(
                court=court,
                title=getattr(e, "title", "").strip(),
                link=getattr(e, "link", "").strip(),
                published_utc=_to_utc_iso(getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)),
                guid=getattr(e, "id", None) or getattr(e, "guid", None),
            )
        )
    return items
