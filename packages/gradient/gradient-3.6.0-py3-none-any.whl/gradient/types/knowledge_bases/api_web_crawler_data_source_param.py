# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["APIWebCrawlerDataSourceParam"]


class APIWebCrawlerDataSourceParam(TypedDict, total=False):
    base_url: str
    """The base url to crawl."""

    crawling_option: Literal["UNKNOWN", "SCOPED", "PATH", "DOMAIN", "SUBDOMAINS"]
    """Options for specifying how URLs found on pages should be handled.

    - UNKNOWN: Default unknown value
    - SCOPED: Only include the base URL.
    - PATH: Crawl the base URL and linked pages within the URL path.
    - DOMAIN: Crawl the base URL and linked pages within the same domain.
    - SUBDOMAINS: Crawl the base URL and linked pages for any subdomain.
    """

    embed_media: bool
    """Whether to ingest and index media (images, etc.) on web pages."""
