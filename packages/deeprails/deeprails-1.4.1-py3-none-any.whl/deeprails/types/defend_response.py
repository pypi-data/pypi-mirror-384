# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["DefendResponse"]


class DefendResponse(BaseModel):
    name: str
    """Name of the workflow."""

    workflow_id: str
    """A unique workflow ID."""

    created_at: Optional[datetime] = None
    """The time the workflow was created in UTC."""

    description: Optional[str] = None
    """Description for the workflow."""

    improvement_action: Optional[Literal["regenerate", "fixit"]] = None
    """
    The action used to improve outputs that fail one or more guardrail metrics for
    the workflow events. May be `regenerate`, `fixit`, or null which represents “do
    nothing”. Regenerate runs the user's input prompt with minor induced variance.
    Fixit attempts to directly address the shortcomings of the output using the
    guardrail failure rationale. Do nothing does not attempt any improvement.
    """

    max_retries: Optional[int] = None
    """Max.

    number of improvement action retries until a given event passes the guardrails.
    """

    modified_at: Optional[datetime] = None
    """The most recent time the workflow was modified in UTC."""

    status: Optional[Literal["archived", "active"]] = None
    """Status of the selected workflow.

    May be `archived` or `active`. Archived workflows will not accept events.
    """

    success_rate: Optional[float] = None
    """Rate of events associated with this workflow that passed evaluation."""
