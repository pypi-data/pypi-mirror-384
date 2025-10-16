# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from agentlin_client import Client, AsyncClient
from agentlin_client.types.conversations import (
    ConversationItem,
    ConversationItemList,
    ConversationResource,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestItems:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Client) -> None:
        item = client.conversations.items.create(
            conversation_id="conv_123",
            items=[
                {
                    "content": "string",
                    "role": "user",
                    "type": "message",
                }
            ],
        )
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Client) -> None:
        item = client.conversations.items.create(
            conversation_id="conv_123",
            items=[
                {
                    "content": "string",
                    "role": "user",
                    "type": "message",
                }
            ],
            include=["code_interpreter_call.outputs"],
        )
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Client) -> None:
        response = client.conversations.items.with_raw_response.create(
            conversation_id="conv_123",
            items=[
                {
                    "content": "string",
                    "role": "user",
                    "type": "message",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Client) -> None:
        with client.conversations.items.with_streaming_response.create(
            conversation_id="conv_123",
            items=[
                {
                    "content": "string",
                    "role": "user",
                    "type": "message",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ConversationItemList, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_id` but received ''"):
            client.conversations.items.with_raw_response.create(
                conversation_id="",
                items=[
                    {
                        "content": "string",
                        "role": "user",
                        "type": "message",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Client) -> None:
        item = client.conversations.items.retrieve(
            item_id="msg_abc",
            conversation_id="conv_123",
        )
        assert_matches_type(ConversationItem, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: Client) -> None:
        item = client.conversations.items.retrieve(
            item_id="msg_abc",
            conversation_id="conv_123",
            include=["code_interpreter_call.outputs"],
        )
        assert_matches_type(ConversationItem, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Client) -> None:
        response = client.conversations.items.with_raw_response.retrieve(
            item_id="msg_abc",
            conversation_id="conv_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ConversationItem, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Client) -> None:
        with client.conversations.items.with_streaming_response.retrieve(
            item_id="msg_abc",
            conversation_id="conv_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ConversationItem, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_id` but received ''"):
            client.conversations.items.with_raw_response.retrieve(
                item_id="msg_abc",
                conversation_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `item_id` but received ''"):
            client.conversations.items.with_raw_response.retrieve(
                item_id="",
                conversation_id="conv_123",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Client) -> None:
        item = client.conversations.items.list(
            conversation_id="conv_123",
        )
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Client) -> None:
        item = client.conversations.items.list(
            conversation_id="conv_123",
            after="after",
            include=["code_interpreter_call.outputs"],
            limit=0,
            order="asc",
        )
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Client) -> None:
        response = client.conversations.items.with_raw_response.list(
            conversation_id="conv_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Client) -> None:
        with client.conversations.items.with_streaming_response.list(
            conversation_id="conv_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ConversationItemList, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_id` but received ''"):
            client.conversations.items.with_raw_response.list(
                conversation_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Client) -> None:
        item = client.conversations.items.delete(
            item_id="msg_abc",
            conversation_id="conv_123",
        )
        assert_matches_type(ConversationResource, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Client) -> None:
        response = client.conversations.items.with_raw_response.delete(
            item_id="msg_abc",
            conversation_id="conv_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ConversationResource, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Client) -> None:
        with client.conversations.items.with_streaming_response.delete(
            item_id="msg_abc",
            conversation_id="conv_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ConversationResource, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_id` but received ''"):
            client.conversations.items.with_raw_response.delete(
                item_id="msg_abc",
                conversation_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `item_id` but received ''"):
            client.conversations.items.with_raw_response.delete(
                item_id="",
                conversation_id="conv_123",
            )


class TestAsyncItems:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncClient) -> None:
        item = await async_client.conversations.items.create(
            conversation_id="conv_123",
            items=[
                {
                    "content": "string",
                    "role": "user",
                    "type": "message",
                }
            ],
        )
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncClient) -> None:
        item = await async_client.conversations.items.create(
            conversation_id="conv_123",
            items=[
                {
                    "content": "string",
                    "role": "user",
                    "type": "message",
                }
            ],
            include=["code_interpreter_call.outputs"],
        )
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncClient) -> None:
        response = await async_client.conversations.items.with_raw_response.create(
            conversation_id="conv_123",
            items=[
                {
                    "content": "string",
                    "role": "user",
                    "type": "message",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncClient) -> None:
        async with async_client.conversations.items.with_streaming_response.create(
            conversation_id="conv_123",
            items=[
                {
                    "content": "string",
                    "role": "user",
                    "type": "message",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ConversationItemList, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_id` but received ''"):
            await async_client.conversations.items.with_raw_response.create(
                conversation_id="",
                items=[
                    {
                        "content": "string",
                        "role": "user",
                        "type": "message",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncClient) -> None:
        item = await async_client.conversations.items.retrieve(
            item_id="msg_abc",
            conversation_id="conv_123",
        )
        assert_matches_type(ConversationItem, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncClient) -> None:
        item = await async_client.conversations.items.retrieve(
            item_id="msg_abc",
            conversation_id="conv_123",
            include=["code_interpreter_call.outputs"],
        )
        assert_matches_type(ConversationItem, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncClient) -> None:
        response = await async_client.conversations.items.with_raw_response.retrieve(
            item_id="msg_abc",
            conversation_id="conv_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ConversationItem, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncClient) -> None:
        async with async_client.conversations.items.with_streaming_response.retrieve(
            item_id="msg_abc",
            conversation_id="conv_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ConversationItem, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_id` but received ''"):
            await async_client.conversations.items.with_raw_response.retrieve(
                item_id="msg_abc",
                conversation_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `item_id` but received ''"):
            await async_client.conversations.items.with_raw_response.retrieve(
                item_id="",
                conversation_id="conv_123",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncClient) -> None:
        item = await async_client.conversations.items.list(
            conversation_id="conv_123",
        )
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncClient) -> None:
        item = await async_client.conversations.items.list(
            conversation_id="conv_123",
            after="after",
            include=["code_interpreter_call.outputs"],
            limit=0,
            order="asc",
        )
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncClient) -> None:
        response = await async_client.conversations.items.with_raw_response.list(
            conversation_id="conv_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ConversationItemList, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncClient) -> None:
        async with async_client.conversations.items.with_streaming_response.list(
            conversation_id="conv_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ConversationItemList, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_id` but received ''"):
            await async_client.conversations.items.with_raw_response.list(
                conversation_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncClient) -> None:
        item = await async_client.conversations.items.delete(
            item_id="msg_abc",
            conversation_id="conv_123",
        )
        assert_matches_type(ConversationResource, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncClient) -> None:
        response = await async_client.conversations.items.with_raw_response.delete(
            item_id="msg_abc",
            conversation_id="conv_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ConversationResource, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncClient) -> None:
        async with async_client.conversations.items.with_streaming_response.delete(
            item_id="msg_abc",
            conversation_id="conv_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ConversationResource, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `conversation_id` but received ''"):
            await async_client.conversations.items.with_raw_response.delete(
                item_id="msg_abc",
                conversation_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `item_id` but received ''"):
            await async_client.conversations.items.with_raw_response.delete(
                item_id="",
                conversation_id="conv_123",
            )
