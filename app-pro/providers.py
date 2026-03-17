"""
Kite Advisor NL — providers.py (Pro version)
Modular weather data provider architecture.

Each provider implements the same interface so they can be swapped/stacked.
Priority: AROME 1.3 > Windguru WG model > Soarcast > Open-Meteo (fallback)
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Base provider interface
# ---------------------------------------------------------------------------

class WeatherProvider(ABC):
    """Base class for all weather data providers."""

    name: str = "base"
    max_forecast_hours: int = 48
    requires_api_key: bool = False

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and accessible."""
        ...

    @abstractmethod
    def get_forecast(self, lat: float, lon: float, days: int) -> pd.DataFrame:
        """
        Fetch forecast. Must return DataFrame with columns:
        time, wind_kn, wind_dir_deg, wind_dir_label, gust_kn, model
        """
        ...

    def get_current(self, lat: float, lon: float) -> Optional[Dict]:
        """Get current conditions. Default: latest hour from forecast."""
        df = self.get_forecast(lat, lon, days=1)
        if df.empty:
            return None
        now = pd.Timestamp.now(tz="Europe/Amsterdam").tz_localize(None)
        past = df[df["time"] <= now]
        row = past.iloc[-1] if not past.empty else df.iloc[0]
        return row.to_dict()


# ---------------------------------------------------------------------------
# Open-Meteo (always available, no key needed)
# ---------------------------------------------------------------------------

class OpenMeteoProvider(WeatherProvider):
    name = "Open-Meteo"
    max_forecast_hours = 16 * 24
    requires_api_key = False

    def is_available(self) -> bool:
        return True

    def get_forecast(self, lat: float, lon: float, days: int) -> pd.DataFrame:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "wind_speed_unit": "kn",
            "timezone": "Europe/Amsterdam",
            "forecast_days": min(days, 16),
        }
        try:
            r = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params=params, timeout=10,
            )
            r.raise_for_status()
            data = r.json()
        except Exception:
            return pd.DataFrame()

        h = data.get("hourly", {})
        if not h:
            return pd.DataFrame()

        from utils import degrees_to_compass
        df = pd.DataFrame({
            "time": pd.to_datetime(h["time"]),
            "wind_kn": h["wind_speed_10m"],
            "wind_dir_deg": h["wind_direction_10m"],
            "gust_kn": h["wind_gusts_10m"],
        })
        df["wind_dir_label"] = df["wind_dir_deg"].apply(
            lambda d: degrees_to_compass(d) if pd.notna(d) else ""
        )
        df["model"] = self.name
        return df


# ---------------------------------------------------------------------------
# AROME 1.3 — Highest priority for short-term (48h)
# ---------------------------------------------------------------------------

