from datetime import datetime, timezone, timedelta
from typing import List
from app.models.morning_report_dto import NewsItem


def get_news_items(limit: int = 5) -> List[NewsItem]:
    """
    Get news items with mock implementation.
    Returns deterministic mock data with stale logic.
    """
    now = datetime.now(timezone.utc)

    # Mock news data - deterministic based on current hour
    hour = now.hour

    mock_news = [
        {
            "id": f"news_{hour}_1",
            "title": "Tech Industry Shows Strong Growth in Q4",
            "source": "Tech News Daily",
            "url": "https://example.com/tech-growth-q4",
            "publishedISO": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": f"news_{hour}_2",
            "title": "Climate Summit Reaches New Agreement",
            "source": "Global Times",
            "url": "https://example.com/climate-summit",
            "publishedISO": (now - timedelta(hours=4)).isoformat(),
        },
        {
            "id": f"news_{hour}_3",
            "title": "Local Sports Team Wins Championship",
            "source": "Sports Central",
            "url": "https://example.com/championship-win",
            "publishedISO": (now - timedelta(hours=6)).isoformat(),
        },
        {
            "id": f"news_{hour}_4",
            "title": "New AI Breakthrough in Medical Research",
            "source": "Science Weekly",
            "url": "https://example.com/ai-medical-research",
            "publishedISO": (now - timedelta(hours=8)).isoformat(),
        },
        {
            "id": f"news_{hour}_5",
            "title": "Economic Markets Show Positive Trends",
            "source": "Financial Times",
            "url": "https://example.com/economic-trends",
            "publishedISO": (now - timedelta(hours=12)).isoformat(),
        },
    ]

    # Return limited number of items
    return [NewsItem(**item) for item in mock_news[:limit]]


def get_live_news_items(limit: int = 5, category: str = "general") -> List[NewsItem]:
    """
    Placeholder for live news API integration.
    Currently returns mock data.
    """
    # TODO: Implement actual news API integration (e.g., NewsAPI, RSS feeds)
    # For now, return mock data
    return get_news_items(limit)


def is_news_stale(last_update: datetime) -> bool:
    """
    Check if news data is stale (older than 1 hour).
    """
    now = datetime.now(timezone.utc)
    return (now - last_update) > timedelta(hours=1)
