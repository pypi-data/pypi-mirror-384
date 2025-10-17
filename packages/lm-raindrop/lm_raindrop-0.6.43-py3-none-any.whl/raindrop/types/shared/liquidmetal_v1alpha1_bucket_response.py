# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["LiquidmetalV1alpha1BucketResponse"]


class LiquidmetalV1alpha1BucketResponse(BaseModel):
    application_name: Optional[str] = FieldInfo(alias="applicationName", default=None)
    """**EXAMPLE** "my-app" """

    application_version_id: Optional[str] = FieldInfo(alias="applicationVersionId", default=None)
    """**EXAMPLE** "01jtryx2f2f61ryk06vd8mr91p" """

    bucket_name: Optional[str] = FieldInfo(alias="bucketName", default=None)
    """**EXAMPLE** "my-smartbucket" """
