# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import search_repo_search_params, search_repo_natural_language_params
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
from ..types.search_repo_search_response import SearchRepoSearchResponse
from ..types.search_repo_natural_language_response import SearchRepoNaturalLanguageResponse

__all__ = ["SearchReposResource", "AsyncSearchReposResource"]


class SearchReposResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SearchReposResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#accessing-raw-response-data-eg-headers
        """
        return SearchReposResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SearchReposResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#with_streaming_response
        """
        return SearchReposResourceWithStreamingResponse(self)

    def natural_language(
        self,
        *,
        query: str,
        include_attributes: search_repo_natural_language_params.IncludeAttributes | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchRepoNaturalLanguageResponse:
        """
        Natural language search that uses AI to understand your query and automatically
        generate search terms and filters. Requires SEARCH service. Credits: 1 per
        result returned + 1 for AI processing + graph relationship credits if
        includeAttributes is specified.

        Args:
          query: Natural language query describing the repositories you want to find

          include_attributes: Optional graph relationships to include (owner, contributors, starrers)

          max_results: Maximum number of results to return (default: 100, max: 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/search/repos/natural-language",
            body=maybe_transform(
                {
                    "query": query,
                    "include_attributes": include_attributes,
                    "max_results": max_results,
                },
                search_repo_natural_language_params.SearchRepoNaturalLanguageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchRepoNaturalLanguageResponse,
        )

    def search(
        self,
        *,
        query: str,
        filters: Optional[search_repo_search_params.Filters] | Omit = omit,
        include_attributes: search_repo_search_params.IncludeAttributes | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchRepoSearchResponse:
        """
        Semantic search across repository READMEs and descriptions using vector
        embeddings and cosine similarity. Results include relevance scores. Requires
        SEARCH service. Credits: 1 per result returned.

        Args:
          query: Natural language search query for semantic search across repository README and
              description using vector embeddings

          filters: Optional filters for narrowing search results. Supports filtering on: githubId,
              ownerLogin, name, stargazerCount, language, totalIssuesCount, totalIssuesOpen,
              totalIssuesClosed, lastContributorLocations.

              Filter structure:

              - Field filters: { field: "fieldName", op: "Eq"|"In"|"Gte"|"Lte", value:
                string|number|array }
              - Composite filters: { op: "And"|"Or", filters: [...] }

              Supported operators:

              - String fields: Eq (exact match), In (one of array)
              - Number fields: Eq (exact), In (one of array), Gte (>=), Lte (<=)
              - Use And/Or to combine multiple filters

          include_attributes: Optional graph relationships to include (owner, contributors, starrers)

          max_results: Maximum number of results to return (default: 100, max: 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/search/repos",
            body=maybe_transform(
                {
                    "query": query,
                    "filters": filters,
                    "include_attributes": include_attributes,
                    "max_results": max_results,
                },
                search_repo_search_params.SearchRepoSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchRepoSearchResponse,
        )


class AsyncSearchReposResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSearchReposResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSearchReposResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSearchReposResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#with_streaming_response
        """
        return AsyncSearchReposResourceWithStreamingResponse(self)

    async def natural_language(
        self,
        *,
        query: str,
        include_attributes: search_repo_natural_language_params.IncludeAttributes | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchRepoNaturalLanguageResponse:
        """
        Natural language search that uses AI to understand your query and automatically
        generate search terms and filters. Requires SEARCH service. Credits: 1 per
        result returned + 1 for AI processing + graph relationship credits if
        includeAttributes is specified.

        Args:
          query: Natural language query describing the repositories you want to find

          include_attributes: Optional graph relationships to include (owner, contributors, starrers)

          max_results: Maximum number of results to return (default: 100, max: 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/search/repos/natural-language",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "include_attributes": include_attributes,
                    "max_results": max_results,
                },
                search_repo_natural_language_params.SearchRepoNaturalLanguageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchRepoNaturalLanguageResponse,
        )

    async def search(
        self,
        *,
        query: str,
        filters: Optional[search_repo_search_params.Filters] | Omit = omit,
        include_attributes: search_repo_search_params.IncludeAttributes | Omit = omit,
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchRepoSearchResponse:
        """
        Semantic search across repository READMEs and descriptions using vector
        embeddings and cosine similarity. Results include relevance scores. Requires
        SEARCH service. Credits: 1 per result returned.

        Args:
          query: Natural language search query for semantic search across repository README and
              description using vector embeddings

          filters: Optional filters for narrowing search results. Supports filtering on: githubId,
              ownerLogin, name, stargazerCount, language, totalIssuesCount, totalIssuesOpen,
              totalIssuesClosed, lastContributorLocations.

              Filter structure:

              - Field filters: { field: "fieldName", op: "Eq"|"In"|"Gte"|"Lte", value:
                string|number|array }
              - Composite filters: { op: "And"|"Or", filters: [...] }

              Supported operators:

              - String fields: Eq (exact match), In (one of array)
              - Number fields: Eq (exact), In (one of array), Gte (>=), Lte (<=)
              - Use And/Or to combine multiple filters

          include_attributes: Optional graph relationships to include (owner, contributors, starrers)

          max_results: Maximum number of results to return (default: 100, max: 1000)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/search/repos",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "filters": filters,
                    "include_attributes": include_attributes,
                    "max_results": max_results,
                },
                search_repo_search_params.SearchRepoSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchRepoSearchResponse,
        )


class SearchReposResourceWithRawResponse:
    def __init__(self, search_repos: SearchReposResource) -> None:
        self._search_repos = search_repos

        self.natural_language = to_raw_response_wrapper(
            search_repos.natural_language,
        )
        self.search = to_raw_response_wrapper(
            search_repos.search,
        )


class AsyncSearchReposResourceWithRawResponse:
    def __init__(self, search_repos: AsyncSearchReposResource) -> None:
        self._search_repos = search_repos

        self.natural_language = async_to_raw_response_wrapper(
            search_repos.natural_language,
        )
        self.search = async_to_raw_response_wrapper(
            search_repos.search,
        )


class SearchReposResourceWithStreamingResponse:
    def __init__(self, search_repos: SearchReposResource) -> None:
        self._search_repos = search_repos

        self.natural_language = to_streamed_response_wrapper(
            search_repos.natural_language,
        )
        self.search = to_streamed_response_wrapper(
            search_repos.search,
        )


class AsyncSearchReposResourceWithStreamingResponse:
    def __init__(self, search_repos: AsyncSearchReposResource) -> None:
        self._search_repos = search_repos

        self.natural_language = async_to_streamed_response_wrapper(
            search_repos.natural_language,
        )
        self.search = async_to_streamed_response_wrapper(
            search_repos.search,
        )
