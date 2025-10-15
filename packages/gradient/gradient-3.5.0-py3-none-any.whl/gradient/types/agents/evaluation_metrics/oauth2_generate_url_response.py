# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ...._models import BaseModel

__all__ = ["Oauth2GenerateURLResponse"]


class Oauth2GenerateURLResponse(BaseModel):
    url: Optional[str] = None
    """The oauth2 url"""
