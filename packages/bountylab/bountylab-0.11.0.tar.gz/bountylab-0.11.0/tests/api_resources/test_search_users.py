# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from bountylab import Bountylab, AsyncBountylab
from tests.utils import assert_matches_type
from bountylab.types import (
    SearchUserSearchResponse,
    SearchUserNaturalLanguageResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSearchUsers:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_natural_language(self, client: Bountylab) -> None:
        search_user = client.search_users.natural_language(
            query="Find machine learning engineers at Google who work on AI infrastructure",
        )
        assert_matches_type(SearchUserNaturalLanguageResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_natural_language_with_all_params(self, client: Bountylab) -> None:
        search_user = client.search_users.natural_language(
            query="Find machine learning engineers at Google who work on AI infrastructure",
            max_results=50,
        )
        assert_matches_type(SearchUserNaturalLanguageResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_natural_language(self, client: Bountylab) -> None:
        response = client.search_users.with_raw_response.natural_language(
            query="Find machine learning engineers at Google who work on AI infrastructure",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        search_user = response.parse()
        assert_matches_type(SearchUserNaturalLanguageResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_natural_language(self, client: Bountylab) -> None:
        with client.search_users.with_streaming_response.natural_language(
            query="Find machine learning engineers at Google who work on AI infrastructure",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            search_user = response.parse()
            assert_matches_type(SearchUserNaturalLanguageResponse, search_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: Bountylab) -> None:
        search_user = client.search_users.search(
            query="machine learning engineer san francisco",
        )
        assert_matches_type(SearchUserSearchResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search_with_all_params(self, client: Bountylab) -> None:
        search_user = client.search_users.search(
            query="machine learning engineer san francisco",
            filters={
                "field": "company",
                "op": "Eq",
                "value": "GitHub",
            },
            max_results=50,
        )
        assert_matches_type(SearchUserSearchResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: Bountylab) -> None:
        response = client.search_users.with_raw_response.search(
            query="machine learning engineer san francisco",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        search_user = response.parse()
        assert_matches_type(SearchUserSearchResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: Bountylab) -> None:
        with client.search_users.with_streaming_response.search(
            query="machine learning engineer san francisco",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            search_user = response.parse()
            assert_matches_type(SearchUserSearchResponse, search_user, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSearchUsers:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_natural_language(self, async_client: AsyncBountylab) -> None:
        search_user = await async_client.search_users.natural_language(
            query="Find machine learning engineers at Google who work on AI infrastructure",
        )
        assert_matches_type(SearchUserNaturalLanguageResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_natural_language_with_all_params(self, async_client: AsyncBountylab) -> None:
        search_user = await async_client.search_users.natural_language(
            query="Find machine learning engineers at Google who work on AI infrastructure",
            max_results=50,
        )
        assert_matches_type(SearchUserNaturalLanguageResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_natural_language(self, async_client: AsyncBountylab) -> None:
        response = await async_client.search_users.with_raw_response.natural_language(
            query="Find machine learning engineers at Google who work on AI infrastructure",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        search_user = await response.parse()
        assert_matches_type(SearchUserNaturalLanguageResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_natural_language(self, async_client: AsyncBountylab) -> None:
        async with async_client.search_users.with_streaming_response.natural_language(
            query="Find machine learning engineers at Google who work on AI infrastructure",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            search_user = await response.parse()
            assert_matches_type(SearchUserNaturalLanguageResponse, search_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncBountylab) -> None:
        search_user = await async_client.search_users.search(
            query="machine learning engineer san francisco",
        )
        assert_matches_type(SearchUserSearchResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncBountylab) -> None:
        search_user = await async_client.search_users.search(
            query="machine learning engineer san francisco",
            filters={
                "field": "company",
                "op": "Eq",
                "value": "GitHub",
            },
            max_results=50,
        )
        assert_matches_type(SearchUserSearchResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncBountylab) -> None:
        response = await async_client.search_users.with_raw_response.search(
            query="machine learning engineer san francisco",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        search_user = await response.parse()
        assert_matches_type(SearchUserSearchResponse, search_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncBountylab) -> None:
        async with async_client.search_users.with_streaming_response.search(
            query="machine learning engineer san francisco",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            search_user = await response.parse()
            assert_matches_type(SearchUserSearchResponse, search_user, path=["response"])

        assert cast(Any, response.is_closed) is True
