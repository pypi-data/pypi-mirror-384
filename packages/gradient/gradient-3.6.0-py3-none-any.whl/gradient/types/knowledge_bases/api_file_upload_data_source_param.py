# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["APIFileUploadDataSourceParam"]


class APIFileUploadDataSourceParam(TypedDict, total=False):
    original_file_name: str
    """The original file name"""

    size_in_bytes: str
    """The size of the file in bytes"""

    stored_object_key: str
    """The object key the file was stored as"""
