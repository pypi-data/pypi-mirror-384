# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dodopayments import DodoPayments, AsyncDodoPayments
from dodopayments.types import Refund, RefundListResponse
from dodopayments._utils import parse_datetime
from dodopayments.pagination import SyncDefaultPageNumberPagination, AsyncDefaultPageNumberPagination

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRefunds:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: DodoPayments) -> None:
        refund = client.refunds.create(
            payment_id="payment_id",
        )
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: DodoPayments) -> None:
        refund = client.refunds.create(
            payment_id="payment_id",
            items=[
                {
                    "item_id": "item_id",
                    "amount": 0,
                    "tax_inclusive": True,
                }
            ],
            reason="reason",
        )
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: DodoPayments) -> None:
        response = client.refunds.with_raw_response.create(
            payment_id="payment_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        refund = response.parse()
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: DodoPayments) -> None:
        with client.refunds.with_streaming_response.create(
            payment_id="payment_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            refund = response.parse()
            assert_matches_type(Refund, refund, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: DodoPayments) -> None:
        refund = client.refunds.retrieve(
            "refund_id",
        )
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: DodoPayments) -> None:
        response = client.refunds.with_raw_response.retrieve(
            "refund_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        refund = response.parse()
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: DodoPayments) -> None:
        with client.refunds.with_streaming_response.retrieve(
            "refund_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            refund = response.parse()
            assert_matches_type(Refund, refund, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: DodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `refund_id` but received ''"):
            client.refunds.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_list(self, client: DodoPayments) -> None:
        refund = client.refunds.list()
        assert_matches_type(SyncDefaultPageNumberPagination[RefundListResponse], refund, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: DodoPayments) -> None:
        refund = client.refunds.list(
            created_at_gte=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_lte=parse_datetime("2019-12-27T18:11:19.117Z"),
            customer_id="customer_id",
            page_number=0,
            page_size=0,
            status="succeeded",
        )
        assert_matches_type(SyncDefaultPageNumberPagination[RefundListResponse], refund, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: DodoPayments) -> None:
        response = client.refunds.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        refund = response.parse()
        assert_matches_type(SyncDefaultPageNumberPagination[RefundListResponse], refund, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: DodoPayments) -> None:
        with client.refunds.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            refund = response.parse()
            assert_matches_type(SyncDefaultPageNumberPagination[RefundListResponse], refund, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncRefunds:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncDodoPayments) -> None:
        refund = await async_client.refunds.create(
            payment_id="payment_id",
        )
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncDodoPayments) -> None:
        refund = await async_client.refunds.create(
            payment_id="payment_id",
            items=[
                {
                    "item_id": "item_id",
                    "amount": 0,
                    "tax_inclusive": True,
                }
            ],
            reason="reason",
        )
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.refunds.with_raw_response.create(
            payment_id="payment_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        refund = await response.parse()
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.refunds.with_streaming_response.create(
            payment_id="payment_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            refund = await response.parse()
            assert_matches_type(Refund, refund, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDodoPayments) -> None:
        refund = await async_client.refunds.retrieve(
            "refund_id",
        )
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.refunds.with_raw_response.retrieve(
            "refund_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        refund = await response.parse()
        assert_matches_type(Refund, refund, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.refunds.with_streaming_response.retrieve(
            "refund_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            refund = await response.parse()
            assert_matches_type(Refund, refund, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `refund_id` but received ''"):
            await async_client.refunds.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncDodoPayments) -> None:
        refund = await async_client.refunds.list()
        assert_matches_type(AsyncDefaultPageNumberPagination[RefundListResponse], refund, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncDodoPayments) -> None:
        refund = await async_client.refunds.list(
            created_at_gte=parse_datetime("2019-12-27T18:11:19.117Z"),
            created_at_lte=parse_datetime("2019-12-27T18:11:19.117Z"),
            customer_id="customer_id",
            page_number=0,
            page_size=0,
            status="succeeded",
        )
        assert_matches_type(AsyncDefaultPageNumberPagination[RefundListResponse], refund, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.refunds.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        refund = await response.parse()
        assert_matches_type(AsyncDefaultPageNumberPagination[RefundListResponse], refund, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.refunds.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            refund = await response.parse()
            assert_matches_type(AsyncDefaultPageNumberPagination[RefundListResponse], refund, path=["response"])

        assert cast(Any, response.is_closed) is True
