# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, TypedDict

__all__ = ["AccountListParams"]


class AccountListParams(TypedDict, total=False):
    cursor: str
    """The pagination cursor value."""

    customer_slug: str
    """Customer slug"""

    deployment_status: Literal["deployed", "migrating", "pre-deployment", "retired", "sales", "test"]
    """
    - `deployed` - Deployed
    - `pre-deployment` - Pre Deployment
    - `migrating` - Migrating
    - `sales` - Sales
    - `test` - Test
    - `retired` - Retired
    """

    environment: Optional[Literal["Demo", "dev", "lower_envs", "production", "qa", "staging", "uat"]]
    """
    - `production` - Production
    - `staging` - Staging
    - `qa` - QA
    - `dev` - Dev
    - `uat` - UAT
    - `lower_envs` - Lower Environments
    - `Demo` - Demo
    """
