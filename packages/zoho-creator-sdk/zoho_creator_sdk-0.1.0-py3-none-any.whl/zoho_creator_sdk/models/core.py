"""
Pydantic models for core entities in the Zoho Creator SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional

from pydantic import EmailStr, Field

from .base import CreatorBaseModel


class Application(CreatorBaseModel):
    """Represents a Zoho Creator application."""

    application_name: str = Field(..., alias="application_name")
    date_format: str = Field(..., alias="date_format")
    creation_date: str = Field(..., alias="creation_date")
    link_name: str = Field(..., alias="link_name")
    category: int
    time_zone: str = Field(..., alias="time_zone")
    created_by: str = Field(..., alias="created_by")
    workspace_name: str = Field(..., alias="workspace_name")


class Record(CreatorBaseModel):
    """Represents a record within a Zoho Creator form."""

    id: str = Field(description="The unique identifier of the record.")
    form_id: str = Field(description="The ID of the form the record belongs to.")
    created_time: datetime = Field(description="The time the record was created.")
    modified_time: datetime = Field(
        description="The time the record was last modified."
    )
    owner: str = Field(description="The owner of the record.")
    data: Mapping[str, Any] = Field(
        description="The data of the record, as a dictionary of field names to values.",
    )


class User(CreatorBaseModel):
    """Represents a Zoho Creator user."""

    id: str = Field(description="The unique identifier of the user.")
    email: EmailStr = Field(description="The email address of the user.")
    first_name: str = Field(description="The first name of the user.")
    last_name: str = Field(description="The last name of the user.")
    role: str = Field(description="The role of the user.")
    active: bool = Field(description="Whether the user is active.")
    status: Optional[str] = Field(default=None, description="The status of the user.")
    added_time: Optional[datetime] = Field(
        default=None, description="The time the user was added."
    )
    profile: Optional[str] = Field(default=None, description="The profile of the user.")
