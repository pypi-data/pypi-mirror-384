# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["OneTimeProductCartItem"]


class OneTimeProductCartItem(BaseModel):
    product_id: str

    quantity: int

    amount: Optional[int] = None
    """Amount the customer pays if pay_what_you_want is enabled.

    If disabled then amount will be ignored Represented in the lowest denomination
    of the currency (e.g., cents for USD). For example, to charge $1.00, pass `100`.
    """
