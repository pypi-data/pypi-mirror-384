# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from crawler.dev import CrawlerDev, AsyncCrawlerDev
from tests.utils import assert_matches_type
from crawler.dev.types import URLExtractTextResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestURLs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_extract_text(self, client: CrawlerDev) -> None:
        url = client.urls.extract_text(
            url="url",
        )
        assert_matches_type(URLExtractTextResponse, url, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_extract_text_with_all_params(self, client: CrawlerDev) -> None:
        url = client.urls.extract_text(
            url="url",
            clean_text=True,
            headers={
                "User-Agent": "Custom Bot/1.0",
                "X-API-Key": "my-api-key",
                "Accept-Language": "en-US",
            },
            proxy={
                "password": "password",
                "server": "server",
                "username": "username",
            },
        )
        assert_matches_type(URLExtractTextResponse, url, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_extract_text(self, client: CrawlerDev) -> None:
        response = client.urls.with_raw_response.extract_text(
            url="url",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        url = response.parse()
        assert_matches_type(URLExtractTextResponse, url, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_extract_text(self, client: CrawlerDev) -> None:
        with client.urls.with_streaming_response.extract_text(
            url="url",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            url = response.parse()
            assert_matches_type(URLExtractTextResponse, url, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncURLs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_extract_text(self, async_client: AsyncCrawlerDev) -> None:
        url = await async_client.urls.extract_text(
            url="url",
        )
        assert_matches_type(URLExtractTextResponse, url, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_extract_text_with_all_params(self, async_client: AsyncCrawlerDev) -> None:
        url = await async_client.urls.extract_text(
            url="url",
            clean_text=True,
            headers={
                "User-Agent": "Custom Bot/1.0",
                "X-API-Key": "my-api-key",
                "Accept-Language": "en-US",
            },
            proxy={
                "password": "password",
                "server": "server",
                "username": "username",
            },
        )
        assert_matches_type(URLExtractTextResponse, url, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_extract_text(self, async_client: AsyncCrawlerDev) -> None:
        response = await async_client.urls.with_raw_response.extract_text(
            url="url",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        url = await response.parse()
        assert_matches_type(URLExtractTextResponse, url, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_extract_text(self, async_client: AsyncCrawlerDev) -> None:
        async with async_client.urls.with_streaming_response.extract_text(
            url="url",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            url = await response.parse()
            assert_matches_type(URLExtractTextResponse, url, path=["response"])

        assert cast(Any, response.is_closed) is True
