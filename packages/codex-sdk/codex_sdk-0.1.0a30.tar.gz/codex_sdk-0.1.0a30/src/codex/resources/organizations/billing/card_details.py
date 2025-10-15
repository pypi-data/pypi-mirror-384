# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.organizations.billing.organization_billing_card_details import OrganizationBillingCardDetails

__all__ = ["CardDetailsResource", "AsyncCardDetailsResource"]


class CardDetailsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CardDetailsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/cleanlab/codex-python#accessing-raw-response-data-eg-headers
        """
        return CardDetailsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CardDetailsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/cleanlab/codex-python#with_streaming_response
        """
        return CardDetailsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        organization_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Optional[OrganizationBillingCardDetails]:
        """
        Get card details for an organization.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not organization_id:
            raise ValueError(f"Expected a non-empty value for `organization_id` but received {organization_id!r}")
        return self._get(
            f"/api/organizations/{organization_id}/billing/card-details",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationBillingCardDetails,
        )


class AsyncCardDetailsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCardDetailsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/cleanlab/codex-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCardDetailsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCardDetailsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/cleanlab/codex-python#with_streaming_response
        """
        return AsyncCardDetailsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        organization_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Optional[OrganizationBillingCardDetails]:
        """
        Get card details for an organization.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not organization_id:
            raise ValueError(f"Expected a non-empty value for `organization_id` but received {organization_id!r}")
        return await self._get(
            f"/api/organizations/{organization_id}/billing/card-details",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OrganizationBillingCardDetails,
        )


class CardDetailsResourceWithRawResponse:
    def __init__(self, card_details: CardDetailsResource) -> None:
        self._card_details = card_details

        self.retrieve = to_raw_response_wrapper(
            card_details.retrieve,
        )


class AsyncCardDetailsResourceWithRawResponse:
    def __init__(self, card_details: AsyncCardDetailsResource) -> None:
        self._card_details = card_details

        self.retrieve = async_to_raw_response_wrapper(
            card_details.retrieve,
        )


class CardDetailsResourceWithStreamingResponse:
    def __init__(self, card_details: CardDetailsResource) -> None:
        self._card_details = card_details

        self.retrieve = to_streamed_response_wrapper(
            card_details.retrieve,
        )


class AsyncCardDetailsResourceWithStreamingResponse:
    def __init__(self, card_details: AsyncCardDetailsResource) -> None:
        self._card_details = card_details

        self.retrieve = async_to_streamed_response_wrapper(
            card_details.retrieve,
        )
