# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Literal

import httpx

from ..types import defend_submit_event_params, defend_create_workflow_params, defend_update_workflow_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.defend_response import DefendResponse
from ..types.workflow_event_response import WorkflowEventResponse

__all__ = ["DefendResource", "AsyncDefendResource"]


class DefendResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DefendResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/deeprails/deeprails-sdk-python#accessing-raw-response-data-eg-headers
        """
        return DefendResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DefendResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/deeprails/deeprails-sdk-python#with_streaming_response
        """
        return DefendResourceWithStreamingResponse(self)

    def create_workflow(
        self,
        *,
        improvement_action: Optional[Literal["regenerate", "fixit"]],
        metrics: Dict[str, float],
        name: str,
        type: Literal["automatic", "custom"],
        automatic_tolerance: Literal["low", "medium", "high"] | Omit = omit,
        description: str | Omit = omit,
        max_retries: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DefendResponse:
        """
        Use this endpoint to create a new guardrail workflow with optional guardrail
        thresholds and improvement actions

        Args:
          improvement_action: The action used to improve outputs that fail one or guardrail metrics for the
              workflow events. May be `regenerate`, `fixit`, or null which represents “do
              nothing”. Regenerate runs the user's input prompt with minor induced variance.
              Fixit attempts to directly address the shortcomings of the output using the
              guardrail failure rationale. Do nothing does not attempt any improvement.

          metrics: Mapping of guardrail metrics to floating point threshold values. If the workflow
              type is automatic, only the metric names are used (`automatic_tolerance`
              determines thresholds). Possible metrics are `correctness`, `completeness`,
              `instruction_adherence`, `context_adherence`, `ground_truth_adherence`, or
              `comprehensive_safety`.

          name: Name of the workflow.

          type: Type of thresholds to use for the workflow, either `automatic` or `custom`.
              Automatic thresholds are assigned internally after the user specifies a
              qualitative tolerance for the metrics, whereas custom metrics allow the user to
              set the threshold for each metric as a floating point number between 0.0 and
              1.0.

          automatic_tolerance: Hallucination tolerance for automatic workflows; may be `low`, `medium`, or
              `high`. Ignored if `type` is `custom`.

          description: Description for the workflow.

          max_retries: Max. number of improvement action retries until a given event passes the
              guardrails. Defaults to 10.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/defend",
            body=maybe_transform(
                {
                    "improvement_action": improvement_action,
                    "metrics": metrics,
                    "name": name,
                    "type": type,
                    "automatic_tolerance": automatic_tolerance,
                    "description": description,
                    "max_retries": max_retries,
                },
                defend_create_workflow_params.DefendCreateWorkflowParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DefendResponse,
        )

    def retrieve_event(
        self,
        event_id: str,
        *,
        workflow_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkflowEventResponse:
        """
        Use this endpoint to retrieve a specific event of a guardrail workflow

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workflow_id:
            raise ValueError(f"Expected a non-empty value for `workflow_id` but received {workflow_id!r}")
        if not event_id:
            raise ValueError(f"Expected a non-empty value for `event_id` but received {event_id!r}")
        return self._get(
            f"/defend/{workflow_id}/events/{event_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkflowEventResponse,
        )

    def retrieve_workflow(
        self,
        workflow_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DefendResponse:
        """
        Use this endpoint to retrieve the details for a specific defend workflow

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workflow_id:
            raise ValueError(f"Expected a non-empty value for `workflow_id` but received {workflow_id!r}")
        return self._get(
            f"/defend/{workflow_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DefendResponse,
        )

    def submit_event(
        self,
        workflow_id: str,
        *,
        model_input: defend_submit_event_params.ModelInput,
        model_output: str,
        model_used: str,
        run_mode: Literal["precision_plus", "precision", "smart", "economy"],
        nametag: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkflowEventResponse:
        """
        Use this endpoint to submit a model input and output pair to a workflow for
        evaluation

        Args:
          model_input: A dictionary of inputs sent to the LLM to generate output. The dictionary must
              contain at least one of `user_prompt` or `system_prompt`. For
              ground_truth_aherence guadrail metric, `ground_truth` should be provided.

          model_output: Output generated by the LLM to be evaluated.

          model_used: Model ID used to generate the output, like `gpt-4o` or `o3`.

          run_mode: Run mode for the workflow event. The run mode allows the user to optimize for
              speed, accuracy, and cost by determining which models are used to evaluate the
              event. Available run modes include `precision_plus`, `precision`, `smart`, and
              `economy`. Defaults to `smart`.

          nametag: An optional, user-defined tag for the event.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workflow_id:
            raise ValueError(f"Expected a non-empty value for `workflow_id` but received {workflow_id!r}")
        return self._post(
            f"/defend/{workflow_id}/events",
            body=maybe_transform(
                {
                    "model_input": model_input,
                    "model_output": model_output,
                    "model_used": model_used,
                    "run_mode": run_mode,
                    "nametag": nametag,
                },
                defend_submit_event_params.DefendSubmitEventParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkflowEventResponse,
        )

    def update_workflow(
        self,
        workflow_id: str,
        *,
        description: str | Omit = omit,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DefendResponse:
        """
        Use this endpoint to update an existing guardrail workflow

        Args:
          description: Description for the workflow.

          name: Name of the workflow.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workflow_id:
            raise ValueError(f"Expected a non-empty value for `workflow_id` but received {workflow_id!r}")
        return self._put(
            f"/defend/{workflow_id}",
            body=maybe_transform(
                {
                    "description": description,
                    "name": name,
                },
                defend_update_workflow_params.DefendUpdateWorkflowParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DefendResponse,
        )


class AsyncDefendResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDefendResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/deeprails/deeprails-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncDefendResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDefendResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/deeprails/deeprails-sdk-python#with_streaming_response
        """
        return AsyncDefendResourceWithStreamingResponse(self)

    async def create_workflow(
        self,
        *,
        improvement_action: Optional[Literal["regenerate", "fixit"]],
        metrics: Dict[str, float],
        name: str,
        type: Literal["automatic", "custom"],
        automatic_tolerance: Literal["low", "medium", "high"] | Omit = omit,
        description: str | Omit = omit,
        max_retries: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DefendResponse:
        """
        Use this endpoint to create a new guardrail workflow with optional guardrail
        thresholds and improvement actions

        Args:
          improvement_action: The action used to improve outputs that fail one or guardrail metrics for the
              workflow events. May be `regenerate`, `fixit`, or null which represents “do
              nothing”. Regenerate runs the user's input prompt with minor induced variance.
              Fixit attempts to directly address the shortcomings of the output using the
              guardrail failure rationale. Do nothing does not attempt any improvement.

          metrics: Mapping of guardrail metrics to floating point threshold values. If the workflow
              type is automatic, only the metric names are used (`automatic_tolerance`
              determines thresholds). Possible metrics are `correctness`, `completeness`,
              `instruction_adherence`, `context_adherence`, `ground_truth_adherence`, or
              `comprehensive_safety`.

          name: Name of the workflow.

          type: Type of thresholds to use for the workflow, either `automatic` or `custom`.
              Automatic thresholds are assigned internally after the user specifies a
              qualitative tolerance for the metrics, whereas custom metrics allow the user to
              set the threshold for each metric as a floating point number between 0.0 and
              1.0.

          automatic_tolerance: Hallucination tolerance for automatic workflows; may be `low`, `medium`, or
              `high`. Ignored if `type` is `custom`.

          description: Description for the workflow.

          max_retries: Max. number of improvement action retries until a given event passes the
              guardrails. Defaults to 10.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/defend",
            body=await async_maybe_transform(
                {
                    "improvement_action": improvement_action,
                    "metrics": metrics,
                    "name": name,
                    "type": type,
                    "automatic_tolerance": automatic_tolerance,
                    "description": description,
                    "max_retries": max_retries,
                },
                defend_create_workflow_params.DefendCreateWorkflowParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DefendResponse,
        )

    async def retrieve_event(
        self,
        event_id: str,
        *,
        workflow_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkflowEventResponse:
        """
        Use this endpoint to retrieve a specific event of a guardrail workflow

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workflow_id:
            raise ValueError(f"Expected a non-empty value for `workflow_id` but received {workflow_id!r}")
        if not event_id:
            raise ValueError(f"Expected a non-empty value for `event_id` but received {event_id!r}")
        return await self._get(
            f"/defend/{workflow_id}/events/{event_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkflowEventResponse,
        )

    async def retrieve_workflow(
        self,
        workflow_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DefendResponse:
        """
        Use this endpoint to retrieve the details for a specific defend workflow

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workflow_id:
            raise ValueError(f"Expected a non-empty value for `workflow_id` but received {workflow_id!r}")
        return await self._get(
            f"/defend/{workflow_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DefendResponse,
        )

    async def submit_event(
        self,
        workflow_id: str,
        *,
        model_input: defend_submit_event_params.ModelInput,
        model_output: str,
        model_used: str,
        run_mode: Literal["precision_plus", "precision", "smart", "economy"],
        nametag: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WorkflowEventResponse:
        """
        Use this endpoint to submit a model input and output pair to a workflow for
        evaluation

        Args:
          model_input: A dictionary of inputs sent to the LLM to generate output. The dictionary must
              contain at least one of `user_prompt` or `system_prompt`. For
              ground_truth_aherence guadrail metric, `ground_truth` should be provided.

          model_output: Output generated by the LLM to be evaluated.

          model_used: Model ID used to generate the output, like `gpt-4o` or `o3`.

          run_mode: Run mode for the workflow event. The run mode allows the user to optimize for
              speed, accuracy, and cost by determining which models are used to evaluate the
              event. Available run modes include `precision_plus`, `precision`, `smart`, and
              `economy`. Defaults to `smart`.

          nametag: An optional, user-defined tag for the event.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workflow_id:
            raise ValueError(f"Expected a non-empty value for `workflow_id` but received {workflow_id!r}")
        return await self._post(
            f"/defend/{workflow_id}/events",
            body=await async_maybe_transform(
                {
                    "model_input": model_input,
                    "model_output": model_output,
                    "model_used": model_used,
                    "run_mode": run_mode,
                    "nametag": nametag,
                },
                defend_submit_event_params.DefendSubmitEventParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WorkflowEventResponse,
        )

    async def update_workflow(
        self,
        workflow_id: str,
        *,
        description: str | Omit = omit,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DefendResponse:
        """
        Use this endpoint to update an existing guardrail workflow

        Args:
          description: Description for the workflow.

          name: Name of the workflow.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workflow_id:
            raise ValueError(f"Expected a non-empty value for `workflow_id` but received {workflow_id!r}")
        return await self._put(
            f"/defend/{workflow_id}",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "name": name,
                },
                defend_update_workflow_params.DefendUpdateWorkflowParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DefendResponse,
        )


class DefendResourceWithRawResponse:
    def __init__(self, defend: DefendResource) -> None:
        self._defend = defend

        self.create_workflow = to_raw_response_wrapper(
            defend.create_workflow,
        )
        self.retrieve_event = to_raw_response_wrapper(
            defend.retrieve_event,
        )
        self.retrieve_workflow = to_raw_response_wrapper(
            defend.retrieve_workflow,
        )
        self.submit_event = to_raw_response_wrapper(
            defend.submit_event,
        )
        self.update_workflow = to_raw_response_wrapper(
            defend.update_workflow,
        )


class AsyncDefendResourceWithRawResponse:
    def __init__(self, defend: AsyncDefendResource) -> None:
        self._defend = defend

        self.create_workflow = async_to_raw_response_wrapper(
            defend.create_workflow,
        )
        self.retrieve_event = async_to_raw_response_wrapper(
            defend.retrieve_event,
        )
        self.retrieve_workflow = async_to_raw_response_wrapper(
            defend.retrieve_workflow,
        )
        self.submit_event = async_to_raw_response_wrapper(
            defend.submit_event,
        )
        self.update_workflow = async_to_raw_response_wrapper(
            defend.update_workflow,
        )


class DefendResourceWithStreamingResponse:
    def __init__(self, defend: DefendResource) -> None:
        self._defend = defend

        self.create_workflow = to_streamed_response_wrapper(
            defend.create_workflow,
        )
        self.retrieve_event = to_streamed_response_wrapper(
            defend.retrieve_event,
        )
        self.retrieve_workflow = to_streamed_response_wrapper(
            defend.retrieve_workflow,
        )
        self.submit_event = to_streamed_response_wrapper(
            defend.submit_event,
        )
        self.update_workflow = to_streamed_response_wrapper(
            defend.update_workflow,
        )


class AsyncDefendResourceWithStreamingResponse:
    def __init__(self, defend: AsyncDefendResource) -> None:
        self._defend = defend

        self.create_workflow = async_to_streamed_response_wrapper(
            defend.create_workflow,
        )
        self.retrieve_event = async_to_streamed_response_wrapper(
            defend.retrieve_event,
        )
        self.retrieve_workflow = async_to_streamed_response_wrapper(
            defend.retrieve_workflow,
        )
        self.submit_event = async_to_streamed_response_wrapper(
            defend.submit_event,
        )
        self.update_workflow = async_to_streamed_response_wrapper(
            defend.update_workflow,
        )
