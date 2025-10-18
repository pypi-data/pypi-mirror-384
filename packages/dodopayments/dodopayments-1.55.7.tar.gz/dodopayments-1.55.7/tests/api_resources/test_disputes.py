# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dodopayments import DodoPayments, AsyncDodoPayments
from dodopayments.types import GetDispute, DisputeListResponse
from dodopayments._utils import parse_datetime
from dodopayments.pagination import SyncDefaultPageNumberPagination, AsyncDefaultPageNumberPagination

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDisputes:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: DodoPayments) -> None:
        dispute = client.disputes.retrieve(
            "dispute_id",
        )
        assert_matches_type(GetDispute, dispute, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: DodoPayments) -> None:
        response = client.disputes.with_raw_response.retrieve(
            "dispute_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dispute = response.parse()
        assert_matches_type(GetDispute, dispute, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: DodoPayments) -> None:
        with client.disputes.with_streaming_response.retrieve(
            "dispute_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dispute = response.parse()
            assert_matches_type(GetDispute, dispute, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: DodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dispute_id` but received ''"):
            client.disputes.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_list(self, client: DodoPayments) -> None:
        dispute = client.disputes.list()
        assert_matches_type(SyncDefaultPageNumberPagination[DisputeListResponse], dispute, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: DodoPayments) -> None:
        dispute = client.disputes.list(
            created_at_gte=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_lte=parse_datetime("2019-12-27T18:11:19.117Z"),
            customer_id="customer_id",
            dispute_stage="pre_dispute",
            dispute_status="dispute_opened",
            page_number=0,
            page_size=0,
        )
        assert_matches_type(SyncDefaultPageNumberPagination[DisputeListResponse], dispute, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: DodoPayments) -> None:
        response = client.disputes.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dispute = response.parse()
        assert_matches_type(SyncDefaultPageNumberPagination[DisputeListResponse], dispute, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: DodoPayments) -> None:
        with client.disputes.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dispute = response.parse()
            assert_matches_type(SyncDefaultPageNumberPagination[DisputeListResponse], dispute, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncDisputes:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDodoPayments) -> None:
        dispute = await async_client.disputes.retrieve(
            "dispute_id",
        )
        assert_matches_type(GetDispute, dispute, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.disputes.with_raw_response.retrieve(
            "dispute_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dispute = await response.parse()
        assert_matches_type(GetDispute, dispute, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.disputes.with_streaming_response.retrieve(
            "dispute_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dispute = await response.parse()
            assert_matches_type(GetDispute, dispute, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `dispute_id` but received ''"):
            await async_client.disputes.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncDodoPayments) -> None:
        dispute = await async_client.disputes.list()
        assert_matches_type(AsyncDefaultPageNumberPagination[DisputeListResponse], dispute, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncDodoPayments) -> None:
        dispute = await async_client.disputes.list(
            created_at_gte=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_lte=parse_datetime("2019-12-27T18:11:19.117Z"),
            customer_id="customer_id",
            dispute_stage="pre_dispute",
            dispute_status="dispute_opened",
            page_number=0,
            page_size=0,
        )
        assert_matches_type(AsyncDefaultPageNumberPagination[DisputeListResponse], dispute, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.disputes.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        dispute = await response.parse()
        assert_matches_type(AsyncDefaultPageNumberPagination[DisputeListResponse], dispute, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.disputes.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            dispute = await response.parse()
            assert_matches_type(AsyncDefaultPageNumberPagination[DisputeListResponse], dispute, path=["response"])

        assert cast(Any, response.is_closed) is True
