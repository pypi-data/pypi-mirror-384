# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["URLExtractTextResponse"]


class URLExtractTextResponse(BaseModel):
    content_type: Optional[str] = FieldInfo(alias="contentType", default=None)

    extracted_text: Optional[str] = FieldInfo(alias="extractedText", default=None)

    final_url: Optional[str] = FieldInfo(alias="finalUrl", default=None)

    size_bytes: Optional[int] = FieldInfo(alias="sizeBytes", default=None)

    status_code: Optional[int] = FieldInfo(alias="statusCode", default=None)

    text_length: Optional[int] = FieldInfo(alias="textLength", default=None)

    url: Optional[str] = None
