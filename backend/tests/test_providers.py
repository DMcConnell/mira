"""Tests for data providers."""

import pytest
from datetime import datetime, timedelta

from app.providers.weather import get_weather_snapshot
from app.providers.news import get_news_items, is_news_stale
from app.providers.calendar import (
    get_calendar_items,
    is_calendar_stale,
    get_upcoming_events,
)


class TestWeatherProvider:
    """Tests for weather provider."""

    def test_get_weather_snapshot(self):
        """Test getting weather snapshot."""
        weather = get_weather_snapshot()

        assert weather is not None
        assert hasattr(weather, "updatedISO")
        assert hasattr(weather, "tempC")
        assert hasattr(weather, "condition")
        assert hasattr(weather, "icon")
        assert hasattr(weather, "stale")

    def test_weather_temperature_type(self):
        """Test weather temperature is a number."""
        weather = get_weather_snapshot()
        assert isinstance(weather.tempC, (int, float))

    def test_weather_condition_string(self):
        """Test weather condition is a string."""
        weather = get_weather_snapshot()
        assert isinstance(weather.condition, str)
        assert len(weather.condition) > 0

    def test_weather_stale_boolean(self):
        """Test weather stale is a boolean."""
        weather = get_weather_snapshot()
        assert isinstance(weather.stale, bool)

    def test_weather_updated_iso_format(self):
        """Test weather updated timestamp is valid ISO format."""
        weather = get_weather_snapshot()
        # Should be parseable as ISO datetime
        datetime.fromisoformat(weather.updatedISO.replace("Z", "+00:00"))


class TestNewsProvider:
    """Tests for news provider."""

    def test_get_news_items_default(self):
        """Test getting news items with default limit."""
        news = get_news_items()

        assert isinstance(news, list)
        assert len(news) <= 5  # Default limit

    def test_get_news_items_custom_limit(self):
        """Test getting news items with custom limit."""
        news = get_news_items(limit=3)

        assert isinstance(news, list)
        assert len(news) <= 3

    def test_news_item_structure(self):
        """Test news item has correct structure."""
        news = get_news_items(limit=1)

        assert len(news) > 0
        item = news[0]

        assert hasattr(item, "id")
        assert hasattr(item, "title")
        assert hasattr(item, "source")
        assert hasattr(item, "url")
        assert hasattr(item, "publishedISO")

    def test_news_item_types(self):
        """Test news item field types."""
        news = get_news_items(limit=1)
        item = news[0]

        assert isinstance(item.id, str)
        assert isinstance(item.title, str)
        assert isinstance(item.source, str)
        assert isinstance(item.url, str)
        assert isinstance(item.publishedISO, str)

    def test_is_news_stale(self):
        """Test news staleness check."""
        from datetime import timezone, timedelta

        # Recent update - not stale
        recent = datetime.now(timezone.utc) - timedelta(minutes=30)
        assert not is_news_stale(recent)

        # Old update - stale
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        assert is_news_stale(old)


class TestCalendarProvider:
    """Tests for calendar provider."""

    def test_get_calendar_items_default(self):
        """Test getting calendar items with default limit."""
        calendar = get_calendar_items()

        assert isinstance(calendar, list)
        # May be empty or have items depending on time of day

    def test_get_calendar_items_custom_limit(self):
        """Test getting calendar items with custom limit."""
        calendar = get_calendar_items(limit=5)

        assert isinstance(calendar, list)
        assert len(calendar) <= 5

    def test_calendar_item_structure(self):
        """Test calendar item structure if items exist."""
        calendar = get_calendar_items()

        if len(calendar) > 0:
            item = calendar[0]

            assert hasattr(item, "id")
            assert hasattr(item, "title")
            assert hasattr(item, "startsAtISO")
            assert hasattr(item, "endsAtISO")
            assert hasattr(item, "location")

    def test_calendar_item_types(self):
        """Test calendar item field types."""
        calendar = get_calendar_items()

        if len(calendar) > 0:
            item = calendar[0]

            assert isinstance(item.id, str)
            assert isinstance(item.title, str)
            assert isinstance(item.startsAtISO, str)
            assert isinstance(item.endsAtISO, str)
            # location can be None or str

    def test_calendar_items_sorted(self):
        """Test that calendar items are sorted by start time."""
        calendar = get_calendar_items()

        if len(calendar) > 1:
            for i in range(len(calendar) - 1):
                current_start = calendar[i].startsAtISO
                next_start = calendar[i + 1].startsAtISO
                assert current_start <= next_start

    def test_is_calendar_stale(self):
        """Test calendar staleness check."""
        from datetime import timezone, timedelta

        # Recent update - not stale
        recent = datetime.now(timezone.utc) - timedelta(minutes=10)
        assert not is_calendar_stale(recent)

        # Old update - stale
        old = datetime.now(timezone.utc) - timedelta(minutes=20)
        assert is_calendar_stale(old)

    def test_get_upcoming_events(self):
        """Test getting upcoming events."""
        upcoming = get_upcoming_events(hours_ahead=24)

        assert isinstance(upcoming, list)

        # All events should be in the future
        now = datetime.now()
        for event in upcoming:
            event_start = datetime.fromisoformat(
                event.startsAtISO.replace("Z", "+00:00")
            )
            # Remove timezone for comparison (simplified)
            assert event_start.replace(tzinfo=None) >= now.replace(
                tzinfo=None
            ) - timedelta(hours=1)
