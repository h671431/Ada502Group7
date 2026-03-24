"""MET.no data controller.

This module wraps the MET Norway Locationforecast API and provides
functions for fetching and normalizing weather time series data.

The controller is designed to be used from FastAPI endpoints, but it is
kept lightweight and testable.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx


MET_API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
MET_HEADERS = {
    "User-Agent": "FireGuard/0.1.0 (https://github.com/Ada502Group7/frcm)"
}


async def fetch_met_latest(
    latitude: float,
    longitude: float,
    altitude: Optional[float] = None,
) -> Dict[str, Any]:
    """Fetch latest weather observation from MET.no (most recent data up to now).

    Args:
        latitude: Latitude in degrees.
        longitude: Longitude in degrees.
        altitude: Optional altitude in meters.

    Returns:
        A dict with keys: timestamp, temperature, humidity, wind_speed.

    Raises:
        httpx.HTTPError: When the API request fails.
        ValueError: When the response doesn't contain data.
    """

    params: Dict[str, Any] = {"lat": latitude, "lon": longitude}
    if altitude is not None:
        params["altitude"] = altitude

    async with httpx.AsyncClient(headers=MET_HEADERS, timeout=30.0) as client:
        resp = await client.get(MET_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    timeseries = data.get("properties", {}).get("timeseries", [])
    if not timeseries:
        raise ValueError("No weather timeseries found in MET response")

    # Find the most recent entry that is at or before the current time
    now = datetime.now(datetime.now().astimezone().tzinfo)
    latest_entry = None

    for entry in timeseries:
        timestamp_str = entry.get("time")
        if not timestamp_str:
            continue

        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        
        # Only consider entries up to current time
        if timestamp <= now:
            latest_entry = entry
        else:
            break  # Since timeseries is sorted, stop when we exceed now

    if not latest_entry:
        # If no historical data, use the first available entry
        latest_entry = timeseries[0]

    timestamp_str = latest_entry.get("time")
    if not timestamp_str:
        raise ValueError("No valid timestamp in latest timeseries entry")

    details = latest_entry.get("data", {}).get("instant", {}).get("details", {})
    temp = details.get("air_temperature")
    rh = details.get("relative_humidity")
    wind = details.get("wind_speed")

    if temp is None or rh is None or wind is None:
        raise ValueError("Latest entry missing required weather fields")

    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return {
        "timestamp": timestamp.isoformat(),
        "temperature": temp,
        "humidity": rh,
        "wind_speed": wind,
    }


async def fetch_met_forecast(
    latitude: float,
    longitude: float,
    altitude: Optional[float] = None,
    days: int = 7,
) -> List[Dict[str, Any]]:
    """Fetch forecast from MET.no and return a normalized timeseries.

    Args:
        latitude: Latitude in degrees.
        longitude: Longitude in degrees.
        altitude: Optional altitude in meters.
        days: Forecast horizon in days.

    Returns:
        A list of dicts with keys: timestamp, temperature, humidity, wind_speed.

    Raises:
        httpx.HTTPError: When the API request fails.
        ValueError: When the response doesn't contain data.
    """

    params: Dict[str, Any] = {"lat": latitude, "lon": longitude}
    if altitude is not None:
        params["altitude"] = altitude

    async with httpx.AsyncClient(headers=MET_HEADERS, timeout=30.0) as client:
        resp = await client.get(MET_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    timeseries = data.get("properties", {}).get("timeseries", [])
    if not timeseries:
        raise ValueError("No weather timeseries found in MET response")

    now = datetime.now(datetime.now().astimezone().tzinfo)
    cutoff = now + timedelta(days=days)

    result: List[Dict[str, Any]] = []
    for entry in timeseries:
        timestamp_str = entry.get("time")
        if not timestamp_str:
            continue

        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if timestamp > cutoff:
            break

        details = entry.get("data", {}).get("instant", {}).get("details", {})
        temp = details.get("air_temperature")
        rh = details.get("relative_humidity")
        wind = details.get("wind_speed")

        if temp is None or rh is None or wind is None:
            continue

        result.append(
            {
                "timestamp": timestamp.isoformat(),
                "temperature": temp,
                "humidity": rh,
                "wind_speed": wind,
            }
        )

    if not result:
        raise ValueError("MET response did not contain usable weather points")

    return result
