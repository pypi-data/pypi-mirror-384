# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["AdminAPIKey", "Owner"]


class Owner(BaseModel):
    id: Optional[str] = None
    """The identifier, which can be referenced in API endpoints"""

    created_at: Optional[int] = None
    """The Unix timestamp (in seconds) of when the user was created"""

    name: Optional[str] = None
    """The name of the user"""

    object: Optional[str] = None
    """The object type, which is always organization.user"""

    role: Optional[str] = None
    """Always `owner`"""

    type: Optional[str] = None
    """Always `user`"""


class AdminAPIKey(BaseModel):
    id: str
    """The identifier, which can be referenced in API endpoints"""

    created_at: int
    """The Unix timestamp (in seconds) of when the API key was created"""

    last_used_at: Optional[int] = None
    """The Unix timestamp (in seconds) of when the API key was last used"""

    name: str
    """The name of the API key"""

    object: str
    """The object type, which is always `organization.admin_api_key`"""

    owner: Owner

    redacted_value: str
    """The redacted value of the API key"""

    value: Optional[str] = None
    """The value of the API key. Only shown on create."""
