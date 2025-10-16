# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .graders import (
    GradersResource,
    AsyncGradersResource,
    GradersResourceWithRawResponse,
    AsyncGradersResourceWithRawResponse,
    GradersResourceWithStreamingResponse,
    AsyncGradersResourceWithStreamingResponse,
)
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["AlphaResource", "AsyncAlphaResource"]


class AlphaResource(SyncAPIResource):
    @cached_property
    def graders(self) -> GradersResource:
        return GradersResource(self._client)

    @cached_property
    def with_raw_response(self) -> AlphaResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AlphaResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AlphaResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AlphaResourceWithStreamingResponse(self)


class AsyncAlphaResource(AsyncAPIResource):
    @cached_property
    def graders(self) -> AsyncGradersResource:
        return AsyncGradersResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncAlphaResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAlphaResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAlphaResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AsyncAlphaResourceWithStreamingResponse(self)


class AlphaResourceWithRawResponse:
    def __init__(self, alpha: AlphaResource) -> None:
        self._alpha = alpha

    @cached_property
    def graders(self) -> GradersResourceWithRawResponse:
        return GradersResourceWithRawResponse(self._alpha.graders)


class AsyncAlphaResourceWithRawResponse:
    def __init__(self, alpha: AsyncAlphaResource) -> None:
        self._alpha = alpha

    @cached_property
    def graders(self) -> AsyncGradersResourceWithRawResponse:
        return AsyncGradersResourceWithRawResponse(self._alpha.graders)


class AlphaResourceWithStreamingResponse:
    def __init__(self, alpha: AlphaResource) -> None:
        self._alpha = alpha

    @cached_property
    def graders(self) -> GradersResourceWithStreamingResponse:
        return GradersResourceWithStreamingResponse(self._alpha.graders)


class AsyncAlphaResourceWithStreamingResponse:
    def __init__(self, alpha: AsyncAlphaResource) -> None:
        self._alpha = alpha

    @cached_property
    def graders(self) -> AsyncGradersResourceWithStreamingResponse:
        return AsyncGradersResourceWithStreamingResponse(self._alpha.graders)
