from __future__ import annotations

from datetime import datetime
import pytz


def current_digest_slot(cfg, now_utc: datetime):
    """
    Returns (slot_id, slot_label) or (None, None) if we should not send a digest now.
    slot_id example: "2026-03-05-AM"
    """
    tz = pytz.timezone(cfg["timezone"])
    local = now_utc.astimezone(tz)

    # skip weekends
    if local.weekday() >= 5:
        return None, None

    hour = local.hour
    date_str = local.strftime("%Y-%m-%d")

    # Wide windows so GitHub scheduling jitter doesn't matter
    # AM window ~ around 9am
    if 8 <= hour <= 11:
        return f"{date_str}-AM", f"{date_str} AM digest"
    # PM window ~ around 2pm
    if 13 <= hour <= 16:
        return f"{date_str}-PM", f"{date_str} PM digest"

    return None, None


def format_window(cfg, start_utc_iso, end_utc: datetime) -> str:
    tz = pytz.timezone(cfg["timezone"])
    end_local = end_utc.astimezone(tz)

    if start_utc_iso:
        start_utc_iso_norm = str(start_utc_iso).replace("Z", "+00:00")
        start_utc = datetime.fromisoformat(start_utc_iso_norm)
        start_local = start_utc.astimezone(tz)
        return f"{start_local:%Y-%m-%d %H:%M} ET → {end_local:%Y-%m-%d %H:%M} ET"

    return f"(first run) → {end_local:%Y-%m-%d %H:%M} ET"


def format_published_et(cfg, published_utc_iso) -> str:
    if not published_utc_iso:
        return "Unknown"
    tz = pytz.timezone(cfg["timezone"])
    dt = datetime.fromisoformat(str(published_utc_iso).replace("Z", "+00:00")).astimezone(tz)
    return dt.strftime("%Y-%m-%d")


def build_digest_md(cfg, window_label: str, items) -> str:
    lines = []
    lines.append("# PA Appeals Digest")
    lines.append("")
    lines.append(f"**Window:** {window_label}")
    lines.append(f"**Matches:** {len(items)}")
    lines.append("")

    if not items:
        lines.append("_No matched items in this window._")
        return "\n".join(lines)

    for it in items:
        title = it.get("title", "")
        link = it.get("link", "")
        court = it.get("court", "")
        score = it.get("score", 0)
        doc_types = ", ".join(it.get("doc_types", ["Unknown"]))
        flags = ", ".join(it.get("flags", []))
        published = format_published_et(cfg, it.get("published_utc"))

        lines.append(f"## {court} — {title}")
        lines.append(f"- Date: {published}")
        lines.append(f"- Link: {link}")
        if it.get("pdf_link"):
            lines.append(f"- PDF: {it['pdf_link']}")
        lines.append(f"- Document type(s): {doc_types}")
        lines.append(f"- Score: **{score}**  ({flags})")
        lines.append("")

    return "\n".join(lines)
