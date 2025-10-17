# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import (
    raw_user_owns_params,
    raw_user_stars_params,
    raw_user_by_login_params,
    raw_user_followers_params,
    raw_user_following_params,
    raw_user_contributes_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
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
from ..types.raw_user_owns_response import RawUserOwnsResponse
from ..types.raw_user_stars_response import RawUserStarsResponse
from ..types.raw_user_by_login_response import RawUserByLoginResponse
from ..types.raw_user_retrieve_response import RawUserRetrieveResponse
from ..types.raw_user_followers_response import RawUserFollowersResponse
from ..types.raw_user_following_response import RawUserFollowingResponse
from ..types.raw_user_contributes_response import RawUserContributesResponse

__all__ = ["RawUsersResource", "AsyncRawUsersResource"]


class RawUsersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RawUsersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#accessing-raw-response-data-eg-headers
        """
        return RawUsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RawUsersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#with_streaming_response
        """
        return RawUsersResourceWithStreamingResponse(self)

    def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserRetrieveResponse:
        """Fetch a single GitHub user by their node ID.

        Requires RAW service. Credits: 1
        per result.

        Args:
          id: GitHub node ID (used to look up the user)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/api/raw/users/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RawUserRetrieveResponse,
        )

    def by_login(
        self,
        *,
        logins: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserByLoginResponse:
        """Fetch GitHub users by their usernames (login).

        Supports batch requests (1-100
        logins). Requires RAW service. Credits: 1 per result returned.

        Args:
          logins: Array of GitHub usernames (1-100)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/raw/users/by-login",
            body=maybe_transform({"logins": logins}, raw_user_by_login_params.RawUserByLoginParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RawUserByLoginResponse,
        )

    def contributes(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserContributesResponse:
        """
        Get repositories this user contributes to (outgoing "contributes" edges).
        Supports pagination. Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/api/raw/users/{id}/contributes",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_contributes_params.RawUserContributesParams,
                ),
            ),
            cast_to=RawUserContributesResponse,
        )

    def followers(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserFollowersResponse:
        """Get users who follow this user (incoming "follows" edges).

        Supports pagination.
        Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/api/raw/users/{id}/followers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_followers_params.RawUserFollowersParams,
                ),
            ),
            cast_to=RawUserFollowersResponse,
        )

    def following(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserFollowingResponse:
        """Get users this user follows (outgoing "follows" edges).

        Supports pagination.
        Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/api/raw/users/{id}/following",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_following_params.RawUserFollowingParams,
                ),
            ),
            cast_to=RawUserFollowingResponse,
        )

    def owns(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserOwnsResponse:
        """Get repositories owned by this user (outgoing "owns" edges).

        Supports
        pagination. Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/api/raw/users/{id}/owns",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_owns_params.RawUserOwnsParams,
                ),
            ),
            cast_to=RawUserOwnsResponse,
        )

    def stars(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserStarsResponse:
        """Get repositories starred by this user (outgoing "stars" edges).

        Supports
        pagination. Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/api/raw/users/{id}/stars",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_stars_params.RawUserStarsParams,
                ),
            ),
            cast_to=RawUserStarsResponse,
        )


class AsyncRawUsersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRawUsersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncRawUsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRawUsersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#with_streaming_response
        """
        return AsyncRawUsersResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserRetrieveResponse:
        """Fetch a single GitHub user by their node ID.

        Requires RAW service. Credits: 1
        per result.

        Args:
          id: GitHub node ID (used to look up the user)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/api/raw/users/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RawUserRetrieveResponse,
        )

    async def by_login(
        self,
        *,
        logins: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserByLoginResponse:
        """Fetch GitHub users by their usernames (login).

        Supports batch requests (1-100
        logins). Requires RAW service. Credits: 1 per result returned.

        Args:
          logins: Array of GitHub usernames (1-100)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/raw/users/by-login",
            body=await async_maybe_transform({"logins": logins}, raw_user_by_login_params.RawUserByLoginParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RawUserByLoginResponse,
        )

    async def contributes(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserContributesResponse:
        """
        Get repositories this user contributes to (outgoing "contributes" edges).
        Supports pagination. Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/api/raw/users/{id}/contributes",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_contributes_params.RawUserContributesParams,
                ),
            ),
            cast_to=RawUserContributesResponse,
        )

    async def followers(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserFollowersResponse:
        """Get users who follow this user (incoming "follows" edges).

        Supports pagination.
        Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/api/raw/users/{id}/followers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_followers_params.RawUserFollowersParams,
                ),
            ),
            cast_to=RawUserFollowersResponse,
        )

    async def following(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserFollowingResponse:
        """Get users this user follows (outgoing "follows" edges).

        Supports pagination.
        Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/api/raw/users/{id}/following",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_following_params.RawUserFollowingParams,
                ),
            ),
            cast_to=RawUserFollowingResponse,
        )

    async def owns(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserOwnsResponse:
        """Get repositories owned by this user (outgoing "owns" edges).

        Supports
        pagination. Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/api/raw/users/{id}/owns",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_owns_params.RawUserOwnsParams,
                ),
            ),
            cast_to=RawUserOwnsResponse,
        )

    async def stars(
        self,
        id: str,
        *,
        limit: str | Omit = omit,
        offset: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RawUserStarsResponse:
        """Get repositories starred by this user (outgoing "stars" edges).

        Supports
        pagination. Requires RAW service. Credits: 1 per result.

        Args:
          id: GitHub node ID (used to look up the user)

          limit: Maximum number of results to return (default: 100, max: 1000)

          offset: Number of results to skip (default: 0)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/api/raw/users/{id}/stars",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    raw_user_stars_params.RawUserStarsParams,
                ),
            ),
            cast_to=RawUserStarsResponse,
        )


class RawUsersResourceWithRawResponse:
    def __init__(self, raw_users: RawUsersResource) -> None:
        self._raw_users = raw_users

        self.retrieve = to_raw_response_wrapper(
            raw_users.retrieve,
        )
        self.by_login = to_raw_response_wrapper(
            raw_users.by_login,
        )
        self.contributes = to_raw_response_wrapper(
            raw_users.contributes,
        )
        self.followers = to_raw_response_wrapper(
            raw_users.followers,
        )
        self.following = to_raw_response_wrapper(
            raw_users.following,
        )
        self.owns = to_raw_response_wrapper(
            raw_users.owns,
        )
        self.stars = to_raw_response_wrapper(
            raw_users.stars,
        )


class AsyncRawUsersResourceWithRawResponse:
    def __init__(self, raw_users: AsyncRawUsersResource) -> None:
        self._raw_users = raw_users

        self.retrieve = async_to_raw_response_wrapper(
            raw_users.retrieve,
        )
        self.by_login = async_to_raw_response_wrapper(
            raw_users.by_login,
        )
        self.contributes = async_to_raw_response_wrapper(
            raw_users.contributes,
        )
        self.followers = async_to_raw_response_wrapper(
            raw_users.followers,
        )
        self.following = async_to_raw_response_wrapper(
            raw_users.following,
        )
        self.owns = async_to_raw_response_wrapper(
            raw_users.owns,
        )
        self.stars = async_to_raw_response_wrapper(
            raw_users.stars,
        )


class RawUsersResourceWithStreamingResponse:
    def __init__(self, raw_users: RawUsersResource) -> None:
        self._raw_users = raw_users

        self.retrieve = to_streamed_response_wrapper(
            raw_users.retrieve,
        )
        self.by_login = to_streamed_response_wrapper(
            raw_users.by_login,
        )
        self.contributes = to_streamed_response_wrapper(
            raw_users.contributes,
        )
        self.followers = to_streamed_response_wrapper(
            raw_users.followers,
        )
        self.following = to_streamed_response_wrapper(
            raw_users.following,
        )
        self.owns = to_streamed_response_wrapper(
            raw_users.owns,
        )
        self.stars = to_streamed_response_wrapper(
            raw_users.stars,
        )


class AsyncRawUsersResourceWithStreamingResponse:
    def __init__(self, raw_users: AsyncRawUsersResource) -> None:
        self._raw_users = raw_users

        self.retrieve = async_to_streamed_response_wrapper(
            raw_users.retrieve,
        )
        self.by_login = async_to_streamed_response_wrapper(
            raw_users.by_login,
        )
        self.contributes = async_to_streamed_response_wrapper(
            raw_users.contributes,
        )
        self.followers = async_to_streamed_response_wrapper(
            raw_users.followers,
        )
        self.following = async_to_streamed_response_wrapper(
            raw_users.following,
        )
        self.owns = async_to_streamed_response_wrapper(
            raw_users.owns,
        )
        self.stars = async_to_streamed_response_wrapper(
            raw_users.stars,
        )
