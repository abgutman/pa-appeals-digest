from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import pytz


def is_digest_time(cfg: Dict[str, Any], now_utc: datetime) -> bool:
    tz = pytz.timezone(cfg["timezone"])
    local = now_utc.astimezone(tz)
    hhmm = local.strftime("%H:%M")
    return hhmm in set(cfg["digest_times_local"])


def format_window(cfg: Dict[str, Any], start_utc_iso: str | None, end_utc: datetime) -> str:
    tz = pytz.timezone(cfg["timezone"])
    end_local = end_utc.astimezone(tz)
    if start_utc_iso:
        start_utc = datetime.fromisoformat(start_utc_iso.replace("Z", "+00:00")).astimezone(timezone.utc)
        start_local = start_utc.astimezone(tz)
        return f"{start_local:%Y-%m-%d %H:%M} ET → {end_local:%Y-%m-%d %H:%M} ET"
    return f"(first run) → {end_local:%Y-%m-%d %H:%M} ET"


def build_digest_md(cfg: Dict[str, Any], window_label: str, items: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append(f"# PA Appeals Digest")
    lines.append("")
    lines.append(f"**Window:** {window_label}")
    lines.append(f"**Matches:** {len(items)}")
    lines.append("")
    if not items:
        lines.append("_No matched items in this window._")
        return "\n".join(lines)

    for it in items:
        title = it["title"]
        link = it["link"]
        court = it["court"]
        score = it["score"]
        doc_types = ", ".join(it.get("doc_types", ["Unknown"]))
        flags = ", ".join(it.get("flags", []))
        excerpt = (it.get("excerpt") or "").strip().replace("\n", " ")
        if len(excerpt) > 240:
            excerpt = excerpt[:237] + "..."

        lines.append(f"## {court} — {title}")
        lines.append(f"- Link: {link}")
        lines.append(f"- Document type(s): {doc_types}")
        lines.append(f"- Score: **{score}**  ({flags})")
        if excerpt:
            lines.append(f"- Summary/snippet: {excerpt}")
        lines.append("")

    return "\n".join(lines)
