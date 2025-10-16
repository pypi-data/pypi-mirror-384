# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.fine_tuning.alpha import grader_run_params, grader_validate_params
from ....types.fine_tuning.alpha.grader_run_response import GraderRunResponse
from ....types.fine_tuning.alpha.grader_validate_response import GraderValidateResponse

__all__ = ["GradersResource", "AsyncGradersResource"]


class GradersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> GradersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return GradersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GradersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return GradersResourceWithStreamingResponse(self)

    def run(
        self,
        *,
        grader: grader_run_params.Grader,
        model_sample: str,
        item: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GraderRunResponse:
        """
        Run a grader.

        Args:
          grader: The grader used for the fine-tuning job.

          model_sample: The model sample to be evaluated. This value will be used to populate the
              `sample` namespace. See [the guide](https://main.excai.ai/docs/guides/graders)
              for more details. The `output_json` variable will be populated if the model
              sample is a valid JSON string.

          item: The dataset item provided to the grader. This will be used to populate the
              `item` namespace. See [the guide](https://main.excai.ai/docs/guides/graders) for
              more details.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/fine_tuning/alpha/graders/run",
            body=maybe_transform(
                {
                    "grader": grader,
                    "model_sample": model_sample,
                    "item": item,
                },
                grader_run_params.GraderRunParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GraderRunResponse,
        )

    def validate(
        self,
        *,
        grader: grader_validate_params.Grader,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GraderValidateResponse:
        """
        Validate a grader.

        Args:
          grader: The grader used for the fine-tuning job.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/fine_tuning/alpha/graders/validate",
            body=maybe_transform({"grader": grader}, grader_validate_params.GraderValidateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GraderValidateResponse,
        )


class AsyncGradersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncGradersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AsyncGradersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGradersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AsyncGradersResourceWithStreamingResponse(self)

    async def run(
        self,
        *,
        grader: grader_run_params.Grader,
        model_sample: str,
        item: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GraderRunResponse:
        """
        Run a grader.

        Args:
          grader: The grader used for the fine-tuning job.

          model_sample: The model sample to be evaluated. This value will be used to populate the
              `sample` namespace. See [the guide](https://main.excai.ai/docs/guides/graders)
              for more details. The `output_json` variable will be populated if the model
              sample is a valid JSON string.

          item: The dataset item provided to the grader. This will be used to populate the
              `item` namespace. See [the guide](https://main.excai.ai/docs/guides/graders) for
              more details.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/fine_tuning/alpha/graders/run",
            body=await async_maybe_transform(
                {
                    "grader": grader,
                    "model_sample": model_sample,
                    "item": item,
                },
                grader_run_params.GraderRunParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GraderRunResponse,
        )

    async def validate(
        self,
        *,
        grader: grader_validate_params.Grader,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GraderValidateResponse:
        """
        Validate a grader.

        Args:
          grader: The grader used for the fine-tuning job.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/fine_tuning/alpha/graders/validate",
            body=await async_maybe_transform({"grader": grader}, grader_validate_params.GraderValidateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GraderValidateResponse,
        )


class GradersResourceWithRawResponse:
    def __init__(self, graders: GradersResource) -> None:
        self._graders = graders

        self.run = to_raw_response_wrapper(
            graders.run,
        )
        self.validate = to_raw_response_wrapper(
            graders.validate,
        )


class AsyncGradersResourceWithRawResponse:
    def __init__(self, graders: AsyncGradersResource) -> None:
        self._graders = graders

        self.run = async_to_raw_response_wrapper(
            graders.run,
        )
        self.validate = async_to_raw_response_wrapper(
            graders.validate,
        )


class GradersResourceWithStreamingResponse:
    def __init__(self, graders: GradersResource) -> None:
        self._graders = graders

        self.run = to_streamed_response_wrapper(
            graders.run,
        )
        self.validate = to_streamed_response_wrapper(
            graders.validate,
        )


class AsyncGradersResourceWithStreamingResponse:
    def __init__(self, graders: AsyncGradersResource) -> None:
        self._graders = graders

        self.run = async_to_streamed_response_wrapper(
            graders.run,
        )
        self.validate = async_to_streamed_response_wrapper(
            graders.validate,
        )
