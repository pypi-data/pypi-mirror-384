from datetime import datetime

from pydantic import BaseModel, Field


class SyncMeta(BaseModel):
    class Config:
        extra = "allow"

    last_sync_time: datetime = Field(
        default=datetime.fromisoformat("1900-01-01T00:00:00Z")
    )
