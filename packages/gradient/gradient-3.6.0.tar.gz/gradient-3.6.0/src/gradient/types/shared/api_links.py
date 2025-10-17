# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["APILinks", "Pages"]


class Pages(BaseModel):
    first: Optional[str] = None
    """First page"""

    last: Optional[str] = None
    """Last page"""

    next: Optional[str] = None
    """Next page"""

    previous: Optional[str] = None
    """Previous page"""


class APILinks(BaseModel):
    pages: Optional[Pages] = None
    """Information about how to reach other pages"""
