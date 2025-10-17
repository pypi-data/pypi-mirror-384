# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from deeprails import Deeprails, AsyncDeeprails
from tests.utils import assert_matches_type
from deeprails.types import (
    APIResponse,
    MonitorRetrieveResponse,
    MonitorSubmitEventResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMonitor:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Deeprails) -> None:
        monitor = client.monitor.create(
            name="name",
        )
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Deeprails) -> None:
        monitor = client.monitor.create(
            name="name",
            description="description",
        )
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Deeprails) -> None:
        response = client.monitor.with_raw_response.create(
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        monitor = response.parse()
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Deeprails) -> None:
        with client.monitor.with_streaming_response.create(
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            monitor = response.parse()
            assert_matches_type(APIResponse, monitor, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Deeprails) -> None:
        monitor = client.monitor.retrieve(
            monitor_id="monitor_id",
        )
        assert_matches_type(MonitorRetrieveResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: Deeprails) -> None:
        monitor = client.monitor.retrieve(
            monitor_id="monitor_id",
            limit=0,
        )
        assert_matches_type(MonitorRetrieveResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Deeprails) -> None:
        response = client.monitor.with_raw_response.retrieve(
            monitor_id="monitor_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        monitor = response.parse()
        assert_matches_type(MonitorRetrieveResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Deeprails) -> None:
        with client.monitor.with_streaming_response.retrieve(
            monitor_id="monitor_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            monitor = response.parse()
            assert_matches_type(MonitorRetrieveResponse, monitor, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Deeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `monitor_id` but received ''"):
            client.monitor.with_raw_response.retrieve(
                monitor_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Deeprails) -> None:
        monitor = client.monitor.update(
            monitor_id="monitor_id",
        )
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Deeprails) -> None:
        monitor = client.monitor.update(
            monitor_id="monitor_id",
            description="description",
            monitor_status="active",
            name="name",
        )
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Deeprails) -> None:
        response = client.monitor.with_raw_response.update(
            monitor_id="monitor_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        monitor = response.parse()
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Deeprails) -> None:
        with client.monitor.with_streaming_response.update(
            monitor_id="monitor_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            monitor = response.parse()
            assert_matches_type(APIResponse, monitor, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Deeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `monitor_id` but received ''"):
            client.monitor.with_raw_response.update(
                monitor_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_event(self, client: Deeprails) -> None:
        monitor = client.monitor.submit_event(
            monitor_id="monitor_id",
            guardrail_metrics=["correctness"],
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
        )
        assert_matches_type(MonitorSubmitEventResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_event_with_all_params(self, client: Deeprails) -> None:
        monitor = client.monitor.submit_event(
            monitor_id="monitor_id",
            guardrail_metrics=["correctness"],
            model_input={
                "user_prompt": "user_prompt",
                "context": "context",
            },
            model_output="model_output",
            model_used="model_used",
            nametag="nametag",
            run_mode="precision_plus",
        )
        assert_matches_type(MonitorSubmitEventResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_submit_event(self, client: Deeprails) -> None:
        response = client.monitor.with_raw_response.submit_event(
            monitor_id="monitor_id",
            guardrail_metrics=["correctness"],
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        monitor = response.parse()
        assert_matches_type(MonitorSubmitEventResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_submit_event(self, client: Deeprails) -> None:
        with client.monitor.with_streaming_response.submit_event(
            monitor_id="monitor_id",
            guardrail_metrics=["correctness"],
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            monitor = response.parse()
            assert_matches_type(MonitorSubmitEventResponse, monitor, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_submit_event(self, client: Deeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `monitor_id` but received ''"):
            client.monitor.with_raw_response.submit_event(
                monitor_id="",
                guardrail_metrics=["correctness"],
                model_input={"user_prompt": "user_prompt"},
                model_output="model_output",
            )


class TestAsyncMonitor:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDeeprails) -> None:
        monitor = await async_client.monitor.create(
            name="name",
        )
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncDeeprails) -> None:
        monitor = await async_client.monitor.create(
            name="name",
            description="description",
        )
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.monitor.with_raw_response.create(
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        monitor = await response.parse()
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDeeprails) -> None:
        async with async_client.monitor.with_streaming_response.create(
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            monitor = await response.parse()
            assert_matches_type(APIResponse, monitor, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDeeprails) -> None:
        monitor = await async_client.monitor.retrieve(
            monitor_id="monitor_id",
        )
        assert_matches_type(MonitorRetrieveResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncDeeprails) -> None:
        monitor = await async_client.monitor.retrieve(
            monitor_id="monitor_id",
            limit=0,
        )
        assert_matches_type(MonitorRetrieveResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.monitor.with_raw_response.retrieve(
            monitor_id="monitor_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        monitor = await response.parse()
        assert_matches_type(MonitorRetrieveResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDeeprails) -> None:
        async with async_client.monitor.with_streaming_response.retrieve(
            monitor_id="monitor_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            monitor = await response.parse()
            assert_matches_type(MonitorRetrieveResponse, monitor, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDeeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `monitor_id` but received ''"):
            await async_client.monitor.with_raw_response.retrieve(
                monitor_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncDeeprails) -> None:
        monitor = await async_client.monitor.update(
            monitor_id="monitor_id",
        )
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncDeeprails) -> None:
        monitor = await async_client.monitor.update(
            monitor_id="monitor_id",
            description="description",
            monitor_status="active",
            name="name",
        )
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.monitor.with_raw_response.update(
            monitor_id="monitor_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        monitor = await response.parse()
        assert_matches_type(APIResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncDeeprails) -> None:
        async with async_client.monitor.with_streaming_response.update(
            monitor_id="monitor_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            monitor = await response.parse()
            assert_matches_type(APIResponse, monitor, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncDeeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `monitor_id` but received ''"):
            await async_client.monitor.with_raw_response.update(
                monitor_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_event(self, async_client: AsyncDeeprails) -> None:
        monitor = await async_client.monitor.submit_event(
            monitor_id="monitor_id",
            guardrail_metrics=["correctness"],
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
        )
        assert_matches_type(MonitorSubmitEventResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_event_with_all_params(self, async_client: AsyncDeeprails) -> None:
        monitor = await async_client.monitor.submit_event(
            monitor_id="monitor_id",
            guardrail_metrics=["correctness"],
            model_input={
                "user_prompt": "user_prompt",
                "context": "context",
            },
            model_output="model_output",
            model_used="model_used",
            nametag="nametag",
            run_mode="precision_plus",
        )
        assert_matches_type(MonitorSubmitEventResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_submit_event(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.monitor.with_raw_response.submit_event(
            monitor_id="monitor_id",
            guardrail_metrics=["correctness"],
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        monitor = await response.parse()
        assert_matches_type(MonitorSubmitEventResponse, monitor, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_submit_event(self, async_client: AsyncDeeprails) -> None:
        async with async_client.monitor.with_streaming_response.submit_event(
            monitor_id="monitor_id",
            guardrail_metrics=["correctness"],
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            monitor = await response.parse()
            assert_matches_type(MonitorSubmitEventResponse, monitor, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_submit_event(self, async_client: AsyncDeeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `monitor_id` but received ''"):
            await async_client.monitor.with_raw_response.submit_event(
                monitor_id="",
                guardrail_metrics=["correctness"],
                model_input={"user_prompt": "user_prompt"},
                model_output="model_output",
            )
