# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from bountylab import Bountylab, AsyncBountylab
from tests.utils import assert_matches_type
from bountylab.types import (
    RawUserOwnsResponse,
    RawUserStarsResponse,
    RawUserByLoginResponse,
    RawUserRetrieveResponse,
    RawUserFollowersResponse,
    RawUserFollowingResponse,
    RawUserContributesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRawUsers:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Bountylab) -> None:
        raw_user = client.raw_users.retrieve(
            "MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserRetrieveResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Bountylab) -> None:
        response = client.raw_users.with_raw_response.retrieve(
            "MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = response.parse()
        assert_matches_type(RawUserRetrieveResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Bountylab) -> None:
        with client.raw_users.with_streaming_response.retrieve(
            "MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = response.parse()
            assert_matches_type(RawUserRetrieveResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_users.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_by_login(self, client: Bountylab) -> None:
        raw_user = client.raw_users.by_login(
            logins=["octocat", "torvalds"],
        )
        assert_matches_type(RawUserByLoginResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_by_login(self, client: Bountylab) -> None:
        response = client.raw_users.with_raw_response.by_login(
            logins=["octocat", "torvalds"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = response.parse()
        assert_matches_type(RawUserByLoginResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_by_login(self, client: Bountylab) -> None:
        with client.raw_users.with_streaming_response.by_login(
            logins=["octocat", "torvalds"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = response.parse()
            assert_matches_type(RawUserByLoginResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_contributes(self, client: Bountylab) -> None:
        raw_user = client.raw_users.contributes(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserContributesResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_contributes_with_all_params(self, client: Bountylab) -> None:
        raw_user = client.raw_users.contributes(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserContributesResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_contributes(self, client: Bountylab) -> None:
        response = client.raw_users.with_raw_response.contributes(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = response.parse()
        assert_matches_type(RawUserContributesResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_contributes(self, client: Bountylab) -> None:
        with client.raw_users.with_streaming_response.contributes(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = response.parse()
            assert_matches_type(RawUserContributesResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_contributes(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_users.with_raw_response.contributes(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_followers(self, client: Bountylab) -> None:
        raw_user = client.raw_users.followers(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserFollowersResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_followers_with_all_params(self, client: Bountylab) -> None:
        raw_user = client.raw_users.followers(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserFollowersResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_followers(self, client: Bountylab) -> None:
        response = client.raw_users.with_raw_response.followers(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = response.parse()
        assert_matches_type(RawUserFollowersResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_followers(self, client: Bountylab) -> None:
        with client.raw_users.with_streaming_response.followers(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = response.parse()
            assert_matches_type(RawUserFollowersResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_followers(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_users.with_raw_response.followers(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_following(self, client: Bountylab) -> None:
        raw_user = client.raw_users.following(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserFollowingResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_following_with_all_params(self, client: Bountylab) -> None:
        raw_user = client.raw_users.following(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserFollowingResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_following(self, client: Bountylab) -> None:
        response = client.raw_users.with_raw_response.following(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = response.parse()
        assert_matches_type(RawUserFollowingResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_following(self, client: Bountylab) -> None:
        with client.raw_users.with_streaming_response.following(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = response.parse()
            assert_matches_type(RawUserFollowingResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_following(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_users.with_raw_response.following(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_owns(self, client: Bountylab) -> None:
        raw_user = client.raw_users.owns(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserOwnsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_owns_with_all_params(self, client: Bountylab) -> None:
        raw_user = client.raw_users.owns(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserOwnsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_owns(self, client: Bountylab) -> None:
        response = client.raw_users.with_raw_response.owns(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = response.parse()
        assert_matches_type(RawUserOwnsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_owns(self, client: Bountylab) -> None:
        with client.raw_users.with_streaming_response.owns(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = response.parse()
            assert_matches_type(RawUserOwnsResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_owns(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_users.with_raw_response.owns(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_stars(self, client: Bountylab) -> None:
        raw_user = client.raw_users.stars(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserStarsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_stars_with_all_params(self, client: Bountylab) -> None:
        raw_user = client.raw_users.stars(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserStarsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_stars(self, client: Bountylab) -> None:
        response = client.raw_users.with_raw_response.stars(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = response.parse()
        assert_matches_type(RawUserStarsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_stars(self, client: Bountylab) -> None:
        with client.raw_users.with_streaming_response.stars(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = response.parse()
            assert_matches_type(RawUserStarsResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_stars(self, client: Bountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.raw_users.with_raw_response.stars(
                id="",
            )


class TestAsyncRawUsers:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.retrieve(
            "MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserRetrieveResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_users.with_raw_response.retrieve(
            "MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = await response.parse()
        assert_matches_type(RawUserRetrieveResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_users.with_streaming_response.retrieve(
            "MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = await response.parse()
            assert_matches_type(RawUserRetrieveResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_users.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_by_login(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.by_login(
            logins=["octocat", "torvalds"],
        )
        assert_matches_type(RawUserByLoginResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_by_login(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_users.with_raw_response.by_login(
            logins=["octocat", "torvalds"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = await response.parse()
        assert_matches_type(RawUserByLoginResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_by_login(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_users.with_streaming_response.by_login(
            logins=["octocat", "torvalds"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = await response.parse()
            assert_matches_type(RawUserByLoginResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_contributes(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.contributes(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserContributesResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_contributes_with_all_params(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.contributes(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserContributesResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_contributes(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_users.with_raw_response.contributes(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = await response.parse()
        assert_matches_type(RawUserContributesResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_contributes(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_users.with_streaming_response.contributes(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = await response.parse()
            assert_matches_type(RawUserContributesResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_contributes(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_users.with_raw_response.contributes(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_followers(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.followers(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserFollowersResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_followers_with_all_params(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.followers(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserFollowersResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_followers(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_users.with_raw_response.followers(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = await response.parse()
        assert_matches_type(RawUserFollowersResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_followers(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_users.with_streaming_response.followers(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = await response.parse()
            assert_matches_type(RawUserFollowersResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_followers(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_users.with_raw_response.followers(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_following(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.following(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserFollowingResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_following_with_all_params(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.following(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserFollowingResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_following(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_users.with_raw_response.following(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = await response.parse()
        assert_matches_type(RawUserFollowingResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_following(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_users.with_streaming_response.following(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = await response.parse()
            assert_matches_type(RawUserFollowingResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_following(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_users.with_raw_response.following(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_owns(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.owns(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserOwnsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_owns_with_all_params(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.owns(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserOwnsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_owns(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_users.with_raw_response.owns(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = await response.parse()
        assert_matches_type(RawUserOwnsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_owns(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_users.with_streaming_response.owns(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = await response.parse()
            assert_matches_type(RawUserOwnsResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_owns(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_users.with_raw_response.owns(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_stars(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.stars(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )
        assert_matches_type(RawUserStarsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_stars_with_all_params(self, async_client: AsyncBountylab) -> None:
        raw_user = await async_client.raw_users.stars(
            id="MDQ6VXNlcjU4MzIzMQ==",
            limit="100",
            offset="0",
        )
        assert_matches_type(RawUserStarsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_stars(self, async_client: AsyncBountylab) -> None:
        response = await async_client.raw_users.with_raw_response.stars(
            id="MDQ6VXNlcjU4MzIzMQ==",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        raw_user = await response.parse()
        assert_matches_type(RawUserStarsResponse, raw_user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_stars(self, async_client: AsyncBountylab) -> None:
        async with async_client.raw_users.with_streaming_response.stars(
            id="MDQ6VXNlcjU4MzIzMQ==",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            raw_user = await response.parse()
            assert_matches_type(RawUserStarsResponse, raw_user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_stars(self, async_client: AsyncBountylab) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.raw_users.with_raw_response.stars(
                id="",
            )
