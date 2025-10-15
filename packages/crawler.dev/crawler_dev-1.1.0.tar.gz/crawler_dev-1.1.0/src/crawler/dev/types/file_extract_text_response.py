# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["FileExtractTextResponse"]


class FileExtractTextResponse(BaseModel):
    content_type: Optional[str] = FieldInfo(alias="contentType", default=None)

    extracted_text: Optional[str] = FieldInfo(alias="extractedText", default=None)

    filename: Optional[str] = None

    size_bytes: Optional[int] = FieldInfo(alias="sizeBytes", default=None)

    text_length: Optional[int] = FieldInfo(alias="textLength", default=None)
