# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["MonitorUpdateParams"]


class MonitorUpdateParams(TypedDict, total=False):
    description: str
    """Description of the monitor."""

    monitor_status: Literal["active", "inactive"]
    """Status of the monitor.

    Can be `active` or `inactive`. Inactive monitors no longer record and evaluate
    events.
    """

    name: str
    """Name of the monitor."""
