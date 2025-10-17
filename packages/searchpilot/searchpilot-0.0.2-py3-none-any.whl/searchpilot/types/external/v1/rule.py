# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ...._models import BaseModel

__all__ = ["Rule"]


class Rule(BaseModel):
    id: int

    account_slug: str

    customer_slug: str

    enabled: bool

    is_in_split_test: bool

    name: str

    section_slug: str
