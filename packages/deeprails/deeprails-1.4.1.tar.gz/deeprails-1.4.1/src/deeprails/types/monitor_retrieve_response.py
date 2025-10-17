# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel
from .evaluation import Evaluation

__all__ = ["MonitorRetrieveResponse", "Data", "DataStats"]


class DataStats(BaseModel):
    completed_evaluations: Optional[int] = None
    """Number of evaluations that completed successfully."""

    failed_evaluations: Optional[int] = None
    """Number of evaluations that failed."""

    in_progress_evaluations: Optional[int] = None
    """Number of evaluations currently in progress."""

    queued_evaluations: Optional[int] = None
    """Number of evaluations currently queued."""

    total_evaluations: Optional[int] = None
    """Total number of evaluations performed by this monitor."""


class Data(BaseModel):
    monitor_id: str
    """A unique monitor ID."""

    monitor_status: Literal["active", "inactive"]
    """Status of the monitor.

    Can be `active` or `inactive`. Inactive monitors no longer record and evaluate
    events.
    """

    name: str
    """Name of this monitor."""

    created_at: Optional[datetime] = None
    """The time the monitor was created in UTC."""

    description: Optional[str] = None
    """Description of this monitor."""

    evaluations: Optional[List[Evaluation]] = None
    """An array of all evaluations performed by this monitor.

    Each one corresponds to a separate monitor event.
    """

    stats: Optional[DataStats] = None
    """
    Contains five fields used for stats of this monitor: total evaluations,
    completed evaluations, failed evaluations, queued evaluations, and in progress
    evaluations.
    """

    updated_at: Optional[datetime] = None
    """The most recent time the monitor was modified in UTC."""

    user_id: Optional[str] = None
    """User ID of the user who created the monitor."""


class MonitorRetrieveResponse(BaseModel):
    success: bool
    """Represents whether the request was completed successfully."""

    data: Optional[Data] = None

    message: Optional[str] = None
    """The accompanying message for the request.

    Includes error details when applicable.
    """
