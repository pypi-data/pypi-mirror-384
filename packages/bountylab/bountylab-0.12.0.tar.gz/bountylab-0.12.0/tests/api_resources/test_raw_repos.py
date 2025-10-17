# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from bountylab import Bountylab, AsyncBountylab
from tests.utils import assert_matches_type
from bountylab.types import (
    RawRepoOwnsResponse,
    RawRepoStarsResponse,
    RawRepoRetrieveResponse,
    RawRepoByFullnameResponse,
    RawRepoContributesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRawRepos:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Bountylab) -> None:
        raw_repo = client.raw_repos.retrieve(
            "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )
        assert_matches_type(RawRepoRetrieveResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Bountylab) -> None:
        response = client.raw_repos.with_raw_response.retrieve(
            "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = response.parse()
        assert_matches_type(RawRepoRetrieveResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Bountylab) -> None:
        with client.raw_repos.with_streaming_response.retrieve(
            "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = response.parse()
            assert_matches_type(RawRepoRetrieveResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_repos.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_by_fullname(self, client: Bountylab) -> None:
        raw_repo = client.raw_repos.by_fullname(
            full_names=["octocat/Hello-World", "torvalds/linux"],
        )
        assert_matches_type(RawRepoByFullnameResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_by_fullname(self, client: Bountylab) -> None:
        response = client.raw_repos.with_raw_response.by_fullname(
            full_names=["octocat/Hello-World", "torvalds/linux"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = response.parse()
        assert_matches_type(RawRepoByFullnameResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_by_fullname(self, client: Bountylab) -> None:
        with client.raw_repos.with_streaming_response.by_fullname(
            full_names=["octocat/Hello-World", "torvalds/linux"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = response.parse()
            assert_matches_type(RawRepoByFullnameResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_contributes(self, client: Bountylab) -> None:
        raw_repo = client.raw_repos.contributes(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )
        assert_matches_type(RawRepoContributesResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_contributes_with_all_params(self, client: Bountylab) -> None:
        raw_repo = client.raw_repos.contributes(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawRepoContributesResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_contributes(self, client: Bountylab) -> None:
        response = client.raw_repos.with_raw_response.contributes(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = response.parse()
        assert_matches_type(RawRepoContributesResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_contributes(self, client: Bountylab) -> None:
        with client.raw_repos.with_streaming_response.contributes(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = response.parse()
            assert_matches_type(RawRepoContributesResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_contributes(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_repos.with_raw_response.contributes(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_owns(self, client: Bountylab) -> None:
        raw_repo = client.raw_repos.owns(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )
        assert_matches_type(RawRepoOwnsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_owns_with_all_params(self, client: Bountylab) -> None:
        raw_repo = client.raw_repos.owns(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawRepoOwnsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_owns(self, client: Bountylab) -> None:
        response = client.raw_repos.with_raw_response.owns(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = response.parse()
        assert_matches_type(RawRepoOwnsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_owns(self, client: Bountylab) -> None:
        with client.raw_repos.with_streaming_response.owns(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = response.parse()
            assert_matches_type(RawRepoOwnsResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_owns(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_repos.with_raw_response.owns(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_stars(self, client: Bountylab) -> None:
        raw_repo = client.raw_repos.stars(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )
        assert_matches_type(RawRepoStarsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_stars_with_all_params(self, client: Bountylab) -> None:
        raw_repo = client.raw_repos.stars(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawRepoStarsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_stars(self, client: Bountylab) -> None:
        response = client.raw_repos.with_raw_response.stars(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = response.parse()
        assert_matches_type(RawRepoStarsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_stars(self, client: Bountylab) -> None:
        with client.raw_repos.with_streaming_response.stars(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = response.parse()
            assert_matches_type(RawRepoStarsResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_stars(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_repos.with_raw_response.stars(
                id="",
            )


class TestAsyncRawRepos:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBountylab) -> None:
        raw_repo = await async_client.raw_repos.retrieve(
            "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )
        assert_matches_type(RawRepoRetrieveResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_repos.with_raw_response.retrieve(
            "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = await response.parse()
        assert_matches_type(RawRepoRetrieveResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_repos.with_streaming_response.retrieve(
            "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = await response.parse()
            assert_matches_type(RawRepoRetrieveResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_repos.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_by_fullname(self, async_client: AsyncBountylab) -> None:
        raw_repo = await async_client.raw_repos.by_fullname(
            full_names=["octocat/Hello-World", "torvalds/linux"],
        )
        assert_matches_type(RawRepoByFullnameResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_by_fullname(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_repos.with_raw_response.by_fullname(
            full_names=["octocat/Hello-World", "torvalds/linux"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = await response.parse()
        assert_matches_type(RawRepoByFullnameResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_by_fullname(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_repos.with_streaming_response.by_fullname(
            full_names=["octocat/Hello-World", "torvalds/linux"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = await response.parse()
            assert_matches_type(RawRepoByFullnameResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_contributes(self, async_client: AsyncBountylab) -> None:
        raw_repo = await async_client.raw_repos.contributes(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )
        assert_matches_type(RawRepoContributesResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_contributes_with_all_params(self, async_client: AsyncBountylab) -> None:
        raw_repo = await async_client.raw_repos.contributes(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawRepoContributesResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_contributes(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_repos.with_raw_response.contributes(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = await response.parse()
        assert_matches_type(RawRepoContributesResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_contributes(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_repos.with_streaming_response.contributes(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = await response.parse()
            assert_matches_type(RawRepoContributesResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_contributes(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_repos.with_raw_response.contributes(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_owns(self, async_client: AsyncBountylab) -> None:
        raw_repo = await async_client.raw_repos.owns(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )
        assert_matches_type(RawRepoOwnsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_owns_with_all_params(self, async_client: AsyncBountylab) -> None:
        raw_repo = await async_client.raw_repos.owns(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawRepoOwnsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_owns(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_repos.with_raw_response.owns(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = await response.parse()
        assert_matches_type(RawRepoOwnsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_owns(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_repos.with_streaming_response.owns(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = await response.parse()
            assert_matches_type(RawRepoOwnsResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_owns(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_repos.with_raw_response.owns(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_stars(self, async_client: AsyncBountylab) -> None:
        raw_repo = await async_client.raw_repos.stars(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )
        assert_matches_type(RawRepoStarsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_stars_with_all_params(self, async_client: AsyncBountylab) -> None:
        raw_repo = await async_client.raw_repos.stars(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawRepoStarsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_stars(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_repos.with_raw_response.stars(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_repo = await response.parse()
        assert_matches_type(RawRepoStarsResponse, raw_repo, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_stars(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_repos.with_streaming_response.stars(
            id="MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_repo = await response.parse()
            assert_matches_type(RawRepoStarsResponse, raw_repo, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_stars(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_repos.with_raw_response.stars(
                id="",
            )
