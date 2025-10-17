# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["DefendCreateWorkflowParams"]


class DefendCreateWorkflowParams(TypedDict, total=False):
    improvement_action: Required[Optional[Literal["regenerate", "fixit"]]]
    """
    The action used to improve outputs that fail one or guardrail metrics for the
    workflow events. May be `regenerate`, `fixit`, or null which represents “do
    nothing”. Regenerate runs the user's input prompt with minor induced variance.
    Fixit attempts to directly address the shortcomings of the output using the
    guardrail failure rationale. Do nothing does not attempt any improvement.
    """

    metrics: Required[Dict[str, float]]
    """Mapping of guardrail metrics to floating point threshold values.

    If the workflow type is automatic, only the metric names are used
    (`automatic_tolerance` determines thresholds). Possible metrics are
    `correctness`, `completeness`, `instruction_adherence`, `context_adherence`,
    `ground_truth_adherence`, or `comprehensive_safety`.
    """

    name: Required[str]
    """Name of the workflow."""

    type: Required[Literal["automatic", "custom"]]
    """Type of thresholds to use for the workflow, either `automatic` or `custom`.

    Automatic thresholds are assigned internally after the user specifies a
    qualitative tolerance for the metrics, whereas custom metrics allow the user to
    set the threshold for each metric as a floating point number between 0.0 and
    1.0.
    """

    automatic_tolerance: Literal["low", "medium", "high"]
    """
    Hallucination tolerance for automatic workflows; may be `low`, `medium`, or
    `high`. Ignored if `type` is `custom`.
    """

    description: str
    """Description for the workflow."""

    max_retries: int
    """Max.

    number of improvement action retries until a given event passes the guardrails.
    Defaults to 10.
    """
