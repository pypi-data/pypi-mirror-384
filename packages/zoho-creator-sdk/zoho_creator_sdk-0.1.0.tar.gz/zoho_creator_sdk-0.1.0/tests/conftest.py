"""Global pytest fixtures for the Zoho Creator SDK test suite."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

import pytest

from zoho_creator_sdk.constants import Datacenter
from zoho_creator_sdk.models import APIConfig, AuthConfig


@pytest.fixture
def api_config() -> APIConfig:
    """Provide a baseline API configuration for tests."""

    return APIConfig(
        datacenter=Datacenter.US,
        timeout=10,
        max_retries=2,
        retry_delay=0.1,
    )


@pytest.fixture
def auth_config() -> AuthConfig:
    """Provide a baseline Auth configuration for tests."""

    return AuthConfig(
        client_id="client",
        client_secret="secret",
        redirect_uri="https://example.com/callback",
        refresh_token="refresh",
        access_token="initial",
        token_expiry=datetime.now(timezone.utc) + timedelta(minutes=5),
    )


@pytest.fixture
def sample_record_data() -> Mapping[str, object]:
    """Common record payload used by multiple tests."""

    return {
        "id": "rec1",
        "form_link_name": "leads",
        "data": {"Name": "Ada"},
        "created_time": "2024-01-01T10:00:00Z",
    }
