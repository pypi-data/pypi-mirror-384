# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["MonitorRetrieveParams"]


class MonitorRetrieveParams(TypedDict, total=False):
    limit: int
    """Limit the returned events associated with this monitor. Defaults to 10."""
