"""
Kite Advisor NL — utils.py (test version)
Core domain logic: wind direction matching, scoring, forecasts via Open-Meteo.
"""

import csv
import math
import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import List, Dict, Optional, Tuple

import pandas as pd
import requests
from geopy.geocoders import Nominatim

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPASS_LABELS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def geocode_postcode(postcode: str) -> Optional[Tuple[float, float]]:
    """Return (lat, lon) for a Dutch postcode, or None."""
    try:
        geo = Nominatim(user_agent="kite-advisor-nl")
        loc = geo.geocode(f"{postcode}, Netherlands")
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        pass
    return None

# ---------------------------------------------------------------------------
# Spot loading
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_spots(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Load kite spots from CSV."""
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "nkv_spots_full.csv")
    df = pd.read_csv(csv_path)
    return df

# ---------------------------------------------------------------------------
# Wind direction helpers
# ---------------------------------------------------------------------------

def degrees_to_compass(deg: float) -> str:
    """Convert degrees (0-360) to 16-point compass label."""
    idx = round(deg / 22.5) % 16
    return COMPASS_LABELS[idx]


def parse_dir_windows(windows_str: str) -> List[Tuple[float, float]]:
    """
    Parse direction window string like '220-300' or '220-300;330-20'.
    Returns list of (start_deg, end_deg) tuples.
    """
    windows = []
    for part in windows_str.split(";"):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            windows.append((float(start_s), float(end_s)))
    return windows


def is_direction_in_window(deg: float, windows: List[Tuple[float, float]]) -> bool:
    """
    Check if a wind direction (degrees) falls in any of the allowed windows.
    Supports wrap-around, e.g. (330, 20) means 330..360 and 0..20.
    """
    deg = deg % 360
    for start, end in windows:
        start = start % 360
        end = end % 360
        if start <= end:
            if start <= deg <= end:
                return True
        else:
            # wrap-around: e.g. 330-20 means 330..360 + 0..20
            if deg >= start or deg <= end:
                return True
    return False

# ---------------------------------------------------------------------------
# Open-Meteo forecast
# ---------------------------------------------------------------------------

@lru_cache(maxsize=64)
def _fetch_open_meteo(lat: float, lon: float, days: int) -> Optional[dict]:
    """Fetch hourly wind forecast from Open-Meteo. Cached."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        "daily": "sunrise,sunset",
        "wind_speed_unit": "kn",
        "timezone": "Europe/Amsterdam",
        "forecast_days": min(days, 16),
    }
    try:
        r = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_forecast(
    lat: float, lon: float, days: int = 3, *, daylight_only: bool = True,
) -> pd.DataFrame:
    """
    Return a DataFrame with columns:
    time, wind_kn, wind_dir_deg, wind_dir_label, gust_kn

    When *daylight_only* is True (default), hours before sunrise or after
    sunset for that location are excluded.
    """
    data = _fetch_open_meteo(lat, lon, days)
    if data is None or "hourly" not in data:
        return pd.DataFrame()

    h = data["hourly"]
    df = pd.DataFrame({
        "time": pd.to_datetime(h["time"]),
        "wind_kn": h["wind_speed_10m"],
        "wind_dir_deg": h["wind_direction_10m"],
        "gust_kn": h["wind_gusts_10m"],
    })
    df["wind_dir_label"] = df["wind_dir_deg"].apply(
        lambda d: degrees_to_compass(d) if pd.notna(d) else ""
    )

    # Filter to daylight hours using daily sunrise/sunset from Open-Meteo
    if daylight_only and "daily" in data:
        daily = data["daily"]
        sunrise_times = pd.to_datetime(daily.get("sunrise", []))
        sunset_times = pd.to_datetime(daily.get("sunset", []))
        if len(sunrise_times) > 0 and len(sunset_times) > 0:
            mask = pd.Series(False, index=df.index)
            for sr, ss in zip(sunrise_times, sunset_times):
                mask = mask | ((df["time"] >= sr) & (df["time"] <= ss))
            df = df[mask].reset_index(drop=True)

    return df


