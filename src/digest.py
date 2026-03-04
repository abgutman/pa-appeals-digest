from __future__ import annotations

from datetime import datetime, timezone
import pytz


def is_digest_time(cfg, now_utc: datetime) -> bool:
    tz = pytz.timezone(cfg["timezone"])
    local = now_utc.astimezone(tz)

    # Do not send digests on weekends (Sat=5, Sun=6)
    if local.weekday() >= 5:
        return False

    targets = set(cfg.get("digest_times_local", []))  # e.g. ["09:00", "14:00"]

    # exact match
    hhmm = local.strftime("%H:%M")
    if hhmm in targets:
        return True

    # grace window: allow 0–9 minutes after an on-the-hour target (09:00–09:09, 14:00–14:09)
    hour = local.strftime("%H")
    minute = int(local.strftime("%M"))
    for t in targets:
        th, tm = t.split(":")
        if int(tm) == 0 and hour == th and 0 <= minute <= 9:
            return True

    return False


def format_window(cfg, start_utc_iso, end_utc: datetime) -> str:
    tz = pytz.timezone(cfg["timezone"])
    end_local = end_utc.astimezone(tz)

    if start_utc_iso:
        start_utc_iso_norm = str(start_utc_iso).replace("Z", "+00:00")
        start_utc = datetime.fromisoformat(start_utc_iso_norm).astimezone(timezone.utc)
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
