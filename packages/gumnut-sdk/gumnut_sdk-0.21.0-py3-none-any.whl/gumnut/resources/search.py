# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import typing_extensions
from typing import Union, Mapping, Optional, cast
from datetime import datetime

import httpx

from ..types import search_search_params, search_search_assets_params
from .._types import Body, Omit, Query, Headers, NotGiven, FileTypes, SequenceNotStr, omit, not_given
from .._utils import extract_files, maybe_transform, deepcopy_minimal, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.search_response import SearchResponse

__all__ = ["SearchResource", "AsyncSearchResource"]


class SearchResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SearchResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/gumnut-ai/photos-sdk-python#accessing-raw-response-data-eg-headers
        """
        return SearchResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SearchResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/gumnut-ai/photos-sdk-python#with_streaming_response
        """
        return SearchResourceWithStreamingResponse(self)

    @typing_extensions.deprecated("deprecated")
    def search(
        self,
        *,
        captured_after: Union[str, datetime, None] | Omit = omit,
        captured_before: Union[str, datetime, None] | Omit = omit,
        library_id: Optional[str] | Omit = omit,
        limit: int | Omit = omit,
        page: int | Omit = omit,
        person_ids: Optional[SequenceNotStr[str]] | Omit = omit,
        query: Optional[str] | Omit = omit,
        threshold: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchResponse:
        """Searches for assets using semantic similarity and/or metadata filters.

        Results
        include asset metadata, faces, and people. At least one search criterion must be
        provided.

        Args:
          captured_after: Filter to only include assets captured after this date (ISO format).

          captured_before: Filter to only include assets captured before this date (ISO format).

          library_id: Library to search assets from (optional)

          limit: Number of results per page

          page: Page number

          person_ids: Filter to only include assets containing ALL of these person IDs. Can be
              comma-delimited string (e.g. 'person_123,person_abc') or multiple query
              parameters.

          query: The text query to search for. If you want to search for a specific person or set
              of people, use the person_ids parameter instead.If you want to search for a
              photos taken during a specific date range, use the captured_before and
              captured_after parameters instead.

          threshold: Similarity threshold (lower means more similar)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/api/search",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "captured_after": captured_after,
                        "captured_before": captured_before,
                        "library_id": library_id,
                        "limit": limit,
                        "page": page,
                        "person_ids": person_ids,
                        "query": query,
                        "threshold": threshold,
                    },
                    search_search_params.SearchSearchParams,
                ),
            ),
            cast_to=SearchResponse,
        )

    def search_assets(
        self,
        *,
        captured_after: Union[str, datetime, None] | Omit = omit,
        captured_before: Union[str, datetime, None] | Omit = omit,
        image: Optional[FileTypes] | Omit = omit,
        library_id: Optional[str] | Omit = omit,
        limit: int | Omit = omit,
        page: int | Omit = omit,
        person_ids: Optional[SequenceNotStr[str]] | Omit = omit,
        query: Optional[str] | Omit = omit,
        threshold: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchResponse:
        """Searches for assets using semantic similarity and/or metadata filters.

        Results
        include asset metadata, faces, and people. At least one search criterion must be
        provided. Can search by text query, uploaded image, or both combined.

        Args:
          captured_after: Filter to only include assets captured after this date (ISO format).

          captured_before: Filter to only include assets captured before this date (ISO format).

          image: Image file to search for similar assets. Can be combined with text query.

          library_id: Library to search assets from (optional)

          limit: Number of results per page

          page: Page number

          person_ids: Filter to only include assets containing ALL of these person IDs. Can be
              comma-delimited string (e.g. 'person_123,person_abc') or multiple query
              parameters.

          query: The text query to search for. If you want to search for a specific person or set
              of people, use the person_ids parameter instead.If you want to search for a
              photos taken during a specific date range, use the captured_before and
              captured_after parameters instead.

          threshold: Similarity threshold (lower means more similar)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "captured_after": captured_after,
                "captured_before": captured_before,
                "image": image,
                "library_id": library_id,
                "limit": limit,
                "page": page,
                "person_ids": person_ids,
                "query": query,
                "threshold": threshold,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["image"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            "/api/search",
            body=maybe_transform(body, search_search_assets_params.SearchSearchAssetsParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchResponse,
        )


class AsyncSearchResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSearchResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/gumnut-ai/photos-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSearchResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSearchResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/gumnut-ai/photos-sdk-python#with_streaming_response
        """
        return AsyncSearchResourceWithStreamingResponse(self)

    @typing_extensions.deprecated("deprecated")
    async def search(
        self,
        *,
        captured_after: Union[str, datetime, None] | Omit = omit,
        captured_before: Union[str, datetime, None] | Omit = omit,
        library_id: Optional[str] | Omit = omit,
        limit: int | Omit = omit,
        page: int | Omit = omit,
        person_ids: Optional[SequenceNotStr[str]] | Omit = omit,
        query: Optional[str] | Omit = omit,
        threshold: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchResponse:
        """Searches for assets using semantic similarity and/or metadata filters.

        Results
        include asset metadata, faces, and people. At least one search criterion must be
        provided.

        Args:
          captured_after: Filter to only include assets captured after this date (ISO format).

          captured_before: Filter to only include assets captured before this date (ISO format).

          library_id: Library to search assets from (optional)

          limit: Number of results per page

          page: Page number

          person_ids: Filter to only include assets containing ALL of these person IDs. Can be
              comma-delimited string (e.g. 'person_123,person_abc') or multiple query
              parameters.

          query: The text query to search for. If you want to search for a specific person or set
              of people, use the person_ids parameter instead.If you want to search for a
              photos taken during a specific date range, use the captured_before and
              captured_after parameters instead.

          threshold: Similarity threshold (lower means more similar)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/api/search",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "captured_after": captured_after,
                        "captured_before": captured_before,
                        "library_id": library_id,
                        "limit": limit,
                        "page": page,
                        "person_ids": person_ids,
                        "query": query,
                        "threshold": threshold,
                    },
                    search_search_params.SearchSearchParams,
                ),
            ),
            cast_to=SearchResponse,
        )

    async def search_assets(
        self,
        *,
        captured_after: Union[str, datetime, None] | Omit = omit,
        captured_before: Union[str, datetime, None] | Omit = omit,
        image: Optional[FileTypes] | Omit = omit,
        library_id: Optional[str] | Omit = omit,
        limit: int | Omit = omit,
        page: int | Omit = omit,
        person_ids: Optional[SequenceNotStr[str]] | Omit = omit,
        query: Optional[str] | Omit = omit,
        threshold: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchResponse:
        """Searches for assets using semantic similarity and/or metadata filters.

        Results
        include asset metadata, faces, and people. At least one search criterion must be
        provided. Can search by text query, uploaded image, or both combined.

        Args:
          captured_after: Filter to only include assets captured after this date (ISO format).

          captured_before: Filter to only include assets captured before this date (ISO format).

          image: Image file to search for similar assets. Can be combined with text query.

          library_id: Library to search assets from (optional)

          limit: Number of results per page

          page: Page number

          person_ids: Filter to only include assets containing ALL of these person IDs. Can be
              comma-delimited string (e.g. 'person_123,person_abc') or multiple query
              parameters.

          query: The text query to search for. If you want to search for a specific person or set
              of people, use the person_ids parameter instead.If you want to search for a
              photos taken during a specific date range, use the captured_before and
              captured_after parameters instead.

          threshold: Similarity threshold (lower means more similar)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "captured_after": captured_after,
                "captured_before": captured_before,
                "image": image,
                "library_id": library_id,
                "limit": limit,
                "page": page,
                "person_ids": person_ids,
                "query": query,
                "threshold": threshold,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["image"]])
        # It should be noted that the actual Content-Type header that will be
        # sent to the server will contain a `boundary` parameter, e.g.
        # multipart/form-data; boundary=---abc--
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            "/api/search",
            body=await async_maybe_transform(body, search_search_assets_params.SearchSearchAssetsParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchResponse,
        )


class SearchResourceWithRawResponse:
    def __init__(self, search: SearchResource) -> None:
        self._search = search

        self.search = (  # pyright: ignore[reportDeprecated]
            to_raw_response_wrapper(
                search.search,  # pyright: ignore[reportDeprecated],
            )
        )
        self.search_assets = to_raw_response_wrapper(
            search.search_assets,
        )


class AsyncSearchResourceWithRawResponse:
    def __init__(self, search: AsyncSearchResource) -> None:
        self._search = search

        self.search = (  # pyright: ignore[reportDeprecated]
            async_to_raw_response_wrapper(
                search.search,  # pyright: ignore[reportDeprecated],
            )
        )
        self.search_assets = async_to_raw_response_wrapper(
            search.search_assets,
        )


class SearchResourceWithStreamingResponse:
    def __init__(self, search: SearchResource) -> None:
        self._search = search

        self.search = (  # pyright: ignore[reportDeprecated]
            to_streamed_response_wrapper(
                search.search,  # pyright: ignore[reportDeprecated],
            )
        )
        self.search_assets = to_streamed_response_wrapper(
            search.search_assets,
        )


class AsyncSearchResourceWithStreamingResponse:
    def __init__(self, search: AsyncSearchResource) -> None:
        self._search = search

        self.search = (  # pyright: ignore[reportDeprecated]
            async_to_streamed_response_wrapper(
                search.search,  # pyright: ignore[reportDeprecated],
            )
        )
        self.search_assets = async_to_streamed_response_wrapper(
            search.search_assets,
        )
