# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ...._models import BaseModel

__all__ = ["Customer"]


class Customer(BaseModel):
    id: int

    name: str

    slug: str
