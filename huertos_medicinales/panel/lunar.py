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

# Fases según conocimiento ancestral: MSP Ecuador (2017), Lineamientos de
# huertos medicinales, p. 42-47 ("ritual de siembra en fase de luna creciente
# o luna llena"; "si se va a utilizar las hojas, flores y frutos se cosecha
# en fase de luna creciente o luna llena. Si se va a utilizar las semillas o
# raíces se cosecha en cuarto menguante").
CRECIENTE_O_LLENA = {"Luna creciente", "Cuarto creciente", "Gibosa creciente", "Luna llena"}
MENGUANTE = {"Cuarto menguante", "Gibosa menguante", "Luna menguante"}

def recomendacion(tipo, fecha, parte_usada=""):
    fase = phase_on(fecha)
    if fase is None:
        return None
    nombre = fase["name"]
    if tipo == "preparacion":
        ideal, detalle = nombre == "Luna nueva", "La preparación de la tierra se recomienda en luna nueva (oscura)."
    elif tipo == "siembra":
        ideal, detalle = nombre in CRECIENTE_O_LLENA, "La siembra se recomienda en luna creciente o luna llena."
    elif tipo == "cosecha" and parte_usada == "hojas_flores_frutos":
        ideal, detalle = nombre in CRECIENTE_O_LLENA, "La cosecha de hojas, flores o frutos se recomienda en luna creciente o luna llena."
    elif tipo == "cosecha" and parte_usada == "semillas_raices":
        ideal, detalle = nombre in MENGUANTE, "La cosecha de semillas o raíces se recomienda en cuarto menguante."
    else:
        return None
    return dict(ideal=ideal, fase=nombre, icono=fase["icon"], detalle=detalle)