def get_current_conditions(lat: float, lon: float) -> Optional[Dict]:
    """Return most recent hourly observation-like data from Open-Meteo."""
    df = get_forecast(lat, lon, days=2, daylight_only=False)
    if df.empty:
        return None
    now = pd.Timestamp.now(tz="Europe/Amsterdam").tz_localize(None)
    past = df[df["time"] <= now]
    if past.empty:
        row = df.iloc[0]
    else:
        row = past.iloc[-1]
    return {
        "time": row["time"],
        "wind_kn": row["wind_kn"],
        "wind_dir_deg": row["wind_dir_deg"],
        "wind_dir_label": row["wind_dir_label"],
        "gust_kn": row["gust_kn"],
    }

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def compute_score(
    wind_kn: float,
    gust_kn: float,
    wind_dir_deg: float,
    dir_windows: List[Tuple[float, float]],
    min_kn: float,
    max_kn: float = 35.0,
    tidal_factor: float = 0.0,
    travel_minutes: Optional[float] = None,
    level: str = "Intermediate",
) -> Optional[float]:
    """
    Compute a score for a spot at a given hour.

    Returns None if direction is outside allowed windows (hard filter).
    Otherwise returns a float — higher is better.
    """
    # Hard filter: direction must match
    if not is_direction_in_window(wind_dir_deg, dir_windows):
        return None

    # Base: how well the wind speed fits the ideal range
    if wind_kn < min_kn * 0.7:
        return 0.0  # way too light

    if wind_kn < min_kn:
        # below minimum but close
        speed_score = 0.3 * (wind_kn / min_kn)
    elif wind_kn <= max_kn:
        # sweet spot — peak around the middle of the range
        mid = (min_kn + max_kn) / 2
        speed_score = 1.0 - 0.3 * abs(wind_kn - mid) / (max_kn - min_kn + 1)
    else:
        # above max
        overshoot = wind_kn - max_kn
        if level == "Advanced":
            speed_score = max(0.4, 1.0 - overshoot * 0.03)
        else:
            speed_score = max(0.1, 0.7 - overshoot * 0.05)

    # Gust stability: penalise large gust-average spread
    gust_diff = abs(gust_kn - wind_kn)
    if gust_diff <= 5:
        gust_factor = 0.1
    elif gust_diff <= 10:
        gust_factor = 0.0
    else:
        gust_factor = -0.15 * ((gust_diff - 10) / 10)

    # Tidal factor: small bonus/malus between -0.15 and +0.15
    tidal = max(-0.15, min(0.15, tidal_factor))

    # Travel penalty (optional)
    travel_penalty = 0.0
    if travel_minutes is not None and travel_minutes > 0:
        travel_penalty = -0.002 * travel_minutes  # ~-0.12 for 60 min

    score = speed_score + gust_factor + tidal + travel_penalty
    return round(score, 3)


def rank_spots(
    spots_df: pd.DataFrame,
    forecast_hours: pd.DataFrame,
    board_type: str = "Twintip",
    level: str = "Intermediate",
    water_filter: str = "Alles",
    min_kn_override: Optional[float] = None,
    max_kn: float = 35.0,
) -> pd.DataFrame:
    """
    For each spot × hour, compute a score.
    Returns a flat DataFrame sorted by score descending.
    """
    rows = []
    for _, spot in spots_df.iterrows():
        # Apply water type filter
        if water_filter != "Alles":
            wt = spot["water_type"]
            if water_filter == "Zee" and wt != "sea":
                continue
            if water_filter == "Binnenwater" and wt != "flat":
                continue

        dir_windows = parse_dir_windows(str(spot["dir_windows_deg"]))
        if board_type == "Foil":
            spot_min = float(spot["min_kn_foil"])
        else:
            spot_min = float(spot["min_kn_twintip"])
        if min_kn_override is not None:
            spot_min = min_kn_override

        for _, hr in forecast_hours.iterrows():
            wind_kn = hr["wind_kn"]
            gust_kn = hr["gust_kn"]
            wind_dir = hr["wind_dir_deg"]
            if pd.isna(wind_kn) or pd.isna(wind_dir):
                continue

            score = compute_score(
                wind_kn=wind_kn,
                gust_kn=gust_kn if pd.notna(gust_kn) else wind_kn,
                wind_dir_deg=wind_dir,
                dir_windows=dir_windows,
                min_kn=spot_min,
                max_kn=max_kn,
                level=level,
            )
            if score is None:
                continue  # direction mismatch

            rows.append({
                "spot": spot["name"],
                "water_type": spot["water_type"],
                "time": hr["time"],
                "wind_kn": round(wind_kn, 1),
                "gust_kn": round(gust_kn, 1) if pd.notna(gust_kn) else None,
                "wind_dir_deg": wind_dir,
                "wind_dir": degrees_to_compass(wind_dir),
                "score": score,
                "model": "Open-Meteo",
            })

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    result = result.sort_values("score", ascending=False).reset_index(drop=True)
    return result
