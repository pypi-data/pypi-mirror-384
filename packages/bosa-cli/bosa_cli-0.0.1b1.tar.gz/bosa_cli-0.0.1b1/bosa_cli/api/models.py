"""Shared data models for BOSA CLI API clients.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class BosaUser(BaseModel):
    """BOSA user information."""

    id: str
    identifier: str = ""
    secret_preview: str = ""
    is_active: bool = True
    client_id: str = ""
    integrations: List[Dict[str, Any]] = Field(default_factory=list)


class CreatedBosaUser(BosaUser):
    """BOSA user information with secret."""

    secret: str = ""


class BosaToken(BaseModel):
    """BOSA authentication token."""

    token: str
    token_type: str = "Bearer"
    expires_at: datetime = Field(default_factory=datetime.now)
    is_revoked: bool = False
    user_id: str = ""


class IntegrationDetail(BaseModel):
    """Integration detail."""

    connector: str
    user_identifier: str
    auth_string: str
    auth_scopes: List[str]
    selected: bool = False
