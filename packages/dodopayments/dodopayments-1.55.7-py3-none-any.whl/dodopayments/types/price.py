# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias

from .._models import BaseModel
from .currency import Currency
from .time_interval import TimeInterval
from .add_meter_to_price import AddMeterToPrice

__all__ = ["Price", "OneTimePrice", "RecurringPrice", "UsageBasedPrice"]


class OneTimePrice(BaseModel):
    currency: Currency
    """The currency in which the payment is made."""

    discount: int
    """Discount applied to the price, represented as a percentage (0 to 100)."""

    price: int
    """
    The payment amount, in the smallest denomination of the currency (e.g., cents
    for USD). For example, to charge $1.00, pass `100`.

    If [`pay_what_you_want`](Self::pay_what_you_want) is set to `true`, this field
    represents the **minimum** amount the customer must pay.
    """

    purchasing_power_parity: bool
    """
    Indicates if purchasing power parity adjustments are applied to the price.
    Purchasing power parity feature is not available as of now.
    """

    type: Literal["one_time_price"]

    pay_what_you_want: Optional[bool] = None
    """
    Indicates whether the customer can pay any amount they choose. If set to `true`,
    the [`price`](Self::price) field is the minimum amount.
    """

    suggested_price: Optional[int] = None
    """A suggested price for the user to pay.

    This value is only considered if [`pay_what_you_want`](Self::pay_what_you_want)
    is `true`. Otherwise, it is ignored.
    """

    tax_inclusive: Optional[bool] = None
    """Indicates if the price is tax inclusive."""


class RecurringPrice(BaseModel):
    currency: Currency
    """The currency in which the payment is made."""

    discount: int
    """Discount applied to the price, represented as a percentage (0 to 100)."""

    payment_frequency_count: int
    """
    Number of units for the payment frequency. For example, a value of `1` with a
    `payment_frequency_interval` of `month` represents monthly payments.
    """

    payment_frequency_interval: TimeInterval
    """The time interval for the payment frequency (e.g., day, month, year)."""

    price: int
    """The payment amount.

    Represented in the lowest denomination of the currency (e.g., cents for USD).
    For example, to charge $1.00, pass `100`.
    """

    purchasing_power_parity: bool
    """
    Indicates if purchasing power parity adjustments are applied to the price.
    Purchasing power parity feature is not available as of now
    """

    subscription_period_count: int
    """
    Number of units for the subscription period. For example, a value of `12` with a
    `subscription_period_interval` of `month` represents a one-year subscription.
    """

    subscription_period_interval: TimeInterval
    """The time interval for the subscription period (e.g., day, month, year)."""

    type: Literal["recurring_price"]

    tax_inclusive: Optional[bool] = None
    """Indicates if the price is tax inclusive"""

    trial_period_days: Optional[int] = None
    """Number of days for the trial period. A value of `0` indicates no trial period."""


class UsageBasedPrice(BaseModel):
    currency: Currency
    """The currency in which the payment is made."""

    discount: int
    """Discount applied to the price, represented as a percentage (0 to 100)."""

    fixed_price: int
    """The fixed payment amount.

    Represented in the lowest denomination of the currency (e.g., cents for USD).
    For example, to charge $1.00, pass `100`.
    """

    payment_frequency_count: int
    """
    Number of units for the payment frequency. For example, a value of `1` with a
    `payment_frequency_interval` of `month` represents monthly payments.
    """

    payment_frequency_interval: TimeInterval
    """The time interval for the payment frequency (e.g., day, month, year)."""

    purchasing_power_parity: bool
    """
    Indicates if purchasing power parity adjustments are applied to the price.
    Purchasing power parity feature is not available as of now
    """

    subscription_period_count: int
    """
    Number of units for the subscription period. For example, a value of `12` with a
    `subscription_period_interval` of `month` represents a one-year subscription.
    """

    subscription_period_interval: TimeInterval
    """The time interval for the subscription period (e.g., day, month, year)."""

    type: Literal["usage_based_price"]

    meters: Optional[List[AddMeterToPrice]] = None

    tax_inclusive: Optional[bool] = None
    """Indicates if the price is tax inclusive"""


Price: TypeAlias = Union[OneTimePrice, RecurringPrice, UsageBasedPrice]
