# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types.organization import ListCertificates

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCertificates:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: ExcaiSDK) -> None:
        certificate = client.organization.projects.certificates.list(
            project_id="project_id",
        )
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: ExcaiSDK) -> None:
        certificate = client.organization.projects.certificates.list(
            project_id="project_id",
            after="after",
            limit=0,
            order="asc",
        )
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: ExcaiSDK) -> None:
        response = client.organization.projects.certificates.with_raw_response.list(
            project_id="project_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        certificate = response.parse()
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: ExcaiSDK) -> None:
        with client.organization.projects.certificates.with_streaming_response.list(
            project_id="project_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            certificate = response.parse()
            assert_matches_type(ListCertificates, certificate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.organization.projects.certificates.with_raw_response.list(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_activate(self, client: ExcaiSDK) -> None:
        certificate = client.organization.projects.certificates.activate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        )
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_activate(self, client: ExcaiSDK) -> None:
        response = client.organization.projects.certificates.with_raw_response.activate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        certificate = response.parse()
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_activate(self, client: ExcaiSDK) -> None:
        with client.organization.projects.certificates.with_streaming_response.activate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            certificate = response.parse()
            assert_matches_type(ListCertificates, certificate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_activate(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.organization.projects.certificates.with_raw_response.activate(
                project_id="",
                certificate_ids=["cert_abc"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_deactivate(self, client: ExcaiSDK) -> None:
        certificate = client.organization.projects.certificates.deactivate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        )
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_deactivate(self, client: ExcaiSDK) -> None:
        response = client.organization.projects.certificates.with_raw_response.deactivate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        certificate = response.parse()
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_deactivate(self, client: ExcaiSDK) -> None:
        with client.organization.projects.certificates.with_streaming_response.deactivate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            certificate = response.parse()
            assert_matches_type(ListCertificates, certificate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_deactivate(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            client.organization.projects.certificates.with_raw_response.deactivate(
                project_id="",
                certificate_ids=["cert_abc"],
            )


class TestAsyncCertificates:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncExcaiSDK) -> None:
        certificate = await async_client.organization.projects.certificates.list(
            project_id="project_id",
        )
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        certificate = await async_client.organization.projects.certificates.list(
            project_id="project_id",
            after="after",
            limit=0,
            order="asc",
        )
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.organization.projects.certificates.with_raw_response.list(
            project_id="project_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        certificate = await response.parse()
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.organization.projects.certificates.with_streaming_response.list(
            project_id="project_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            certificate = await response.parse()
            assert_matches_type(ListCertificates, certificate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.organization.projects.certificates.with_raw_response.list(
                project_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_activate(self, async_client: AsyncExcaiSDK) -> None:
        certificate = await async_client.organization.projects.certificates.activate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        )
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_activate(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.organization.projects.certificates.with_raw_response.activate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        certificate = await response.parse()
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_activate(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.organization.projects.certificates.with_streaming_response.activate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            certificate = await response.parse()
            assert_matches_type(ListCertificates, certificate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_activate(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.organization.projects.certificates.with_raw_response.activate(
                project_id="",
                certificate_ids=["cert_abc"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_deactivate(self, async_client: AsyncExcaiSDK) -> None:
        certificate = await async_client.organization.projects.certificates.deactivate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        )
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_deactivate(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.organization.projects.certificates.with_raw_response.deactivate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        certificate = await response.parse()
        assert_matches_type(ListCertificates, certificate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_deactivate(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.organization.projects.certificates.with_streaming_response.deactivate(
            project_id="project_id",
            certificate_ids=["cert_abc"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            certificate = await response.parse()
            assert_matches_type(ListCertificates, certificate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_deactivate(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `project_id` but received ''"):
            await async_client.organization.projects.certificates.with_raw_response.deactivate(
                project_id="",
                certificate_ids=["cert_abc"],
            )
