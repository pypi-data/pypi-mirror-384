# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from dodopayments import DodoPayments, AsyncDodoPayments
from dodopayments.types import (
    AddonResponse,
    AddonUpdateImagesResponse,
)
from dodopayments.pagination import SyncDefaultPageNumberPagination, AsyncDefaultPageNumberPagination

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAddons:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: DodoPayments) -> None:
        addon = client.addons.create(
            currency="AED",
            name="name",
            price=0,
            tax_category="digital_products",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: DodoPayments) -> None:
        addon = client.addons.create(
            currency="AED",
            name="name",
            price=0,
            tax_category="digital_products",
            description="description",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: DodoPayments) -> None:
        response = client.addons.with_raw_response.create(
            currency="AED",
            name="name",
            price=0,
            tax_category="digital_products",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = response.parse()
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: DodoPayments) -> None:
        with client.addons.with_streaming_response.create(
            currency="AED",
            name="name",
            price=0,
            tax_category="digital_products",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = response.parse()
            assert_matches_type(AddonResponse, addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: DodoPayments) -> None:
        addon = client.addons.retrieve(
            "id",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: DodoPayments) -> None:
        response = client.addons.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = response.parse()
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: DodoPayments) -> None:
        with client.addons.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = response.parse()
            assert_matches_type(AddonResponse, addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: DodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.addons.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_update(self, client: DodoPayments) -> None:
        addon = client.addons.update(
            id="id",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: DodoPayments) -> None:
        addon = client.addons.update(
            id="id",
            currency="AED",
            description="description",
            image_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
            price=0,
            tax_category="digital_products",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: DodoPayments) -> None:
        response = client.addons.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = response.parse()
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: DodoPayments) -> None:
        with client.addons.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = response.parse()
            assert_matches_type(AddonResponse, addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: DodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.addons.with_raw_response.update(
                id="",
            )

    @parametrize
    def test_method_list(self, client: DodoPayments) -> None:
        addon = client.addons.list()
        assert_matches_type(SyncDefaultPageNumberPagination[AddonResponse], addon, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: DodoPayments) -> None:
        addon = client.addons.list(
            page_number=0,
            page_size=0,
        )
        assert_matches_type(SyncDefaultPageNumberPagination[AddonResponse], addon, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: DodoPayments) -> None:
        response = client.addons.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = response.parse()
        assert_matches_type(SyncDefaultPageNumberPagination[AddonResponse], addon, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: DodoPayments) -> None:
        with client.addons.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = response.parse()
            assert_matches_type(SyncDefaultPageNumberPagination[AddonResponse], addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_update_images(self, client: DodoPayments) -> None:
        addon = client.addons.update_images(
            "id",
        )
        assert_matches_type(AddonUpdateImagesResponse, addon, path=["response"])

    @parametrize
    def test_raw_response_update_images(self, client: DodoPayments) -> None:
        response = client.addons.with_raw_response.update_images(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = response.parse()
        assert_matches_type(AddonUpdateImagesResponse, addon, path=["response"])

    @parametrize
    def test_streaming_response_update_images(self, client: DodoPayments) -> None:
        with client.addons.with_streaming_response.update_images(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = response.parse()
            assert_matches_type(AddonUpdateImagesResponse, addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update_images(self, client: DodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.addons.with_raw_response.update_images(
                "",
            )


class TestAsyncAddons:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncDodoPayments) -> None:
        addon = await async_client.addons.create(
            currency="AED",
            name="name",
            price=0,
            tax_category="digital_products",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncDodoPayments) -> None:
        addon = await async_client.addons.create(
            currency="AED",
            name="name",
            price=0,
            tax_category="digital_products",
            description="description",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.addons.with_raw_response.create(
            currency="AED",
            name="name",
            price=0,
            tax_category="digital_products",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = await response.parse()
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.addons.with_streaming_response.create(
            currency="AED",
            name="name",
            price=0,
            tax_category="digital_products",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = await response.parse()
            assert_matches_type(AddonResponse, addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDodoPayments) -> None:
        addon = await async_client.addons.retrieve(
            "id",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.addons.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = await response.parse()
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.addons.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = await response.parse()
            assert_matches_type(AddonResponse, addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.addons.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncDodoPayments) -> None:
        addon = await async_client.addons.update(
            id="id",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncDodoPayments) -> None:
        addon = await async_client.addons.update(
            id="id",
            currency="AED",
            description="description",
            image_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            name="name",
            price=0,
            tax_category="digital_products",
        )
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.addons.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = await response.parse()
        assert_matches_type(AddonResponse, addon, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.addons.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = await response.parse()
            assert_matches_type(AddonResponse, addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncDodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.addons.with_raw_response.update(
                id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncDodoPayments) -> None:
        addon = await async_client.addons.list()
        assert_matches_type(AsyncDefaultPageNumberPagination[AddonResponse], addon, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncDodoPayments) -> None:
        addon = await async_client.addons.list(
            page_number=0,
            page_size=0,
        )
        assert_matches_type(AsyncDefaultPageNumberPagination[AddonResponse], addon, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.addons.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = await response.parse()
        assert_matches_type(AsyncDefaultPageNumberPagination[AddonResponse], addon, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.addons.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = await response.parse()
            assert_matches_type(AsyncDefaultPageNumberPagination[AddonResponse], addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_update_images(self, async_client: AsyncDodoPayments) -> None:
        addon = await async_client.addons.update_images(
            "id",
        )
        assert_matches_type(AddonUpdateImagesResponse, addon, path=["response"])

    @parametrize
    async def test_raw_response_update_images(self, async_client: AsyncDodoPayments) -> None:
        response = await async_client.addons.with_raw_response.update_images(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        addon = await response.parse()
        assert_matches_type(AddonUpdateImagesResponse, addon, path=["response"])

    @parametrize
    async def test_streaming_response_update_images(self, async_client: AsyncDodoPayments) -> None:
        async with async_client.addons.with_streaming_response.update_images(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            addon = await response.parse()
            assert_matches_type(AddonUpdateImagesResponse, addon, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update_images(self, async_client: AsyncDodoPayments) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.addons.with_raw_response.update_images(
                "",
            )
