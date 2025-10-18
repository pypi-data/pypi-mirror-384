from datetime import datetime

from pydantic import BaseModel


class TrackStat(BaseModel):
    Count: int
    FirstPlayed: datetime | None
    LastPlayed: datetime | None
    Added: datetime | None
    Subsong: int | None
    Path: str
