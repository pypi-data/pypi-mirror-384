# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types import (
    UsageResponse,
    OrganizationListAuditLogsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestOrganization:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_costs(self, client: ExcaiSDK) -> None:
        organization = client.organization.get_costs(
            start_time=0,
        )
        assert_matches_type(UsageResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_costs_with_all_params(self, client: ExcaiSDK) -> None:
        organization = client.organization.get_costs(
            start_time=0,
            bucket_width="1d",
            end_time=0,
            group_by=["project_id"],
            limit=0,
            page="page",
            project_ids=["string"],
        )
        assert_matches_type(UsageResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_costs(self, client: ExcaiSDK) -> None:
        response = client.organization.with_raw_response.get_costs(
            start_time=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = response.parse()
        assert_matches_type(UsageResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_costs(self, client: ExcaiSDK) -> None:
        with client.organization.with_streaming_response.get_costs(
            start_time=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = response.parse()
            assert_matches_type(UsageResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_audit_logs(self, client: ExcaiSDK) -> None:
        organization = client.organization.list_audit_logs()
        assert_matches_type(OrganizationListAuditLogsResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_audit_logs_with_all_params(self, client: ExcaiSDK) -> None:
        organization = client.organization.list_audit_logs(
            actor_emails=["string"],
            actor_ids=["string"],
            after="after",
            before="before",
            effective_at={
                "gt": 0,
                "gte": 0,
                "lt": 0,
                "lte": 0,
            },
            event_types=["api_key.created"],
            limit=0,
            project_ids=["string"],
            resource_ids=["string"],
        )
        assert_matches_type(OrganizationListAuditLogsResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_audit_logs(self, client: ExcaiSDK) -> None:
        response = client.organization.with_raw_response.list_audit_logs()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = response.parse()
        assert_matches_type(OrganizationListAuditLogsResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_audit_logs(self, client: ExcaiSDK) -> None:
        with client.organization.with_streaming_response.list_audit_logs() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = response.parse()
            assert_matches_type(OrganizationListAuditLogsResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncOrganization:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_costs(self, async_client: AsyncExcaiSDK) -> None:
        organization = await async_client.organization.get_costs(
            start_time=0,
        )
        assert_matches_type(UsageResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_costs_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        organization = await async_client.organization.get_costs(
            start_time=0,
            bucket_width="1d",
            end_time=0,
            group_by=["project_id"],
            limit=0,
            page="page",
            project_ids=["string"],
        )
        assert_matches_type(UsageResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_costs(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.organization.with_raw_response.get_costs(
            start_time=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = await response.parse()
        assert_matches_type(UsageResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_costs(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.organization.with_streaming_response.get_costs(
            start_time=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = await response.parse()
            assert_matches_type(UsageResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_audit_logs(self, async_client: AsyncExcaiSDK) -> None:
        organization = await async_client.organization.list_audit_logs()
        assert_matches_type(OrganizationListAuditLogsResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_audit_logs_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        organization = await async_client.organization.list_audit_logs(
            actor_emails=["string"],
            actor_ids=["string"],
            after="after",
            before="before",
            effective_at={
                "gt": 0,
                "gte": 0,
                "lt": 0,
                "lte": 0,
            },
            event_types=["api_key.created"],
            limit=0,
            project_ids=["string"],
            resource_ids=["string"],
        )
        assert_matches_type(OrganizationListAuditLogsResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_audit_logs(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.organization.with_raw_response.list_audit_logs()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = await response.parse()
        assert_matches_type(OrganizationListAuditLogsResponse, organization, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_audit_logs(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.organization.with_streaming_response.list_audit_logs() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = await response.parse()
            assert_matches_type(OrganizationListAuditLogsResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True
