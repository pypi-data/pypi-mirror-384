import os
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel


class PerformedBy(BaseModel):
    type: Literal["system"]
    id: str
    timestamp: datetime


def get_performed_by_now() -> PerformedBy:
    return PerformedBy(
        type="system",
        id=os.environ.get("DATABUTTON_PROJECT_ID", "unknown"),
        timestamp=datetime.now(timezone.utc),
    )
