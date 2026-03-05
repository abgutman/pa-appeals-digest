from __future__ import annotations

from datetime import datetime
import pytz

def current_digest_slot(cfg, now_utc: datetime):
    """
    Returns (slot_id, slot_label) or (None, None).

    Slot windows (ET):
      - AM:  09:00–09:30
      - PM:  14:00–14:30
    """
    tz = pytz.timezone(cfg["timezone"])
    local = now_utc.astimezone(tz)

    # skip weekends
    if local.weekday() >= 5:
        return None, None

    date_str = local.strftime("%Y-%m-%d")
    minutes = local.hour * 60 + local.minute

    am_start = 9 * 60 + 0
    am_end = 9 * 60 + 30
    pm_start = 14 * 60 + 0
    pm_end = 14 * 60 + 30

    if am_start <= minutes <= am_end:
        return f"{date_str}-AM", f"{date_str} AM digest"
    if pm_start <= minutes <= pm_end:
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

    # Group by court
    court_order = [
        "Pennsylvania Supreme Court",
        "Superior Court",
        "Commonwealth Court",
        "Disciplinary Board",
    ]

    grouped = {}
    for it in items:
        grouped.setdefault(it.get("court", "Unknown Court"), []).append(it)

    # stable ordering of courts
    def court_sort_key(c):
        return court_order.index(c) if c in court_order else 999

    for court in sorted(grouped.keys(), key=court_sort_key):
        court_items = grouped[court]
        court_items.sort(key=lambda r: int(r.get("score", 0)), reverse=True)

        lines.append(f"# {court}")
        lines.append("")

        for it in court_items:
            title = it.get("title", "")
            link = it.get("link", "")
            score = it.get("score", 0)
            doc_types = ", ".join(it.get("doc_types", ["Unknown"]))
            flags = ", ".join(it.get("flags", []))
            published = format_published_et(cfg, it.get("published_utc"))

            place_hits = it.get("place_hits", [])
            special_hits = it.get("special_hits", [])
            reversal_hits = it.get("reversal_hits", [])

            lines.append(f"## {title}")
            lines.append(f"- Date: {published}")
            lines.append(f"- Link: {link}")
            if it.get("pdf_link"):
                lines.append(f"- PDF: {it['pdf_link']}")
            lines.append(f"- Document type(s): {doc_types}")
            lines.append(f"- Score: **{score}**  ({flags})")

            # Transparency: why it matched
            if place_hits:
                lines.append(f"- Matched place terms: {', '.join(place_hits)}")
            if special_hits:
                lines.append(f"- Matched special terms: {', '.join(special_hits)}")
            if reversal_hits:
                lines.append(f"- Matched reversal/remand terms: {', '.join(reversal_hits)}")

            lines.append("")

    return "\n".join(lines)

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