class AromeProvider(WeatherProvider):
    """
    AROME 1.3 km model — the best short-term model for the Netherlands.
    ~42-48 hours ahead. Highest priority.

    TODO: Implement actual AROME data fetching.
    Possible sources:
    - Météo-France open data API
    - Open-Meteo with model=meteofrance_arome_france_hd
    - KNMI data platform
    """
    name = "AROME 1.3"
    max_forecast_hours = 48
    requires_api_key = False  # Open-Meteo AROME doesn't need a key

    def is_available(self) -> bool:
        # TODO: Check if AROME data is actually available
        # For now, try via Open-Meteo's AROME endpoint
        return True

    def get_forecast(self, lat: float, lon: float, days: int) -> pd.DataFrame:
        """
        Try to fetch AROME via Open-Meteo's model-specific endpoint.
        Falls back gracefully if not available.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "wind_speed_unit": "kn",
            "timezone": "Europe/Amsterdam",
            "forecast_days": min(days, 2),  # AROME only goes ~48h
        }
        try:
            # Open-Meteo provides AROME via the DWD API
            r = requests.get(
                "https://api.open-meteo.com/v1/meteofrance",
                params=params, timeout=10,
            )
            r.raise_for_status()
            data = r.json()
        except Exception:
            return pd.DataFrame()

        h = data.get("hourly", {})
        if not h:
            return pd.DataFrame()

        from utils import degrees_to_compass
        df = pd.DataFrame({
            "time": pd.to_datetime(h["time"]),
            "wind_kn": h["wind_speed_10m"],
            "wind_dir_deg": h["wind_direction_10m"],
            "gust_kn": h["wind_gusts_10m"],
        })
        df["wind_dir_label"] = df["wind_dir_deg"].apply(
            lambda d: degrees_to_compass(d) if pd.notna(d) else ""
        )
        df["model"] = self.name
        return df


# ---------------------------------------------------------------------------
# Windguru — WG model (average of all models), up to 14 days
# ---------------------------------------------------------------------------

class WindguruProvider(WeatherProvider):
    """
    Windguru.cz — uses spot-specific IDs.
    The WG model is the average of all wind models, good for 2-week planning.

    TODO: Windguru requires either:
    - Windguru Pro API key (paid)
    - Web scraping (fragile, against ToS)

    For now this is a stub. When API key is available, set WINDGURU_API_KEY
    in .env file.
    """
    name = "Windguru WG"
    max_forecast_hours = 14 * 24
    requires_api_key = True

    def __init__(self):
        self.api_key = os.getenv("WINDGURU_API_KEY")

    def is_available(self) -> bool:
        return self.api_key is not None

    def get_forecast(self, lat: float, lon: float, days: int,
                     spot_id: Optional[int] = None) -> pd.DataFrame:
        """
        TODO: Implement Windguru API call.
        Windguru API endpoint: https://www.windguru.cz/int/iapi.php
        Requires: spot_id, API key

        For the user's primary spot (IJmuiden): spot_id = 48299
        URL: https://www.windguru.cz/48299
        """
        if not self.is_available():
            return pd.DataFrame()

        # TODO: Implement actual API call
        # Example structure:
        # params = {
        #     "q": "forecast",
        #     "id_spot": spot_id,
        #     "id_model": 3,  # WG model
        #     "token": self.api_key,
        # }
        # r = requests.get("https://www.windguru.cz/int/iapi.php", params=params)
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Soarcast
# ---------------------------------------------------------------------------

class SoarcastProvider(WeatherProvider):
    """
    Soarcast.nl — Dutch wind forecast source.
    URL pattern: https://soarcast.nl/web/spotinfo?spot={id}&sport=kite&day=today

    TODO: Implement data fetching from Soarcast.
    May require web scraping or finding an API endpoint.
    """
    name = "Soarcast"
    max_forecast_hours = 72
    requires_api_key = False

    def is_available(self) -> bool:
        # TODO: Check if Soarcast data can be fetched
        return False

    def get_forecast(self, lat: float, lon: float, days: int,
                     spot_slug: Optional[str] = None) -> pd.DataFrame:
        """
        TODO: Implement Soarcast data fetching.
        """
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# KNMI live measurements
# ---------------------------------------------------------------------------

class KNMIProvider(WeatherProvider):
    """
    KNMI — live weather measurements from Dutch weather stations.

    TODO: Implement using KNMI Open Data API.
    https://dataplatform.knmi.nl/
    """
    name = "KNMI Live"
    max_forecast_hours = 0  # measurements only, no forecast
    requires_api_key = True

    def __init__(self):
        self.api_key = os.getenv("KNMI_API_KEY")

    def is_available(self) -> bool:
        return self.api_key is not None

    def get_forecast(self, lat: float, lon: float, days: int) -> pd.DataFrame:
        """KNMI provides measurements, not forecasts."""
        return pd.DataFrame()

    def get_current(self, lat: float, lon: float) -> Optional[Dict]:
        """
        TODO: Fetch latest measurement from nearest KNMI station.
        """
        return None


# ---------------------------------------------------------------------------
# Rijkswaterstaat — tidal data
# ---------------------------------------------------------------------------

class RijkswaterstaatProvider:
    """
    Rijkswaterstaat — tidal and current data.
    Not a weather provider but provides tidal factor for scoring.

    TODO: Implement using RWS Waterinfo API.
    https://waterinfo.rws.nl/
    """

    def is_available(self) -> bool:
        return False

    def get_tidal_factor(self, lat: float, lon: float,
                         time: datetime) -> float:
        """
        Return a tidal factor between -0.15 and +0.15.
        Positive = favorable tide, negative = unfavorable.

        TODO: Implement using actual tidal data.
        """
        return 0.0


# ---------------------------------------------------------------------------
# Google Maps — travel time
# ---------------------------------------------------------------------------

class GoogleMapsProvider:
    """
    Google Maps — travel time calculation.

    TODO: Implement using Google Maps Distance Matrix API.
    Requires GOOGLE_MAPS_API_KEY in .env.
    """

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    def is_available(self) -> bool:
        return self.api_key is not None

    def get_travel_time(self, origin_lat: float, origin_lon: float,
                        dest_lat: float, dest_lon: float) -> Optional[float]:
        """
        Return travel time in minutes, or None if unavailable.

        TODO: Implement Google Maps Distance Matrix API call.
        """
        if not self.is_available():
            return None
        return None


# ---------------------------------------------------------------------------
# Provider manager — cascading fallback
# ---------------------------------------------------------------------------

class ProviderManager:
    """
    Manages multiple weather providers with cascading fallback.
    Priority order: AROME > Windguru > Soarcast > Open-Meteo
    """

    def __init__(self):
        self.providers: List[WeatherProvider] = [
            AromeProvider(),
            WindguruProvider(),
            SoarcastProvider(),
            OpenMeteoProvider(),  # always-available fallback
        ]
        self.tidal = RijkswaterstaatProvider()
        self.maps = GoogleMapsProvider()

    def get_available_providers(self) -> List[WeatherProvider]:
        return [p for p in self.providers if p.is_available()]

    def get_forecast(self, lat: float, lon: float, days: int,
                     preferred_model: Optional[str] = None) -> pd.DataFrame:
        """
        Get forecast from the highest-priority available provider.
        If preferred_model is set, try that first.
        """
        providers = self.get_available_providers()

        if preferred_model:
            for p in providers:
                if p.name == preferred_model:
                    df = p.get_forecast(lat, lon, days)
                    if not df.empty:
                        return df
                    break

        # Cascade through providers
        for p in providers:
            df = p.get_forecast(lat, lon, days)
            if not df.empty:
                return df

        return pd.DataFrame()

    def get_all_forecasts(self, lat: float, lon: float,
                          days: int) -> Dict[str, pd.DataFrame]:
        """Get forecasts from all available providers (for comparison)."""
        results = {}
        for p in self.get_available_providers():
            df = p.get_forecast(lat, lon, days)
            if not df.empty:
                results[p.name] = df
        return results

    def get_tidal_factor(self, lat: float, lon: float,
                         time: datetime) -> float:
        if self.tidal.is_available():
            return self.tidal.get_tidal_factor(lat, lon, time)
        return 0.0

    def get_travel_time(self, origin: tuple, dest: tuple) -> Optional[float]:
        if self.maps.is_available():
            return self.maps.get_travel_time(
                origin[0], origin[1], dest[0], dest[1]
            )
        return None
