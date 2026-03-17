"""
Kite Advisor NL — utils.py (Pro version)
Same core domain logic as app-test, but uses modular providers.
"""

import json
import os
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Optional, Tuple

import pandas as pd
from geopy.geocoders import Nominatim

from providers import ProviderManager

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPASS_LABELS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]

# Singleton provider manager
_provider_mgr = ProviderManager()

# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def geocode_postcode(postcode: str) -> Optional[Tuple[float, float]]:
    try:
        geo = Nominatim(user_agent="kite-advisor-nl-pro")
        loc = geo.geocode(f"{postcode}, Netherlands")
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        pass
    return None

# ---------------------------------------------------------------------------
# Spot loading (JSON for pro version)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_spots(json_path: Optional[str] = None) -> pd.DataFrame:
    if json_path is None:
        json_path = os.path.join(os.path.dirname(__file__), "spots_nkv.json")
    with open(json_path) as f:
        spots = json.load(f)
    return pd.DataFrame(spots)

# ---------------------------------------------------------------------------
# Wind direction helpers
# ---------------------------------------------------------------------------

def degrees_to_compass(deg: float) -> str:
    idx = round(deg / 22.5) % 16
    return COMPASS_LABELS[idx]


def parse_dir_windows(windows_str: str) -> List[Tuple[float, float]]:
    windows = []
    for part in windows_str.split(";"):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            windows.append((float(start_s), float(end_s)))
    return windows


def is_direction_in_window(deg: float, windows: List[Tuple[float, float]]) -> bool:
    deg = deg % 360
    for start, end in windows:
        start = start % 360
        end = end % 360
        if start <= end:
            if start <= deg <= end:
                return True
        else:
            if deg >= start or deg <= end:
                return True
    return False

# ---------------------------------------------------------------------------
# Forecast (via provider manager)
# ---------------------------------------------------------------------------

def get_forecast(lat: float, lon: float, days: int = 3,
                 preferred_model: Optional[str] = None) -> pd.DataFrame:
    return _provider_mgr.get_forecast(lat, lon, days, preferred_model)


def get_all_forecasts(lat: float, lon: float, days: int = 3) -> Dict[str, pd.DataFrame]:
    return _provider_mgr.get_all_forecasts(lat, lon, days)


def get_current_conditions(lat: float, lon: float) -> Optional[Dict]:
    df = get_forecast(lat, lon, days=2)
    if df.empty:
        return None
    now = pd.Timestamp.now(tz="Europe/Amsterdam").tz_localize(None)
    past = df[df["time"] <= now]
    row = past.iloc[-1] if not past.empty else df.iloc[0]
    return row.to_dict()


def get_available_models() -> List[str]:
    return [p.name for p in _provider_mgr.get_available_providers()]

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
    if not is_direction_in_window(wind_dir_deg, dir_windows):
        return None

    if wind_kn < min_kn * 0.7:
        return 0.0

    if wind_kn < min_kn:
        speed_score = 0.3 * (wind_kn / min_kn)
    elif wind_kn <= max_kn:
        mid = (min_kn + max_kn) / 2
        speed_score = 1.0 - 0.3 * abs(wind_kn - mid) / (max_kn - min_kn + 1)
    else:
        overshoot = wind_kn - max_kn
        if level == "Advanced":
            speed_score = max(0.4, 1.0 - overshoot * 0.03)
        else:
            speed_score = max(0.1, 0.7 - overshoot * 0.05)

    gust_diff = abs(gust_kn - wind_kn)
    if gust_diff <= 5:
        gust_factor = 0.1
    elif gust_diff <= 10:
        gust_factor = 0.0
    else:
        gust_factor = -0.15 * ((gust_diff - 10) / 10)

    tidal = max(-0.15, min(0.15, tidal_factor))

    travel_penalty = 0.0
    if travel_minutes is not None and travel_minutes > 0:
        travel_penalty = -0.002 * travel_minutes

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
    user_location: Optional[Tuple[float, float]] = None,
) -> pd.DataFrame:
    rows = []
    for _, spot in spots_df.iterrows():
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

        # Travel time (if available)
        travel_min = None
        if user_location:
            travel_min = _provider_mgr.get_travel_time(
                user_location, (spot["lat"], spot["lon"])
            )

        # Tidal factor stub
        tidal = 0.0

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
                tidal_factor=tidal,
                travel_minutes=travel_min,
                level=level,
            )
            if score is None:
                continue

            model = hr.get("model", "Open-Meteo")
            rows.append({
                "spot": spot["name"],
                "water_type": spot["water_type"],
                "time": hr["time"],
                "wind_kn": round(wind_kn, 1),
                "gust_kn": round(gust_kn, 1) if pd.notna(gust_kn) else None,
                "wind_dir_deg": wind_dir,
                "wind_dir": degrees_to_compass(wind_dir),
                "score": score,
                "model": model,
                "travel_min": travel_min,
            })

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    result = result.sort_values("score", ascending=False).reset_index(drop=True)
    return result
