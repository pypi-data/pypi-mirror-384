# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from deeprails import Deeprails, AsyncDeeprails
from tests.utils import assert_matches_type
from deeprails.types import (
    DefendResponse,
    WorkflowEventResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDefend:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_workflow(self, client: Deeprails) -> None:
        defend = client.defend.create_workflow(
            improvement_action="regenerate",
            metrics={"foo": 0},
            name="name",
            type="automatic",
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_workflow_with_all_params(self, client: Deeprails) -> None:
        defend = client.defend.create_workflow(
            improvement_action="regenerate",
            metrics={"foo": 0},
            name="name",
            type="automatic",
            automatic_tolerance="low",
            description="description",
            max_retries=0,
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_workflow(self, client: Deeprails) -> None:
        response = client.defend.with_raw_response.create_workflow(
            improvement_action="regenerate",
            metrics={"foo": 0},
            name="name",
            type="automatic",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = response.parse()
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_workflow(self, client: Deeprails) -> None:
        with client.defend.with_streaming_response.create_workflow(
            improvement_action="regenerate",
            metrics={"foo": 0},
            name="name",
            type="automatic",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = response.parse()
            assert_matches_type(DefendResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_event(self, client: Deeprails) -> None:
        defend = client.defend.retrieve_event(
            event_id="event_id",
            workflow_id="workflow_id",
        )
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_event(self, client: Deeprails) -> None:
        response = client.defend.with_raw_response.retrieve_event(
            event_id="event_id",
            workflow_id="workflow_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = response.parse()
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_event(self, client: Deeprails) -> None:
        with client.defend.with_streaming_response.retrieve_event(
            event_id="event_id",
            workflow_id="workflow_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = response.parse()
            assert_matches_type(WorkflowEventResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_event(self, client: Deeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workflow_id` but received ''"):
            client.defend.with_raw_response.retrieve_event(
                event_id="event_id",
                workflow_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `event_id` but received ''"):
            client.defend.with_raw_response.retrieve_event(
                event_id="",
                workflow_id="workflow_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_workflow(self, client: Deeprails) -> None:
        defend = client.defend.retrieve_workflow(
            "workflow_id",
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_workflow(self, client: Deeprails) -> None:
        response = client.defend.with_raw_response.retrieve_workflow(
            "workflow_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = response.parse()
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_workflow(self, client: Deeprails) -> None:
        with client.defend.with_streaming_response.retrieve_workflow(
            "workflow_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = response.parse()
            assert_matches_type(DefendResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_workflow(self, client: Deeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workflow_id` but received ''"):
            client.defend.with_raw_response.retrieve_workflow(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_event(self, client: Deeprails) -> None:
        defend = client.defend.submit_event(
            workflow_id="workflow_id",
            model_input={},
            model_output="model_output",
            model_used="model_used",
            run_mode="precision_plus",
        )
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_event_with_all_params(self, client: Deeprails) -> None:
        defend = client.defend.submit_event(
            workflow_id="workflow_id",
            model_input={
                "ground_truth": "ground_truth",
                "system_prompt": "system_prompt",
                "user_prompt": "user_prompt",
            },
            model_output="model_output",
            model_used="model_used",
            run_mode="precision_plus",
            nametag="nametag",
        )
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_submit_event(self, client: Deeprails) -> None:
        response = client.defend.with_raw_response.submit_event(
            workflow_id="workflow_id",
            model_input={},
            model_output="model_output",
            model_used="model_used",
            run_mode="precision_plus",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = response.parse()
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_submit_event(self, client: Deeprails) -> None:
        with client.defend.with_streaming_response.submit_event(
            workflow_id="workflow_id",
            model_input={},
            model_output="model_output",
            model_used="model_used",
            run_mode="precision_plus",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = response.parse()
            assert_matches_type(WorkflowEventResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_submit_event(self, client: Deeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workflow_id` but received ''"):
            client.defend.with_raw_response.submit_event(
                workflow_id="",
                model_input={},
                model_output="model_output",
                model_used="model_used",
                run_mode="precision_plus",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_workflow(self, client: Deeprails) -> None:
        defend = client.defend.update_workflow(
            workflow_id="workflow_id",
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_workflow_with_all_params(self, client: Deeprails) -> None:
        defend = client.defend.update_workflow(
            workflow_id="workflow_id",
            description="description",
            name="name",
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_workflow(self, client: Deeprails) -> None:
        response = client.defend.with_raw_response.update_workflow(
            workflow_id="workflow_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = response.parse()
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_workflow(self, client: Deeprails) -> None:
        with client.defend.with_streaming_response.update_workflow(
            workflow_id="workflow_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = response.parse()
            assert_matches_type(DefendResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_workflow(self, client: Deeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workflow_id` but received ''"):
            client.defend.with_raw_response.update_workflow(
                workflow_id="",
            )


class TestAsyncDefend:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_workflow(self, async_client: AsyncDeeprails) -> None:
        defend = await async_client.defend.create_workflow(
            improvement_action="regenerate",
            metrics={"foo": 0},
            name="name",
            type="automatic",
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_workflow_with_all_params(self, async_client: AsyncDeeprails) -> None:
        defend = await async_client.defend.create_workflow(
            improvement_action="regenerate",
            metrics={"foo": 0},
            name="name",
            type="automatic",
            automatic_tolerance="low",
            description="description",
            max_retries=0,
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_workflow(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.defend.with_raw_response.create_workflow(
            improvement_action="regenerate",
            metrics={"foo": 0},
            name="name",
            type="automatic",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = await response.parse()
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_workflow(self, async_client: AsyncDeeprails) -> None:
        async with async_client.defend.with_streaming_response.create_workflow(
            improvement_action="regenerate",
            metrics={"foo": 0},
            name="name",
            type="automatic",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = await response.parse()
            assert_matches_type(DefendResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_event(self, async_client: AsyncDeeprails) -> None:
        defend = await async_client.defend.retrieve_event(
            event_id="event_id",
            workflow_id="workflow_id",
        )
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_event(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.defend.with_raw_response.retrieve_event(
            event_id="event_id",
            workflow_id="workflow_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = await response.parse()
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_event(self, async_client: AsyncDeeprails) -> None:
        async with async_client.defend.with_streaming_response.retrieve_event(
            event_id="event_id",
            workflow_id="workflow_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = await response.parse()
            assert_matches_type(WorkflowEventResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_event(self, async_client: AsyncDeeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workflow_id` but received ''"):
            await async_client.defend.with_raw_response.retrieve_event(
                event_id="event_id",
                workflow_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `event_id` but received ''"):
            await async_client.defend.with_raw_response.retrieve_event(
                event_id="",
                workflow_id="workflow_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_workflow(self, async_client: AsyncDeeprails) -> None:
        defend = await async_client.defend.retrieve_workflow(
            "workflow_id",
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_workflow(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.defend.with_raw_response.retrieve_workflow(
            "workflow_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = await response.parse()
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_workflow(self, async_client: AsyncDeeprails) -> None:
        async with async_client.defend.with_streaming_response.retrieve_workflow(
            "workflow_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = await response.parse()
            assert_matches_type(DefendResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_workflow(self, async_client: AsyncDeeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workflow_id` but received ''"):
            await async_client.defend.with_raw_response.retrieve_workflow(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_event(self, async_client: AsyncDeeprails) -> None:
        defend = await async_client.defend.submit_event(
            workflow_id="workflow_id",
            model_input={},
            model_output="model_output",
            model_used="model_used",
            run_mode="precision_plus",
        )
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_event_with_all_params(self, async_client: AsyncDeeprails) -> None:
        defend = await async_client.defend.submit_event(
            workflow_id="workflow_id",
            model_input={
                "ground_truth": "ground_truth",
                "system_prompt": "system_prompt",
                "user_prompt": "user_prompt",
            },
            model_output="model_output",
            model_used="model_used",
            run_mode="precision_plus",
            nametag="nametag",
        )
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_submit_event(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.defend.with_raw_response.submit_event(
            workflow_id="workflow_id",
            model_input={},
            model_output="model_output",
            model_used="model_used",
            run_mode="precision_plus",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = await response.parse()
        assert_matches_type(WorkflowEventResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_submit_event(self, async_client: AsyncDeeprails) -> None:
        async with async_client.defend.with_streaming_response.submit_event(
            workflow_id="workflow_id",
            model_input={},
            model_output="model_output",
            model_used="model_used",
            run_mode="precision_plus",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = await response.parse()
            assert_matches_type(WorkflowEventResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_submit_event(self, async_client: AsyncDeeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workflow_id` but received ''"):
            await async_client.defend.with_raw_response.submit_event(
                workflow_id="",
                model_input={},
                model_output="model_output",
                model_used="model_used",
                run_mode="precision_plus",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_workflow(self, async_client: AsyncDeeprails) -> None:
        defend = await async_client.defend.update_workflow(
            workflow_id="workflow_id",
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_workflow_with_all_params(self, async_client: AsyncDeeprails) -> None:
        defend = await async_client.defend.update_workflow(
            workflow_id="workflow_id",
            description="description",
            name="name",
        )
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_workflow(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.defend.with_raw_response.update_workflow(
            workflow_id="workflow_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        defend = await response.parse()
        assert_matches_type(DefendResponse, defend, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_workflow(self, async_client: AsyncDeeprails) -> None:
        async with async_client.defend.with_streaming_response.update_workflow(
            workflow_id="workflow_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            defend = await response.parse()
            assert_matches_type(DefendResponse, defend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_workflow(self, async_client: AsyncDeeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workflow_id` but received ''"):
            await async_client.defend.with_raw_response.update_workflow(
                workflow_id="",
            )
