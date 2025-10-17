# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["MonitorSubmitEventResponse", "Data"]


class Data(BaseModel):
    evaluation_id: str
    """A unique evaluation ID associated with this event."""

    event_id: str
    """A unique monitor event ID."""

    monitor_id: str
    """Monitor ID associated with this event."""

    created_at: Optional[datetime] = None
    """The time the monitor event was created in UTC."""


class MonitorSubmitEventResponse(BaseModel):
    success: bool
    """Represents whether the request was completed successfully."""

    data: Optional[Data] = None

    message: Optional[str] = None
    """The accompanying message for the request.

    Includes error details when applicable.
    """
