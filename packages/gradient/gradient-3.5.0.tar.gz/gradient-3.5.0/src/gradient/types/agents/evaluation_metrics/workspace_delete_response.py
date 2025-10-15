# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ...._models import BaseModel

__all__ = ["WorkspaceDeleteResponse"]


class WorkspaceDeleteResponse(BaseModel):
    workspace_uuid: Optional[str] = None
    """Workspace"""
