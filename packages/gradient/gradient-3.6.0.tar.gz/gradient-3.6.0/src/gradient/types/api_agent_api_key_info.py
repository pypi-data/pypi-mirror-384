# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["APIAgentAPIKeyInfo"]


class APIAgentAPIKeyInfo(BaseModel):
    created_at: Optional[datetime] = None
    """Creation date"""

    created_by: Optional[str] = None
    """Created by"""

    deleted_at: Optional[datetime] = None
    """Deleted date"""

    name: Optional[str] = None
    """Name"""

    secret_key: Optional[str] = None

    uuid: Optional[str] = None
    """Uuid"""
