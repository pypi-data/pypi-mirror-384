# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["DefendUpdateWorkflowParams"]


class DefendUpdateWorkflowParams(TypedDict, total=False):
    description: str
    """Description for the workflow."""

    name: str
    """Name of the workflow."""
