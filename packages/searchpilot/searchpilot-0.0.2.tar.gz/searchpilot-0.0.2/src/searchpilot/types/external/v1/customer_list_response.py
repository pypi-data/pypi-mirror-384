# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .customer import Customer
from ...._models import BaseModel

__all__ = ["CustomerListResponse"]


class CustomerListResponse(BaseModel):
    results: List[Customer]

    next: Optional[str] = None

    previous: Optional[str] = None
