# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["WorkflowEventResponse"]


class WorkflowEventResponse(BaseModel):
    event_id: str
    """A unique workflow event ID."""

    workflow_id: str
    """Workflow ID associated with the event."""

    attempt_number: Optional[int] = None
    """Count of improvement attempts for the event.

    If greater than one then all previous improvement attempts failed.
    """

    evaluation_id: Optional[str] = None
    """A unique evaluation ID associated with this event.

    Every event has one or more evaluation attempts.
    """

    filtered: Optional[bool] = None
    """
    `False` if evaluation passed all of the guardrail metrics, `True` if evaluation
    failed any of the guardrail metrics.
    """
