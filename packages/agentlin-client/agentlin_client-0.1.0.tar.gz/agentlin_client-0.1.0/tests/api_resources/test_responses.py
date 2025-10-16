# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from agentlin_client import Client, AsyncClient
from agentlin_client.types import (
    Response,
    ResponseListInputItemsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestResponses:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Client) -> None:
        response = client.responses.create()
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Client) -> None:
        response = client.responses.create(
            background=True,
            conversation="string",
            include=["code_interpreter_call.outputs"],
            input="string",
            instructions="instructions",
            max_output_tokens=0,
            max_tool_calls=0,
            metadata={"foo": "string"},
            model="o1-pro",
            parallel_tool_calls=True,
            previous_response_id="previous_response_id",
            prompt={
                "id": "id",
                "variables": {"foo": "string"},
                "version": "version",
            },
            prompt_cache_key="prompt-cache-key-1234",
            reasoning={
                "effort": "minimal",
                "generate_summary": "auto",
                "summary": "auto",
            },
            safety_identifier="safety-identifier-1234",
            service_tier="auto",
            store=True,
            stream=True,
            stream_options={"include_obfuscation": True},
            temperature=1,
            text={
                "format": {"type": "text"},
                "verbosity": "low",
            },
            tool_choice={"type": "none"},
            tools=[
                {
                    "name": "name",
                    "parameters": {"foo": "bar"},
                    "strict": True,
                    "type": "function",
                    "description": "description",
                }
            ],
            top_logprobs=0,
            top_p=1,
            truncation="auto",
            user="user-1234",
        )
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Client) -> None:
        http_response = client.responses.with_raw_response.create()

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = http_response.parse()
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Client) -> None:
        with client.responses.with_streaming_response.create() as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = http_response.parse()
            assert_matches_type(Response, response, path=["response"])

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Client) -> None:
        response = client.responses.retrieve(
            response_id="resp_677efb5139a88190b512bc3fef8e535d",
        )
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: Client) -> None:
        response = client.responses.retrieve(
            response_id="resp_677efb5139a88190b512bc3fef8e535d",
            include=["code_interpreter_call.outputs"],
            include_obfuscation=True,
            starting_after=0,
            stream=True,
        )
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Client) -> None:
        http_response = client.responses.with_raw_response.retrieve(
            response_id="resp_677efb5139a88190b512bc3fef8e535d",
        )

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = http_response.parse()
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Client) -> None:
        with client.responses.with_streaming_response.retrieve(
            response_id="resp_677efb5139a88190b512bc3fef8e535d",
        ) as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = http_response.parse()
            assert_matches_type(Response, response, path=["response"])

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `response_id` but received ''"):
            client.responses.with_raw_response.retrieve(
                response_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Client) -> None:
        response = client.responses.delete(
            "resp_677efb5139a88190b512bc3fef8e535d",
        )
        assert response is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Client) -> None:
        http_response = client.responses.with_raw_response.delete(
            "resp_677efb5139a88190b512bc3fef8e535d",
        )

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = http_response.parse()
        assert response is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Client) -> None:
        with client.responses.with_streaming_response.delete(
            "resp_677efb5139a88190b512bc3fef8e535d",
        ) as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = http_response.parse()
            assert response is None

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `response_id` but received ''"):
            client.responses.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cancel(self, client: Client) -> None:
        response = client.responses.cancel(
            "resp_677efb5139a88190b512bc3fef8e535d",
        )
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_cancel(self, client: Client) -> None:
        http_response = client.responses.with_raw_response.cancel(
            "resp_677efb5139a88190b512bc3fef8e535d",
        )

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = http_response.parse()
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_cancel(self, client: Client) -> None:
        with client.responses.with_streaming_response.cancel(
            "resp_677efb5139a88190b512bc3fef8e535d",
        ) as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = http_response.parse()
            assert_matches_type(Response, response, path=["response"])

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_cancel(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `response_id` but received ''"):
            client.responses.with_raw_response.cancel(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_input_items(self, client: Client) -> None:
        response = client.responses.list_input_items(
            response_id="response_id",
        )
        assert_matches_type(ResponseListInputItemsResponse, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_input_items_with_all_params(self, client: Client) -> None:
        response = client.responses.list_input_items(
            response_id="response_id",
            after="after",
            include=["code_interpreter_call.outputs"],
            limit=0,
            order="asc",
        )
        assert_matches_type(ResponseListInputItemsResponse, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_input_items(self, client: Client) -> None:
        http_response = client.responses.with_raw_response.list_input_items(
            response_id="response_id",
        )

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = http_response.parse()
        assert_matches_type(ResponseListInputItemsResponse, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_input_items(self, client: Client) -> None:
        with client.responses.with_streaming_response.list_input_items(
            response_id="response_id",
        ) as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = http_response.parse()
            assert_matches_type(ResponseListInputItemsResponse, response, path=["response"])

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_input_items(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `response_id` but received ''"):
            client.responses.with_raw_response.list_input_items(
                response_id="",
            )


class TestAsyncResponses:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncClient) -> None:
        response = await async_client.responses.create()
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncClient) -> None:
        response = await async_client.responses.create(
            background=True,
            conversation="string",
            include=["code_interpreter_call.outputs"],
            input="string",
            instructions="instructions",
            max_output_tokens=0,
            max_tool_calls=0,
            metadata={"foo": "string"},
            model="o1-pro",
            parallel_tool_calls=True,
            previous_response_id="previous_response_id",
            prompt={
                "id": "id",
                "variables": {"foo": "string"},
                "version": "version",
            },
            prompt_cache_key="prompt-cache-key-1234",
            reasoning={
                "effort": "minimal",
                "generate_summary": "auto",
                "summary": "auto",
            },
            safety_identifier="safety-identifier-1234",
            service_tier="auto",
            store=True,
            stream=True,
            stream_options={"include_obfuscation": True},
            temperature=1,
            text={
                "format": {"type": "text"},
                "verbosity": "low",
            },
            tool_choice={"type": "none"},
            tools=[
                {
                    "name": "name",
                    "parameters": {"foo": "bar"},
                    "strict": True,
                    "type": "function",
                    "description": "description",
                }
            ],
            top_logprobs=0,
            top_p=1,
            truncation="auto",
            user="user-1234",
        )
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncClient) -> None:
        http_response = await async_client.responses.with_raw_response.create()

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = await http_response.parse()
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncClient) -> None:
        async with async_client.responses.with_streaming_response.create() as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = await http_response.parse()
            assert_matches_type(Response, response, path=["response"])

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncClient) -> None:
        response = await async_client.responses.retrieve(
            response_id="resp_677efb5139a88190b512bc3fef8e535d",
        )
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncClient) -> None:
        response = await async_client.responses.retrieve(
            response_id="resp_677efb5139a88190b512bc3fef8e535d",
            include=["code_interpreter_call.outputs"],
            include_obfuscation=True,
            starting_after=0,
            stream=True,
        )
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncClient) -> None:
        http_response = await async_client.responses.with_raw_response.retrieve(
            response_id="resp_677efb5139a88190b512bc3fef8e535d",
        )

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = await http_response.parse()
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncClient) -> None:
        async with async_client.responses.with_streaming_response.retrieve(
            response_id="resp_677efb5139a88190b512bc3fef8e535d",
        ) as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = await http_response.parse()
            assert_matches_type(Response, response, path=["response"])

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `response_id` but received ''"):
            await async_client.responses.with_raw_response.retrieve(
                response_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncClient) -> None:
        response = await async_client.responses.delete(
            "resp_677efb5139a88190b512bc3fef8e535d",
        )
        assert response is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncClient) -> None:
        http_response = await async_client.responses.with_raw_response.delete(
            "resp_677efb5139a88190b512bc3fef8e535d",
        )

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = await http_response.parse()
        assert response is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncClient) -> None:
        async with async_client.responses.with_streaming_response.delete(
            "resp_677efb5139a88190b512bc3fef8e535d",
        ) as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = await http_response.parse()
            assert response is None

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `response_id` but received ''"):
            await async_client.responses.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cancel(self, async_client: AsyncClient) -> None:
        response = await async_client.responses.cancel(
            "resp_677efb5139a88190b512bc3fef8e535d",
        )
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncClient) -> None:
        http_response = await async_client.responses.with_raw_response.cancel(
            "resp_677efb5139a88190b512bc3fef8e535d",
        )

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = await http_response.parse()
        assert_matches_type(Response, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncClient) -> None:
        async with async_client.responses.with_streaming_response.cancel(
            "resp_677efb5139a88190b512bc3fef8e535d",
        ) as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = await http_response.parse()
            assert_matches_type(Response, response, path=["response"])

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `response_id` but received ''"):
            await async_client.responses.with_raw_response.cancel(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_input_items(self, async_client: AsyncClient) -> None:
        response = await async_client.responses.list_input_items(
            response_id="response_id",
        )
        assert_matches_type(ResponseListInputItemsResponse, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_input_items_with_all_params(self, async_client: AsyncClient) -> None:
        response = await async_client.responses.list_input_items(
            response_id="response_id",
            after="after",
            include=["code_interpreter_call.outputs"],
            limit=0,
            order="asc",
        )
        assert_matches_type(ResponseListInputItemsResponse, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_input_items(self, async_client: AsyncClient) -> None:
        http_response = await async_client.responses.with_raw_response.list_input_items(
            response_id="response_id",
        )

        assert http_response.is_closed is True
        assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"
        response = await http_response.parse()
        assert_matches_type(ResponseListInputItemsResponse, response, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_input_items(self, async_client: AsyncClient) -> None:
        async with async_client.responses.with_streaming_response.list_input_items(
            response_id="response_id",
        ) as http_response:
            assert not http_response.is_closed
            assert http_response.http_request.headers.get("X-Stainless-Lang") == "python"

            response = await http_response.parse()
            assert_matches_type(ResponseListInputItemsResponse, response, path=["response"])

        assert cast(Any, http_response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_input_items(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `response_id` but received ''"):
            await async_client.responses.with_raw_response.list_input_items(
                response_id="",
            )
