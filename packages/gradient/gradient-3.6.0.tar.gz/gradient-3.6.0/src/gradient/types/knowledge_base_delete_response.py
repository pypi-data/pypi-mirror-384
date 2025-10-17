# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["KnowledgeBaseDeleteResponse"]


class KnowledgeBaseDeleteResponse(BaseModel):
    uuid: Optional[str] = None
    """The id of the deleted knowledge base"""
