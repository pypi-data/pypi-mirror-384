# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from bountylab import Bountylab, AsyncBountylab
from tests.utils import assert_matches_type
from bountylab.types import (
    SearchRepoSearchResponse,
    SearchRepoNaturalLanguageResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSearchRepos:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_natural_language(self, client: Bountylab) -> None:
        search_repo = client.search_repos.natural_language(
            query="Find React libraries with over 1000 stars that have good TypeScript support and are actively maintained",
        )
        assert_matches_type(SearchRepoNaturalLanguageResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_natural_language_with_all_params(self, client: Bountylab) -> None:
        search_repo = client.search_repos.natural_language(
            query="Find React libraries with over 1000 stars that have good TypeScript support and are actively maintained",
            include_attributes={
                "contributors": {"limit": 10},
                "owner": True,
                "starrers": {"limit": 5},
            },
            max_results=50,
        )
        assert_matches_type(SearchRepoNaturalLanguageResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_natural_language(self, client: Bountylab) -> None:
        response = client.search_repos.with_raw_response.natural_language(
            query="Find React libraries with over 1000 stars that have good TypeScript support and are actively maintained",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        search_repo = response.parse()
        assert_matches_type(SearchRepoNaturalLanguageResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_natural_language(self, client: Bountylab) -> None:
        with client.search_repos.with_streaming_response.natural_language(
            query="Find React libraries with over 1000 stars that have good TypeScript support and are actively maintained",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            search_repo = response.parse()
            assert_matches_type(SearchRepoNaturalLanguageResponse, search_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: Bountylab) -> None:
        search_repo = client.search_repos.search(
            query="react component library with typescript",
        )
        assert_matches_type(SearchRepoSearchResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search_with_all_params(self, client: Bountylab) -> None:
        search_repo = client.search_repos.search(
            query="react component library with typescript",
            filters={
                "field": "language",
                "op": "Eq",
                "value": "TypeScript",
            },
            include_attributes={
                "contributors": {"limit": 10},
                "owner": True,
                "starrers": {"limit": 5},
            },
            max_results=50,
        )
        assert_matches_type(SearchRepoSearchResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: Bountylab) -> None:
        response = client.search_repos.with_raw_response.search(
            query="react component library with typescript",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        search_repo = response.parse()
        assert_matches_type(SearchRepoSearchResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: Bountylab) -> None:
        with client.search_repos.with_streaming_response.search(
            query="react component library with typescript",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            search_repo = response.parse()
            assert_matches_type(SearchRepoSearchResponse, search_repo, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSearchRepos:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_natural_language(self, async_client: AsyncBountylab) -> None:
        search_repo = await async_client.search_repos.natural_language(
            query="Find React libraries with over 1000 stars that have good TypeScript support and are actively maintained",
        )
        assert_matches_type(SearchRepoNaturalLanguageResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_natural_language_with_all_params(self, async_client: AsyncBountylab) -> None:
        search_repo = await async_client.search_repos.natural_language(
            query="Find React libraries with over 1000 stars that have good TypeScript support and are actively maintained",
            include_attributes={
                "contributors": {"limit": 10},
                "owner": True,
                "starrers": {"limit": 5},
            },
            max_results=50,
        )
        assert_matches_type(SearchRepoNaturalLanguageResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_natural_language(self, async_client: AsyncBountylab) -> None:
        response = await async_client.search_repos.with_raw_response.natural_language(
            query="Find React libraries with over 1000 stars that have good TypeScript support and are actively maintained",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        search_repo = await response.parse()
        assert_matches_type(SearchRepoNaturalLanguageResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_natural_language(self, async_client: AsyncBountylab) -> None:
        async with async_client.search_repos.with_streaming_response.natural_language(
            query="Find React libraries with over 1000 stars that have good TypeScript support and are actively maintained",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            search_repo = await response.parse()
            assert_matches_type(SearchRepoNaturalLanguageResponse, search_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncBountylab) -> None:
        search_repo = await async_client.search_repos.search(
            query="react component library with typescript",
        )
        assert_matches_type(SearchRepoSearchResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncBountylab) -> None:
        search_repo = await async_client.search_repos.search(
            query="react component library with typescript",
            filters={
                "field": "language",
                "op": "Eq",
                "value": "TypeScript",
            },
            include_attributes={
                "contributors": {"limit": 10},
                "owner": True,
                "starrers": {"limit": 5},
            },
            max_results=50,
        )
        assert_matches_type(SearchRepoSearchResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncBountylab) -> None:
        response = await async_client.search_repos.with_raw_response.search(
            query="react component library with typescript",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        search_repo = await response.parse()
        assert_matches_type(SearchRepoSearchResponse, search_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncBountylab) -> None:
        async with async_client.search_repos.with_streaming_response.search(
            query="react component library with typescript",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            search_repo = await response.parse()
            assert_matches_type(SearchRepoSearchResponse, search_repo, path=["response"])

        assert cast(Any, response.is_closed) is True
