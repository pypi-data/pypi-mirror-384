# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Mapping, cast
from typing_extensions import Literal

import httpx

from ..types import (
    OrderEnum,
    VideoSize,
    VideoModel,
    VideoSeconds,
    video_list_params,
    video_remix_params,
    video_create_params,
    video_retrieve_content_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, FileTypes, omit, not_given
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
from ..types.order_enum import OrderEnum
from ..types.video_size import VideoSize
from ..types.video_model import VideoModel
from ..types.video_seconds import VideoSeconds
from ..types.video_resource import VideoResource
from ..types.video_list_response import VideoListResponse
from ..types.video_delete_response import VideoDeleteResponse

__all__ = ["VideosResource", "AsyncVideosResource"]


class VideosResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> VideosResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return VideosResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> VideosResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return VideosResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        prompt: str,
        input_reference: FileTypes | Omit = omit,
        model: VideoModel | Omit = omit,
        seconds: VideoSeconds | Omit = omit,
        size: VideoSize | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoResource:
        """
        Create a video

        Args:
          prompt: Text prompt that describes the video to generate.

          input_reference: Optional image reference that guides generation.

          model: The video generation model to use. Defaults to `sora-2`.

          seconds: Clip duration in seconds. Defaults to 4 seconds.

          size: Output resolution formatted as width x height. Defaults to 720x1280.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "prompt": prompt,
                "input_reference": input_reference,
                "model": model,
                "seconds": seconds,
                "size": size,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["input_reference"]])
        if files:
            # It should be noted that the actual Content-Type header that will be
            # sent to the server will contain a `boundary` parameter, e.g.
            # multipart/form-data; boundary=---abc--
            extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            "/videos",
            body=maybe_transform(body, video_create_params.VideoCreateParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VideoResource,
        )

    def retrieve(
        self,
        video_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoResource:
        """
        Retrieve a video

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not video_id:
            raise ValueError(f"Expected a non-empty value for `video_id` but received {video_id!r}")
        return self._get(
            f"/videos/{video_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VideoResource,
        )

    def list(
        self,
        *,
        after: str | Omit = omit,
        limit: int | Omit = omit,
        order: OrderEnum | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoListResponse:
        """
        List videos

        Args:
          after: Identifier for the last item from the previous pagination request

          limit: Number of items to retrieve

          order: Sort order of results by timestamp. Use `asc` for ascending order or `desc` for
              descending order.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/videos",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                        "order": order,
                    },
                    video_list_params.VideoListParams,
                ),
            ),
            cast_to=VideoListResponse,
        )

    def delete(
        self,
        video_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoDeleteResponse:
        """
        Delete a video

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not video_id:
            raise ValueError(f"Expected a non-empty value for `video_id` but received {video_id!r}")
        return self._delete(
            f"/videos/{video_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VideoDeleteResponse,
        )

    def remix(
        self,
        video_id: str,
        *,
        prompt: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoResource:
        """
        Create a video remix

        Args:
          prompt: Updated text prompt that directs the remix generation.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not video_id:
            raise ValueError(f"Expected a non-empty value for `video_id` but received {video_id!r}")
        return self._post(
            f"/videos/{video_id}/remix",
            body=maybe_transform({"prompt": prompt}, video_remix_params.VideoRemixParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VideoResource,
        )

    def retrieve_content(
        self,
        video_id: str,
        *,
        variant: Literal["video", "thumbnail", "spritesheet"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> str:
        """Download video content

        Args:
          variant: Which downloadable asset to return.

        Defaults to the MP4 video.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not video_id:
            raise ValueError(f"Expected a non-empty value for `video_id` but received {video_id!r}")
        return self._get(
            f"/videos/{video_id}/content",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"variant": variant}, video_retrieve_content_params.VideoRetrieveContentParams),
            ),
            cast_to=str,
        )


class AsyncVideosResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncVideosResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AsyncVideosResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncVideosResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AsyncVideosResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        prompt: str,
        input_reference: FileTypes | Omit = omit,
        model: VideoModel | Omit = omit,
        seconds: VideoSeconds | Omit = omit,
        size: VideoSize | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoResource:
        """
        Create a video

        Args:
          prompt: Text prompt that describes the video to generate.

          input_reference: Optional image reference that guides generation.

          model: The video generation model to use. Defaults to `sora-2`.

          seconds: Clip duration in seconds. Defaults to 4 seconds.

          size: Output resolution formatted as width x height. Defaults to 720x1280.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal(
            {
                "prompt": prompt,
                "input_reference": input_reference,
                "model": model,
                "seconds": seconds,
                "size": size,
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["input_reference"]])
        if files:
            # It should be noted that the actual Content-Type header that will be
            # sent to the server will contain a `boundary` parameter, e.g.
            # multipart/form-data; boundary=---abc--
            extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            "/videos",
            body=await async_maybe_transform(body, video_create_params.VideoCreateParams),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VideoResource,
        )

    async def retrieve(
        self,
        video_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoResource:
        """
        Retrieve a video

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not video_id:
            raise ValueError(f"Expected a non-empty value for `video_id` but received {video_id!r}")
        return await self._get(
            f"/videos/{video_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VideoResource,
        )

    async def list(
        self,
        *,
        after: str | Omit = omit,
        limit: int | Omit = omit,
        order: OrderEnum | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoListResponse:
        """
        List videos

        Args:
          after: Identifier for the last item from the previous pagination request

          limit: Number of items to retrieve

          order: Sort order of results by timestamp. Use `asc` for ascending order or `desc` for
              descending order.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/videos",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                        "order": order,
                    },
                    video_list_params.VideoListParams,
                ),
            ),
            cast_to=VideoListResponse,
        )

    async def delete(
        self,
        video_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoDeleteResponse:
        """
        Delete a video

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not video_id:
            raise ValueError(f"Expected a non-empty value for `video_id` but received {video_id!r}")
        return await self._delete(
            f"/videos/{video_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VideoDeleteResponse,
        )

    async def remix(
        self,
        video_id: str,
        *,
        prompt: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VideoResource:
        """
        Create a video remix

        Args:
          prompt: Updated text prompt that directs the remix generation.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not video_id:
            raise ValueError(f"Expected a non-empty value for `video_id` but received {video_id!r}")
        return await self._post(
            f"/videos/{video_id}/remix",
            body=await async_maybe_transform({"prompt": prompt}, video_remix_params.VideoRemixParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VideoResource,
        )

    async def retrieve_content(
        self,
        video_id: str,
        *,
        variant: Literal["video", "thumbnail", "spritesheet"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> str:
        """Download video content

        Args:
          variant: Which downloadable asset to return.

        Defaults to the MP4 video.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not video_id:
            raise ValueError(f"Expected a non-empty value for `video_id` but received {video_id!r}")
        return await self._get(
            f"/videos/{video_id}/content",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"variant": variant}, video_retrieve_content_params.VideoRetrieveContentParams
                ),
            ),
            cast_to=str,
        )


class VideosResourceWithRawResponse:
    def __init__(self, videos: VideosResource) -> None:
        self._videos = videos

        self.create = to_raw_response_wrapper(
            videos.create,
        )
        self.retrieve = to_raw_response_wrapper(
            videos.retrieve,
        )
        self.list = to_raw_response_wrapper(
            videos.list,
        )
        self.delete = to_raw_response_wrapper(
            videos.delete,
        )
        self.remix = to_raw_response_wrapper(
            videos.remix,
        )
        self.retrieve_content = to_raw_response_wrapper(
            videos.retrieve_content,
        )


class AsyncVideosResourceWithRawResponse:
    def __init__(self, videos: AsyncVideosResource) -> None:
        self._videos = videos

        self.create = async_to_raw_response_wrapper(
            videos.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            videos.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            videos.list,
        )
        self.delete = async_to_raw_response_wrapper(
            videos.delete,
        )
        self.remix = async_to_raw_response_wrapper(
            videos.remix,
        )
        self.retrieve_content = async_to_raw_response_wrapper(
            videos.retrieve_content,
        )


class VideosResourceWithStreamingResponse:
    def __init__(self, videos: VideosResource) -> None:
        self._videos = videos

        self.create = to_streamed_response_wrapper(
            videos.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            videos.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            videos.list,
        )
        self.delete = to_streamed_response_wrapper(
            videos.delete,
        )
        self.remix = to_streamed_response_wrapper(
            videos.remix,
        )
        self.retrieve_content = to_streamed_response_wrapper(
            videos.retrieve_content,
        )


class AsyncVideosResourceWithStreamingResponse:
    def __init__(self, videos: AsyncVideosResource) -> None:
        self._videos = videos

        self.create = async_to_streamed_response_wrapper(
            videos.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            videos.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            videos.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            videos.delete,
        )
        self.remix = async_to_streamed_response_wrapper(
            videos.remix,
        )
        self.retrieve_content = async_to_streamed_response_wrapper(
            videos.retrieve_content,
        )
