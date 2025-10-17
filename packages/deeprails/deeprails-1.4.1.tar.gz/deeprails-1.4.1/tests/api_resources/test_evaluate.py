# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from deeprails import Deeprails, AsyncDeeprails
from tests.utils import assert_matches_type
from deeprails.types import Evaluation

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEvaluate:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Deeprails) -> None:
        evaluate = client.evaluate.create(
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
            run_mode="precision_plus",
        )
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Deeprails) -> None:
        evaluate = client.evaluate.create(
            model_input={
                "user_prompt": "user_prompt",
                "context": "context",
            },
            model_output="model_output",
            run_mode="precision_plus",
            guardrail_metrics=["correctness"],
            model_used="model_used",
            nametag="nametag",
        )
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Deeprails) -> None:
        response = client.evaluate.with_raw_response.create(
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
            run_mode="precision_plus",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluate = response.parse()
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Deeprails) -> None:
        with client.evaluate.with_streaming_response.create(
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
            run_mode="precision_plus",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluate = response.parse()
            assert_matches_type(Evaluation, evaluate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Deeprails) -> None:
        evaluate = client.evaluate.retrieve(
            "eval_id",
        )
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Deeprails) -> None:
        response = client.evaluate.with_raw_response.retrieve(
            "eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluate = response.parse()
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Deeprails) -> None:
        with client.evaluate.with_streaming_response.retrieve(
            "eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluate = response.parse()
            assert_matches_type(Evaluation, evaluate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Deeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            client.evaluate.with_raw_response.retrieve(
                "",
            )


class TestAsyncEvaluate:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDeeprails) -> None:
        evaluate = await async_client.evaluate.create(
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
            run_mode="precision_plus",
        )
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncDeeprails) -> None:
        evaluate = await async_client.evaluate.create(
            model_input={
                "user_prompt": "user_prompt",
                "context": "context",
            },
            model_output="model_output",
            run_mode="precision_plus",
            guardrail_metrics=["correctness"],
            model_used="model_used",
            nametag="nametag",
        )
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.evaluate.with_raw_response.create(
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
            run_mode="precision_plus",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluate = await response.parse()
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDeeprails) -> None:
        async with async_client.evaluate.with_streaming_response.create(
            model_input={"user_prompt": "user_prompt"},
            model_output="model_output",
            run_mode="precision_plus",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluate = await response.parse()
            assert_matches_type(Evaluation, evaluate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDeeprails) -> None:
        evaluate = await async_client.evaluate.retrieve(
            "eval_id",
        )
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDeeprails) -> None:
        response = await async_client.evaluate.with_raw_response.retrieve(
            "eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        evaluate = await response.parse()
        assert_matches_type(Evaluation, evaluate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDeeprails) -> None:
        async with async_client.evaluate.with_streaming_response.retrieve(
            "eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            evaluate = await response.parse()
            assert_matches_type(Evaluation, evaluate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDeeprails) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            await async_client.evaluate.with_raw_response.retrieve(
                "",
            )
