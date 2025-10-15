# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .._types import FileTypes

__all__ = ["FileExtractTextParams"]


class FileExtractTextParams(TypedDict, total=False):
    file: Required[FileTypes]
    """The file to upload."""

    clean_text: bool
    """Whether to clean the extracted text"""
