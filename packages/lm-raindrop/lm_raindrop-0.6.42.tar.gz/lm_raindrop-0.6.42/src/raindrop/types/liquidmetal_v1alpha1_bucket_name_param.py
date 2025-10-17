# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["LiquidmetalV1alpha1BucketNameParam"]


class LiquidmetalV1alpha1BucketNameParam(TypedDict, total=False):
    name: Required[str]
    """The name of the bucket **EXAMPLE** "my-bucket" **REQUIRED** TRUE"""

    application_name: Annotated[Optional[str], PropertyInfo(alias="applicationName")]
    """Optional Application **EXAMPLE** "my-app" **REQUIRED** FALSE"""

    version: Optional[str]
    """
    Optional version of the bucket **EXAMPLE** "01jtryx2f2f61ryk06vd8mr91p"
    **REQUIRED** FALSE
    """
