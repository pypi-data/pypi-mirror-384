from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Tuple, Dict, Any

import requests

OPEN_METEO_WX = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIR = "https://air-quality-api.open-meteo.com/v1/air-quality"
ZIP_API = "https://api.zippopotam.us/us/{zip}"

@dataclass
class Thresholds:
    hi_amber: int = 95
    hi_red: int = 103
    aqi_amber: int = 101
    aqi_red: int = 151

def get_status(
    zip_code: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    tz: str = "America/New_York",
    when: Optional[str] = None, # "HH:MM" local to tz
    thresholds: Thresholds = Thresholds(),
) -> Dict[str, Any]:
    """Return dict with heat_index_f, aqi_us, status, reason, timestamp."""
    la, lo = resolve_coords(zip_code, lat, lon)
    t_index, ts_text, T_c, RH, pm25 = fetch_hour_hourly(la, lo, tz, when)
    hi = round(heat_index_f(T_c * 9/5 + 32, RH))
    aqi = aqi_from_pm25(pm25)
    status, reason = decide_status(hi, aqi, thresholds)
    return {
        "status": status,
        "reason": reason,
        "heat_index_f": hi,
        "aqi_us": aqi,
        "timestamp": ts_text,
        "lat": la, "lon": lo, "tz": tz
    }

def resolve_coords(zip_code: Optional[str], lat: Optional[float], lon: Optional[float]) -> Tuple[float, float]:
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    if zip_code:
        r = requests.get(ZIP_API.format(zip=zip_code), timeout=15)
        r.raise_for_status()
        j = r.json()
        place = j["places"][0]
        return float(place["latitude"]), float(place["longitude"])
    raise ValueError("Provide either --zip ZIP or both --lat and --lon.")

def fetch_hour_hourly(lat: float, lon: float, tz: str, when: Optional[str]):
    wx = requests.get(OPEN_METEO_WX, params={
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m",
        "timezone": tz
    }, timeout=20).json()
    air = requests.get(OPEN_METEO_AIR, params={
        "latitude": lat, "longitude": lon,
        "hourly": "pm2_5",
        "timezone": tz
    }, timeout=20).json()

    times = wx["hourly"]["time"]
    idx = select_hour_index(times, tz, when)
    T_c = wx["hourly"]["temperature_2m"][idx]
    RH = wx["hourly"]["relative_humidity_2m"][idx]
    pm25 = air["hourly"]["pm2_5"][idx]
    ts = datetime.fromisoformat(times[idx]).replace(tzinfo=ZoneInfo(tz)).strftime("%Y-%m-%d %H:00 %Z")
    return idx, ts, T_c, RH, pm25

def select_hour_index(times, tz: str, when: Optional[str]) -> int:
    if when:
        hh, mm = [int(x) for x in when.split(":")]
        now = datetime.now(ZoneInfo(tz))
        target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    else:
        target = datetime.now(ZoneInfo(tz)).replace(minute=0, second=0, microsecond=0)
    hour_key = target.strftime("%Y-%m-%dT%H")
    for i, t in enumerate(times):
        if t.startswith(hour_key):
            return i
    # fallback: nearest future hour
    return max(0, min(range(len(times)), key=lambda i: abs(datetime.fromisoformat(times[i]).timestamp() - target.timestamp())))

def heat_index_f(T_f: float, RH: float) -> float:
    # Rothfusz regression (NOAA)
    return (-42.379 + 2.04901523*T_f + 10.14333127*RH - 0.22475541*T_f*RH
            - 6.83783e-3*T_f*T_f - 5.481717e-2*RH*RH + 1.22874e-3*T_f*T_f*RH
            + 8.5282e-4*T_f*RH*RH - 1.99e-6*T_f*T_f*RH*RH)

def aqi_from_pm25(c: float) -> int:
    # EPA breakpoints for PM2.5 (µg/m³)
    bp = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]
    clo, chi, Ilo, Ihi = bp[-1]
    for row in bp:
        if row[0] <= c <= row[1]:
            clo, chi, Ilo, Ihi = row; break
    I = (Ihi - Ilo) / (chi - clo) * (c - clo) + Ilo
    return int(round(I))

def decide_status(hi: int, aqi: int, th: Thresholds) -> Tuple[str, str]:
    hi_cat = "Cancel" if hi >= th.hi_red else "Modify" if hi >= th.hi_amber else "OK"
    aqi_cat = "Cancel" if aqi >= th.aqi_red else "Modify" if aqi >= th.aqi_amber else "OK"
    status = "Cancel" if "Cancel" in (hi_cat, aqi_cat) else ("Modify" if "Modify" in (hi_cat, aqi_cat) else "OK")
    if status == hi_cat and status != "OK":
        reason = f"{status} — HI={hi}°F"
    elif status == aqi_cat and status != "OK":
        reason = f"{status} — AQI={aqi}"
    else:
        reason = f"OK — HI={hi}°F; AQI={aqi}"
    return status, reason
