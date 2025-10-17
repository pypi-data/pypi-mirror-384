# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from ...._models import BaseModel

__all__ = ["Account"]


class Account(BaseModel):
    id: int

    customer_slug: str

    deployment_status: Literal["deployed", "pre-deployment", "migrating", "sales", "test", "retired"]
    """
    - `deployed` - Deployed
    - `pre-deployment` - Pre Deployment
    - `migrating` - Migrating
    - `sales` - Sales
    - `test` - Test
    - `retired` - Retired
    """

    domain_name: str
    """Domain name of the site (excluding .live.spodn.com)"""

    name: str

    slug: str
