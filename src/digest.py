from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
import pytz


def is_digest_time(cfg: Dict[str, Any], now_utc: datetime) -> bool:
    tz = pytz.timezone(cfg["timezone"])
    local = now_utc.astimezone(tz)

    targets = set(cfg["digest_times_local"])  # e.g., {"09:00", "14:00"}

    # exact match
    hhmm = local.strftime("%H:%M")
    if hhmm in targets:
        return True

    # grace window: within first 10 minutes after the target time (e.g., 14:00–14:09)
    hour = local.strftime("%H")
    minute = int(local.strftime("%M"))
    for t in targets:
        th, tm = t.split(":")
        if int(tm) == 0 and hour == th and 0 <= minute <= 9:
            return True

    return False


def format_window(cfg: Dict[str, Any], start_utc_iso: str | None, end_utc: datetime) -> str:
    tz = pytz.timezone(cfg["timezone"])
    end_local = end_utc.astimezone(tz)

    if start_utc_iso:
        # tolerate either "...+00:00" or "...Z"
        start_utc_iso_norm = start_utc_iso.replace("Z", "+00:00")
        start_utc = datetime.fromisoformat(start_utc_iso_norm).astimezone(timezone.utc)
        start_local = start_utc.astimezone(tz)
        return f"{start_local:%Y-%m-%d %H:%M} ET → {end_local:%Y-%m-%d %H:%M} ET"

    return f"(first run) → {end_local:%Y-%m-%d %H:%M} ET"


def build_digest_md(cfg: Dict[str,
