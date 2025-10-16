"""
Pydantic model for custom actions in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional

from pydantic import Field

from .base import CreatorBaseModel


class CustomAction(CreatorBaseModel):
    """Represents a custom action in Zoho Creator."""

    id: str = Field(description="The unique identifier of the custom action.")
    name: str = Field(description="The name of the custom action.")
    link_name: str = Field(
        description="The link name of the custom action (URL-friendly)."
    )
    application_id: str = Field(
        description="The ID of the application the custom action belongs to."
    )
    form_id: str = Field(
        description="The ID of the form this custom action is associated with."
    )
    action_type: str = Field(
        description="The type of custom action (e.g., script, workflow, API call)."
    )
    configuration: Mapping[str, Any] = Field(
        description="Custom action-specific configuration parameters."
    )
    is_active: bool = Field(
        default=True, description="Whether the custom action is active."
    )
    created_time: datetime = Field(
        description="The time the custom action was created."
    )
    modified_time: datetime = Field(
        description="The time the custom action was last modified."
    )
    description: Optional[str] = Field(
        default=None, description="A description of the custom action."
    )
    owner: str = Field(description="The owner of the custom action.")
