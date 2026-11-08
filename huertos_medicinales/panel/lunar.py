"""Primary phases from USNO; local dates for continental Ecuador."""
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("America/Guayaquil")
PHASES = {
    "New Moon": ("Luna nueva", "🌑", False),
    "First Quarter": ("Cuarto creciente", "🌓", True),
    "Full Moon": ("Luna llena", "🌕", False),
    "Last Quarter": ("Cuarto menguante", "🌗", False),
}
INTERMEDIATE = {
    "New Moon": ("Luna creciente", "🌒", True),
    "First Quarter": ("Gibosa creciente", "🌔", True),
    "Full Moon": ("Gibosa menguante", "🌖", False),
    "Last Quarter": ("Luna menguante", "🌘", False),
}

@lru_cache(maxsize=1)
def events():
    data = json.loads(Path(__file__).with_name("moon_phases_usno.json").read_text(encoding="utf-8-sig"))
    result = []
    for rows in data["years"].values():
        for row in rows:
            hour, minute = map(int, row["time"].split(":"))
            instant = datetime(row["year"], row["month"], row["day"], hour, minute, tzinfo=timezone.utc).astimezone(ZONE)
            name, icon, sow = PHASES[row["phase"]]
            result.append(dict(date=instant.date(), time=instant.strftime("%H:%M"), name=name, icon=icon, sow=sow, primary=True, phase=row["phase"]))
    return sorted(result, key=lambda item: item["date"])

def phase_on(day):
    records = events()
    for event in records:
        if event["date"] == day:
            return dict(event)
    if not records[0]["date"] < day < records[-1]["date"]:
        return None
    previous = next(event for event in reversed(records) if event["date"] < day)
    name, icon, sow = INTERMEDIATE[previous["phase"]]
    return dict(date=day, name=name, icon=icon, sow=sow, primary=False)

def month_phases(month):
    return [dict(event) for event in events() if (event["date"].year,event["date"].month) == (month.year,month.month)]
