from pydantic import BaseModel, Field
from typing import List, Optional


class CalendarItem(BaseModel):
    id: str
    title: str
    startsAtISO: str
    endsAtISO: str
    location: Optional[str] = None


class WeatherSnapshot(BaseModel):
    updatedISO: str
    tempC: float
    condition: str
    icon: str
    stale: bool = False


class NewsItem(BaseModel):
    id: str
    title: str
    source: str
    url: str
    publishedISO: str


class Todo(BaseModel):
    id: str
    text: str
    done: bool = False
    createdAtISO: str


class MorningReport(BaseModel):
    calendar: List[CalendarItem]
    weather: WeatherSnapshot
    news: List[NewsItem]
    todos: List[Todo]
