# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["MonitorCreateParams"]


class MonitorCreateParams(TypedDict, total=False):
    name: Required[str]
    """Name of the new monitor."""

    description: str
    """Description of the new monitor."""
