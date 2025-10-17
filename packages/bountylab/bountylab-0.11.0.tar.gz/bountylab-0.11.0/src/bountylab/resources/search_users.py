# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import search_user_search_params, search_user_natural_language_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ..types.search_user_search_response import SearchUserSearchResponse
from ..types.search_user_natural_language_response import SearchUserNaturalLanguageResponse

__all__ = ["SearchUsersResource", "AsyncSearchUsersResource"]


class SearchUsersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SearchUsersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#accessing-raw-response-data-eg-headers
        """
        return SearchUsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SearchUsersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#with_streaming_response
        """
        return SearchUsersResourceWithStreamingResponse(self)

    def natural_language(
        self,
        *,
        query: str,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchUserNaturalLanguageResponse:
        """
        Natural language search that uses AI to understand your query and automatically
        generate search terms and filters. Requires SEARCH service. Credits: 1 per
        result returned + 1 for AI processing.

        Args:
          query: Natural language query describing the users you want to find

          max_results: Maximum number of results to return (default: 100, max: 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/search/users/natural-language",
            body=maybe_transform(
                {
                    "query": query,
                    "max_results": max_results,
                },
                search_user_natural_language_params.SearchUserNaturalLanguageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchUserNaturalLanguageResponse,
        )

    def search(
        self,
        *,
        query: str,
        filters: Optional[search_user_search_params.Filters] | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchUserSearchResponse:
        """
        Full-text search across user login, name, bio, company, and location using BM25
        ranking. Results include relevance scores. Requires SEARCH service. Credits: 1
        per result returned.

        Args:
          query: Full-text search query across user fields. Searches: login, displayName, bio,
              company, location, emails, resolvedCountry, resolvedState, resolvedCity (with
              login weighted 2x)

          filters: Optional filters for narrowing search results. Supports filtering on: githubId,
              login, displayName, bio, company, location, emails, resolvedCountry,
              resolvedState, resolvedCity.

              Full-text searchable fields (automatically searched): login, displayName, bio,
              company, location, emails, resolvedCountry, resolvedState, resolvedCity.

              Filter structure:

              - Field filters: { field: "fieldName", op: "Eq"|"In", value: string|string[] }
              - Composite filters: { op: "And"|"Or", filters: [...] }

              Supported operators:

              - String fields: Eq (exact match), In (one of array)
              - Use And/Or to combine multiple filters

          max_results: Maximum number of results to return (default: 100, max: 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/search/users",
            body=maybe_transform(
                {
                    "query": query,
                    "filters": filters,
                    "max_results": max_results,
                },
                search_user_search_params.SearchUserSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchUserSearchResponse,
        )


class AsyncSearchUsersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSearchUsersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSearchUsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSearchUsersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#with_streaming_response
        """
        return AsyncSearchUsersResourceWithStreamingResponse(self)

    async def natural_language(
        self,
        *,
        query: str,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchUserNaturalLanguageResponse:
        """
        Natural language search that uses AI to understand your query and automatically
        generate search terms and filters. Requires SEARCH service. Credits: 1 per
        result returned + 1 for AI processing.

        Args:
          query: Natural language query describing the users you want to find

          max_results: Maximum number of results to return (default: 100, max: 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/search/users/natural-language",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "max_results": max_results,
                },
                search_user_natural_language_params.SearchUserNaturalLanguageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchUserNaturalLanguageResponse,
        )

    async def search(
        self,
        *,
        query: str,
        filters: Optional[search_user_search_params.Filters] | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchUserSearchResponse:
        """
        Full-text search across user login, name, bio, company, and location using BM25
        ranking. Results include relevance scores. Requires SEARCH service. Credits: 1
        per result returned.

        Args:
          query: Full-text search query across user fields. Searches: login, displayName, bio,
              company, location, emails, resolvedCountry, resolvedState, resolvedCity (with
              login weighted 2x)

          filters: Optional filters for narrowing search results. Supports filtering on: githubId,
              login, displayName, bio, company, location, emails, resolvedCountry,
              resolvedState, resolvedCity.

              Full-text searchable fields (automatically searched): login, displayName, bio,
              company, location, emails, resolvedCountry, resolvedState, resolvedCity.

              Filter structure:

              - Field filters: { field: "fieldName", op: "Eq"|"In", value: string|string[] }
              - Composite filters: { op: "And"|"Or", filters: [...] }

              Supported operators:

              - String fields: Eq (exact match), In (one of array)
              - Use And/Or to combine multiple filters

          max_results: Maximum number of results to return (default: 100, max: 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/search/users",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "filters": filters,
                    "max_results": max_results,
                },
                search_user_search_params.SearchUserSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchUserSearchResponse,
        )


class SearchUsersResourceWithRawResponse:
    def __init__(self, search_users: SearchUsersResource) -> None:
        self._search_users = search_users

        self.natural_language = to_raw_response_wrapper(
            search_users.natural_language,
        )
        self.search = to_raw_response_wrapper(
            search_users.search,
        )


class AsyncSearchUsersResourceWithRawResponse:
    def __init__(self, search_users: AsyncSearchUsersResource) -> None:
        self._search_users = search_users

        self.natural_language = async_to_raw_response_wrapper(
            search_users.natural_language,
        )
        self.search = async_to_raw_response_wrapper(
            search_users.search,
        )


class SearchUsersResourceWithStreamingResponse:
    def __init__(self, search_users: SearchUsersResource) -> None:
        self._search_users = search_users

        self.natural_language = to_streamed_response_wrapper(
            search_users.natural_language,
        )
        self.search = to_streamed_response_wrapper(
            search_users.search,
        )


class AsyncSearchUsersResourceWithStreamingResponse:
    def __init__(self, search_users: AsyncSearchUsersResource) -> None:
        self._search_users = search_users

        self.natural_language = async_to_streamed_response_wrapper(
            search_users.natural_language,
        )
        self.search = async_to_streamed_response_wrapper(
            search_users.search,
        )
