from datetime import datetime, timezone
from typing import Optional
from app.models.morning_report import WeatherSnapshot


def get_weather_snapshot() -> WeatherSnapshot:
    """
    Get weather data with mock implementation.
    Returns deterministic mock data with stale logic.
    """
    now = datetime.now(timezone.utc)

    # Mock weather data - deterministic based on current hour
    hour = now.hour
    conditions = ["sunny", "cloudy", "rainy", "partly_cloudy"]
    condition = conditions[hour % len(conditions)]

    # Temperature varies by hour (20-25°C range)
    temp_c = 20 + (hour % 6)

    # Determine if data is stale (older than 30 minutes)
    # In mock mode, we'll simulate stale data every 5th call
    stale = hour % 5 == 0

    icons = {"sunny": "☀️", "cloudy": "☁️", "rainy": "🌧️", "partly_cloudy": "⛅"}

    return WeatherSnapshot(
        updatedISO=now.isoformat(),
        tempC=temp_c,
        condition=condition,
        icon=icons.get(condition, "☀️"),
        stale=stale,
    )


def get_live_weather_snapshot(location: str = "London") -> WeatherSnapshot:
    """
    Placeholder for live weather API integration.
    Currently returns mock data.
    """
    # TODO: Implement actual weather API integration
    # For now, return mock data
    return get_weather_snapshot()
