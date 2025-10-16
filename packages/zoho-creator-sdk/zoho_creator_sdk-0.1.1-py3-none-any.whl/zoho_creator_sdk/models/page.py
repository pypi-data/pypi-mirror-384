"""
Pydantic model for pages in the Zoho Creator SDK.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from .base import CreatorBaseModel


class Page(CreatorBaseModel):
    """Represents a page within a Zoho Creator application."""

    id: str = Field(description="The unique identifier of the page.")
    name: str = Field(description="The name of the page.")
    link_name: str = Field(description="The link name of the page (URL-friendly).")
    application_id: str = Field(
        description="The ID of the application the page belongs to."
    )
    description: Optional[str] = Field(
        default=None, description="A description of the page."
    )
    is_active: bool = Field(default=True, description="Whether the page is active.")
    created_time: Optional[str] = Field(
        default=None, description="The time the page was created."
    )
    modified_time: Optional[str] = Field(
        default=None, description="The time the page was last modified."
    )
