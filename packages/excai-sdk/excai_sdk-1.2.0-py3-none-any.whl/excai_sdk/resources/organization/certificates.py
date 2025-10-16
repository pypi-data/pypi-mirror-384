# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.organization import (
    certificate_list_params,
    certificate_update_params,
    certificate_upload_params,
    certificate_activate_params,
    certificate_retrieve_params,
    certificate_deactivate_params,
)
from ...types.organization.certificate import Certificate
from ...types.organization.list_certificates import ListCertificates
from ...types.organization.certificate_delete_response import CertificateDeleteResponse

__all__ = ["CertificatesResource", "AsyncCertificatesResource"]


class CertificatesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CertificatesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return CertificatesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CertificatesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return CertificatesResourceWithStreamingResponse(self)

    def retrieve(
        self,
        certificate_id: str,
        *,
        include: List[Literal["content"]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Certificate:
        """
        Get a certificate that has been uploaded to the organization.

        You can get a certificate regardless of whether it is active or not.

        Args:
          include: A list of additional fields to include in the response. Currently the only
              supported value is `content` to fetch the PEM content of the certificate.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not certificate_id:
            raise ValueError(f"Expected a non-empty value for `certificate_id` but received {certificate_id!r}")
        return self._get(
            f"/organization/certificates/{certificate_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"include": include}, certificate_retrieve_params.CertificateRetrieveParams),
            ),
            cast_to=Certificate,
        )

    def update(
        self,
        certificate_id: str,
        *,
        name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Certificate:
        """Modify a certificate.

        Note that only the name can be modified.

        Args:
          name: The updated name for the certificate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not certificate_id:
            raise ValueError(f"Expected a non-empty value for `certificate_id` but received {certificate_id!r}")
        return self._post(
            f"/organization/certificates/{certificate_id}",
            body=maybe_transform({"name": name}, certificate_update_params.CertificateUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Certificate,
        )

    def list(
        self,
        *,
        after: str | Omit = omit,
        limit: int | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ListCertificates:
        """
        List uploaded certificates for this organization.

        Args:
          after: A cursor for use in pagination. `after` is an object ID that defines your place
              in the list. For instance, if you make a list request and receive 100 objects,
              ending with obj_foo, your subsequent call can include after=obj_foo in order to
              fetch the next page of the list.

          limit: A limit on the number of objects to be returned. Limit can range between 1 and
              100, and the default is 20.

          order: Sort order by the `created_at` timestamp of the objects. `asc` for ascending
              order and `desc` for descending order.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/organization/certificates",
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
                    certificate_list_params.CertificateListParams,
                ),
            ),
            cast_to=ListCertificates,
        )

    def delete(
        self,
        certificate_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CertificateDeleteResponse:
        """
        Delete a certificate from the organization.

        The certificate must be inactive for the organization and all projects.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not certificate_id:
            raise ValueError(f"Expected a non-empty value for `certificate_id` but received {certificate_id!r}")
        return self._delete(
            f"/organization/certificates/{certificate_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CertificateDeleteResponse,
        )

    def activate(
        self,
        *,
        certificate_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ListCertificates:
        """
        Activate certificates at the organization level.

        You can atomically and idempotently activate up to 10 certificates at a time.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/organization/certificates/activate",
            body=maybe_transform(
                {"certificate_ids": certificate_ids}, certificate_activate_params.CertificateActivateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListCertificates,
        )

    def deactivate(
        self,
        *,
        certificate_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ListCertificates:
        """
        Deactivate certificates at the organization level.

        You can atomically and idempotently deactivate up to 10 certificates at a time.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/organization/certificates/deactivate",
            body=maybe_transform(
                {"certificate_ids": certificate_ids}, certificate_deactivate_params.CertificateDeactivateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListCertificates,
        )

    def upload(
        self,
        *,
        content: str,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Certificate:
        """Upload a certificate to the organization.

        This does **not** automatically
        activate the certificate.

        Organizations can upload up to 50 certificates.

        Args:
          content: The certificate content in PEM format

          name: An optional name for the certificate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/organization/certificates",
            body=maybe_transform(
                {
                    "content": content,
                    "name": name,
                },
                certificate_upload_params.CertificateUploadParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Certificate,
        )


class AsyncCertificatesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCertificatesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCertificatesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCertificatesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AsyncCertificatesResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        certificate_id: str,
        *,
        include: List[Literal["content"]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Certificate:
        """
        Get a certificate that has been uploaded to the organization.

        You can get a certificate regardless of whether it is active or not.

        Args:
          include: A list of additional fields to include in the response. Currently the only
              supported value is `content` to fetch the PEM content of the certificate.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not certificate_id:
            raise ValueError(f"Expected a non-empty value for `certificate_id` but received {certificate_id!r}")
        return await self._get(
            f"/organization/certificates/{certificate_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"include": include}, certificate_retrieve_params.CertificateRetrieveParams
                ),
            ),
            cast_to=Certificate,
        )

    async def update(
        self,
        certificate_id: str,
        *,
        name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Certificate:
        """Modify a certificate.

        Note that only the name can be modified.

        Args:
          name: The updated name for the certificate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not certificate_id:
            raise ValueError(f"Expected a non-empty value for `certificate_id` but received {certificate_id!r}")
        return await self._post(
            f"/organization/certificates/{certificate_id}",
            body=await async_maybe_transform({"name": name}, certificate_update_params.CertificateUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Certificate,
        )

    async def list(
        self,
        *,
        after: str | Omit = omit,
        limit: int | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ListCertificates:
        """
        List uploaded certificates for this organization.

        Args:
          after: A cursor for use in pagination. `after` is an object ID that defines your place
              in the list. For instance, if you make a list request and receive 100 objects,
              ending with obj_foo, your subsequent call can include after=obj_foo in order to
              fetch the next page of the list.

          limit: A limit on the number of objects to be returned. Limit can range between 1 and
              100, and the default is 20.

          order: Sort order by the `created_at` timestamp of the objects. `asc` for ascending
              order and `desc` for descending order.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/organization/certificates",
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
                    certificate_list_params.CertificateListParams,
                ),
            ),
            cast_to=ListCertificates,
        )

    async def delete(
        self,
        certificate_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CertificateDeleteResponse:
        """
        Delete a certificate from the organization.

        The certificate must be inactive for the organization and all projects.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not certificate_id:
            raise ValueError(f"Expected a non-empty value for `certificate_id` but received {certificate_id!r}")
        return await self._delete(
            f"/organization/certificates/{certificate_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CertificateDeleteResponse,
        )

    async def activate(
        self,
        *,
        certificate_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ListCertificates:
        """
        Activate certificates at the organization level.

        You can atomically and idempotently activate up to 10 certificates at a time.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/organization/certificates/activate",
            body=await async_maybe_transform(
                {"certificate_ids": certificate_ids}, certificate_activate_params.CertificateActivateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListCertificates,
        )

    async def deactivate(
        self,
        *,
        certificate_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ListCertificates:
        """
        Deactivate certificates at the organization level.

        You can atomically and idempotently deactivate up to 10 certificates at a time.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/organization/certificates/deactivate",
            body=await async_maybe_transform(
                {"certificate_ids": certificate_ids}, certificate_deactivate_params.CertificateDeactivateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListCertificates,
        )

    async def upload(
        self,
        *,
        content: str,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Certificate:
        """Upload a certificate to the organization.

        This does **not** automatically
        activate the certificate.

        Organizations can upload up to 50 certificates.

        Args:
          content: The certificate content in PEM format

          name: An optional name for the certificate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/organization/certificates",
            body=await async_maybe_transform(
                {
                    "content": content,
                    "name": name,
                },
                certificate_upload_params.CertificateUploadParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Certificate,
        )


class CertificatesResourceWithRawResponse:
    def __init__(self, certificates: CertificatesResource) -> None:
        self._certificates = certificates

        self.retrieve = to_raw_response_wrapper(
            certificates.retrieve,
        )
        self.update = to_raw_response_wrapper(
            certificates.update,
        )
        self.list = to_raw_response_wrapper(
            certificates.list,
        )
        self.delete = to_raw_response_wrapper(
            certificates.delete,
        )
        self.activate = to_raw_response_wrapper(
            certificates.activate,
        )
        self.deactivate = to_raw_response_wrapper(
            certificates.deactivate,
        )
        self.upload = to_raw_response_wrapper(
            certificates.upload,
        )


class AsyncCertificatesResourceWithRawResponse:
    def __init__(self, certificates: AsyncCertificatesResource) -> None:
        self._certificates = certificates

        self.retrieve = async_to_raw_response_wrapper(
            certificates.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            certificates.update,
        )
        self.list = async_to_raw_response_wrapper(
            certificates.list,
        )
        self.delete = async_to_raw_response_wrapper(
            certificates.delete,
        )
        self.activate = async_to_raw_response_wrapper(
            certificates.activate,
        )
        self.deactivate = async_to_raw_response_wrapper(
            certificates.deactivate,
        )
        self.upload = async_to_raw_response_wrapper(
            certificates.upload,
        )


class CertificatesResourceWithStreamingResponse:
    def __init__(self, certificates: CertificatesResource) -> None:
        self._certificates = certificates

        self.retrieve = to_streamed_response_wrapper(
            certificates.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            certificates.update,
        )
        self.list = to_streamed_response_wrapper(
            certificates.list,
        )
        self.delete = to_streamed_response_wrapper(
            certificates.delete,
        )
        self.activate = to_streamed_response_wrapper(
            certificates.activate,
        )
        self.deactivate = to_streamed_response_wrapper(
            certificates.deactivate,
        )
        self.upload = to_streamed_response_wrapper(
            certificates.upload,
        )


class AsyncCertificatesResourceWithStreamingResponse:
    def __init__(self, certificates: AsyncCertificatesResource) -> None:
        self._certificates = certificates

        self.retrieve = async_to_streamed_response_wrapper(
            certificates.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            certificates.update,
        )
        self.list = async_to_streamed_response_wrapper(
            certificates.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            certificates.delete,
        )
        self.activate = async_to_streamed_response_wrapper(
            certificates.activate,
        )
        self.deactivate = async_to_streamed_response_wrapper(
            certificates.deactivate,
        )
        self.upload = async_to_streamed_response_wrapper(
            certificates.upload,
        )
