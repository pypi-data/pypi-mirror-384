import re

TIME_RE = re.compile(r"^(\d{2}):(\d{2})$")

def _valid_time(hour: int, minute: int) -> bool:
    return 0 <= hour <= 23 and 0 <= minute <= 59

def parse_time(time_string: str) -> dict:
    m = TIME_RE.match(time_string.strip())
    if not m:
        return {}
    hour, minute = (int(m.group(1)), int(m.group(2)))
    if not _valid_time(hour, minute):
        return {}
    return {"hour": hour, "minute": minute}
