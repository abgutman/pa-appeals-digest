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
