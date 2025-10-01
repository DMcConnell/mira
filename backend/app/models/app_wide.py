from pydantic import BaseModel


class VisionIntent(BaseModel):
    tsISO: str
    gesture: str
    confidence: float
    armed: bool


class Settings(BaseModel):
    weatherMode: str = "mock"
    newsMode: str = "mock"
