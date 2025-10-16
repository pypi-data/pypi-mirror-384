"""
Pydantic model for connections in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional

from pydantic import Field

from .base import CreatorBaseModel


class Connection(CreatorBaseModel):
    """Represents a connection to an external service in Zoho Creator."""

    id: str = Field(description="The unique identifier of the connection.")
    name: str = Field(description="The name of the connection.")
    connection_type: str = Field(
        description="The type of the connection (e.g., REST, OAuth)."
    )
    application_id: str = Field(
        description="The ID of the application the connection belongs to."
    )
    configuration: Mapping[str, Any] = Field(
        description="Connection-specific configuration parameters."
    )
    is_active: bool = Field(
        default=True, description="Whether the connection is active."
    )
    is_encrypted: bool = Field(
        default=True, description="Whether the connection data is encrypted."
    )
    created_time: datetime = Field(description="The time the connection was created.")
    modified_time: datetime = Field(
        description="The time the connection was last modified."
    )
    description: Optional[str] = Field(
        default=None, description="A description of the connection."
    )
    owner: str = Field(description="The owner of the connection.")
