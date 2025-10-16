"""Unit tests for :mod:`zoho_creator_sdk.constants`."""

from __future__ import annotations

import pytest

from zoho_creator_sdk.constants import Datacenter


@pytest.mark.parametrize(
    "datacenter, api_url, accounts_url",
    [
        (Datacenter.US, "https://www.zohoapis.com", "https://accounts.zoho.com"),
        (Datacenter.EU, "https://www.zohoapis.eu", "https://accounts.zoho.eu"),
        (Datacenter.IN, "https://www.zohoapis.in", "https://accounts.zoho.in"),
        (
            Datacenter.AU,
            "https://www.zohoapis.com.au",
            "https://accounts.zoho.au",
        ),
        (Datacenter.CA, "https://www.zohoapis.ca", "https://accounts.zoho.ca"),
    ],
)
def test_datacenter_urls(
    datacenter: Datacenter, api_url: str, accounts_url: str
) -> None:
    """Each datacenter exposes the expected service URLs."""

    assert datacenter.api_url == api_url
    assert datacenter.accounts_url == accounts_url
