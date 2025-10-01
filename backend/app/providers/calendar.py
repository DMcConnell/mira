from datetime import datetime, timezone, timedelta
from typing import List
from app.models.morning_report import CalendarItem


def get_calendar_items(limit: int = 10) -> List[CalendarItem]:
    """
    Get calendar items with mock implementation.
    Returns deterministic mock data with stale logic.
    """
    now = datetime.now(timezone.utc)

    # Mock calendar data - deterministic based on current hour
    hour = now.hour
    day_of_week = now.weekday()  # 0 = Monday, 6 = Sunday

    # Generate mock calendar events for today and tomorrow
    mock_events = []

    # Today's events
    for i in range(3):
        event_time = now.replace(hour=9 + i * 3, minute=0, second=0, microsecond=0)
        if event_time > now:  # Only future events
            mock_events.append(
                {
                    "id": f"event_today_{i}",
                    "title": f"Meeting {i+1} - Project Discussion",
                    "startsAtISO": event_time.isoformat(),
                    "endsAtISO": (event_time + timedelta(hours=1)).isoformat(),
                    "location": f"Conference Room {chr(65 + i)}" if i < 2 else "Remote",
                }
            )

    # Tomorrow's events
    tomorrow = now + timedelta(days=1)
    for i in range(2):
        event_time = tomorrow.replace(
            hour=10 + i * 4, minute=30, second=0, microsecond=0
        )
        mock_events.append(
            {
                "id": f"event_tomorrow_{i}",
                "title": f"Tomorrow's Event {i+1}",
                "startsAtISO": event_time.isoformat(),
                "endsAtISO": (event_time + timedelta(hours=2)).isoformat(),
                "location": "Main Office" if i == 0 else None,
            }
        )

    # Add some weekend events if it's Friday or weekend
    if day_of_week >= 4:  # Friday, Saturday, Sunday
        weekend_start = now + timedelta(
            days=(5 - day_of_week) if day_of_week < 5 else 0
        )
        weekend_start = weekend_start.replace(
            hour=14, minute=0, second=0, microsecond=0
        )
        mock_events.append(
            {
                "id": "weekend_event",
                "title": "Weekend Planning Session",
                "startsAtISO": weekend_start.isoformat(),
                "endsAtISO": (weekend_start + timedelta(hours=1)).isoformat(),
                "location": "Home Office",
            }
        )

    # Return limited number of events, sorted by start time
    events = [CalendarItem(**event) for event in mock_events]
    events.sort(key=lambda x: x.startsAtISO)
    return events[:limit]


def get_live_calendar_items(
    limit: int = 10, calendar_id: str = "primary"
) -> List[CalendarItem]:
    """
    Placeholder for live calendar API integration.
    Currently returns mock data.
    """
    # TODO: Implement actual calendar API integration (e.g., Google Calendar, Outlook)
    # For now, return mock data
    return get_calendar_items(limit)


def is_calendar_stale(last_update: datetime) -> bool:
    """
    Check if calendar data is stale (older than 15 minutes).
    """
    now = datetime.now(timezone.utc)
    return (now - last_update) > timedelta(minutes=15)


def get_upcoming_events(hours_ahead: int = 24) -> List[CalendarItem]:
    """
    Get calendar events for the next N hours.
    """
    now = datetime.now(timezone.utc)
    cutoff_time = now + timedelta(hours=hours_ahead)

    all_events = get_calendar_items()

    # Filter events that start within the time window
    upcoming = []
    for event in all_events:
        event_start = datetime.fromisoformat(event.startsAtISO.replace("Z", "+00:00"))
        if now <= event_start <= cutoff_time:
            upcoming.append(event)

    return upcoming
