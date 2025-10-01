from fastapi import APIRouter

from app.models.morning_report_dto import MorningReport
from app.providers.calendar import get_calendar_items
from app.providers.news import get_news_items
from app.providers.weather import get_weather_snapshot
from app.api.todos import get_all_todos

router = APIRouter()


@router.get("/api/v1/morning-report", response_model=MorningReport)
async def get_morning_report():
    """Get the morning report aggregating all data sources."""
    try:
        # Fetch data from all providers
        calendar = get_calendar_items(limit=10)
        weather = get_weather_snapshot()
        news = get_news_items(limit=5)
        todos = get_all_todos()

        return MorningReport(calendar=calendar, weather=weather, news=news, todos=todos)
    except Exception as e:
        # In case of any errors, return empty data rather than failing completely
        from app.models.morning_report_dto import (
            CalendarItem,
            NewsItem,
            Todo,
            WeatherSnapshot,
        )
        from datetime import datetime, timezone

        return MorningReport(
            calendar=[],
            weather=WeatherSnapshot(
                updatedISO=datetime.now(timezone.utc).isoformat(),
                tempC=20.0,
                condition="unknown",
                icon="❓",
                stale=True,
            ),
            news=[],
            todos=[],
        )
