# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, TypedDict

__all__ = ["URLExtractTextParams", "Proxy"]


class URLExtractTextParams(TypedDict, total=False):
    url: Required[str]
    """The URL to extract text from."""

    clean_text: bool
    """Whether to clean extracted text"""

    headers: Dict[str, str]
    """Custom HTTP headers to send with the request (case-insensitive)"""

    proxy: Proxy
    """Proxy configuration for the request"""


class Proxy(TypedDict, total=False):
    password: str
    """Proxy password for authentication"""

    server: str
    """
    Proxy server URL (e.g., http://proxy.example.com:8080 or
    socks5://proxy.example.com:1080)
    """

    username: str
    """Proxy username for authentication"""
