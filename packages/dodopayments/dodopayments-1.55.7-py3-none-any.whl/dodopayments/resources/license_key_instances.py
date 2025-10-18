# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import license_key_instance_list_params, license_key_instance_update_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncDefaultPageNumberPagination, AsyncDefaultPageNumberPagination
from .._base_client import AsyncPaginator, make_request_options
from ..types.license_key_instance import LicenseKeyInstance

__all__ = ["LicenseKeyInstancesResource", "AsyncLicenseKeyInstancesResource"]


class LicenseKeyInstancesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> LicenseKeyInstancesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dodopayments/dodopayments-python#accessing-raw-response-data-eg-headers
        """
        return LicenseKeyInstancesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LicenseKeyInstancesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dodopayments/dodopayments-python#with_streaming_response
        """
        return LicenseKeyInstancesResourceWithStreamingResponse(self)

    def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LicenseKeyInstance:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/license_key_instances/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LicenseKeyInstance,
        )

    def update(
        self,
        id: str,
        *,
        name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LicenseKeyInstance:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._patch(
            f"/license_key_instances/{id}",
            body=maybe_transform({"name": name}, license_key_instance_update_params.LicenseKeyInstanceUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LicenseKeyInstance,
        )

    def list(
        self,
        *,
        license_key_id: Optional[str] | Omit = omit,
        page_number: Optional[int] | Omit = omit,
        page_size: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncDefaultPageNumberPagination[LicenseKeyInstance]:
        """
        Args:
          license_key_id: Filter by license key ID

          page_number: Page number default is 0

          page_size: Page size default is 10 max is 100

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/license_key_instances",
            page=SyncDefaultPageNumberPagination[LicenseKeyInstance],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "license_key_id": license_key_id,
                        "page_number": page_number,
                        "page_size": page_size,
                    },
                    license_key_instance_list_params.LicenseKeyInstanceListParams,
                ),
            ),
            model=LicenseKeyInstance,
        )


class AsyncLicenseKeyInstancesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncLicenseKeyInstancesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/dodopayments/dodopayments-python#accessing-raw-response-data-eg-headers
        """
        return AsyncLicenseKeyInstancesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLicenseKeyInstancesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/dodopayments/dodopayments-python#with_streaming_response
        """
        return AsyncLicenseKeyInstancesResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LicenseKeyInstance:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/license_key_instances/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LicenseKeyInstance,
        )

    async def update(
        self,
        id: str,
        *,
        name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LicenseKeyInstance:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._patch(
            f"/license_key_instances/{id}",
            body=await async_maybe_transform(
                {"name": name}, license_key_instance_update_params.LicenseKeyInstanceUpdateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LicenseKeyInstance,
        )

    def list(
        self,
        *,
        license_key_id: Optional[str] | Omit = omit,
        page_number: Optional[int] | Omit = omit,
        page_size: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[LicenseKeyInstance, AsyncDefaultPageNumberPagination[LicenseKeyInstance]]:
        """
        Args:
          license_key_id: Filter by license key ID

          page_number: Page number default is 0

          page_size: Page size default is 10 max is 100

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/license_key_instances",
            page=AsyncDefaultPageNumberPagination[LicenseKeyInstance],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "license_key_id": license_key_id,
                        "page_number": page_number,
                        "page_size": page_size,
                    },
                    license_key_instance_list_params.LicenseKeyInstanceListParams,
                ),
            ),
            model=LicenseKeyInstance,
        )


class LicenseKeyInstancesResourceWithRawResponse:
    def __init__(self, license_key_instances: LicenseKeyInstancesResource) -> None:
        self._license_key_instances = license_key_instances

        self.retrieve = to_raw_response_wrapper(
            license_key_instances.retrieve,
        )
        self.update = to_raw_response_wrapper(
            license_key_instances.update,
        )
        self.list = to_raw_response_wrapper(
            license_key_instances.list,
        )


class AsyncLicenseKeyInstancesResourceWithRawResponse:
    def __init__(self, license_key_instances: AsyncLicenseKeyInstancesResource) -> None:
        self._license_key_instances = license_key_instances

        self.retrieve = async_to_raw_response_wrapper(
            license_key_instances.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            license_key_instances.update,
        )
        self.list = async_to_raw_response_wrapper(
            license_key_instances.list,
        )


class LicenseKeyInstancesResourceWithStreamingResponse:
    def __init__(self, license_key_instances: LicenseKeyInstancesResource) -> None:
        self._license_key_instances = license_key_instances

        self.retrieve = to_streamed_response_wrapper(
            license_key_instances.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            license_key_instances.update,
        )
        self.list = to_streamed_response_wrapper(
            license_key_instances.list,
        )


class AsyncLicenseKeyInstancesResourceWithStreamingResponse:
    def __init__(self, license_key_instances: AsyncLicenseKeyInstancesResource) -> None:
        self._license_key_instances = license_key_instances

        self.retrieve = async_to_streamed_response_wrapper(
            license_key_instances.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            license_key_instances.update,
        )
        self.list = async_to_streamed_response_wrapper(
            license_key_instances.list,
        )
