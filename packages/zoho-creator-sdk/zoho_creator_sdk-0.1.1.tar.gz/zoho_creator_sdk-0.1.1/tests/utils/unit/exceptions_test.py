"""Unit tests for :mod:`zoho_creator_sdk.exceptions`."""

from __future__ import annotations

import pytest

from zoho_creator_sdk import exceptions


def test_zoho_creator_error_captures_message_and_code() -> None:
    err = exceptions.ZohoCreatorError("boom", error_code=99)

    assert err.message == "boom"
    assert err.error_code == 99
    assert isinstance(err, Exception)


def test_api_error_includes_status_code() -> None:
    err = exceptions.APIError("bad", status_code=500, error_code=123)

    assert err.status_code == 500
    assert err.error_code == 123
    assert str(err) == "bad"


def test_token_refresh_error_recoverable_flag() -> None:
    err = exceptions.TokenRefreshError("retry")

    assert err.is_recoverable is True

    non_rec = exceptions.TokenRefreshError.non_recoverable("stop", error_code=10)
    assert isinstance(non_rec, exceptions.TokenRefreshError)
    assert non_rec.is_recoverable is False
    assert non_rec.error_code == 10


@pytest.mark.parametrize(
    "exc_cls",
    [
        exceptions.AuthenticationError,
        exceptions.TokenExpiredError,
        exceptions.InvalidCredentialsError,
        exceptions.RateLimitError,
        exceptions.ResourceNotFoundError,
        exceptions.BadRequestError,
        exceptions.ServerError,
        exceptions.ZohoPermissionError,
        exceptions.ValidationError,
        exceptions.ZohoTimeoutError,
        exceptions.QuotaExceededError,
        exceptions.ConfigurationError,
        exceptions.NetworkError,
    ],
)
def test_exception_hierarchy(exc_cls: type[exceptions.ZohoCreatorError]) -> None:
    err = exc_cls("issue")

    assert isinstance(err, exceptions.ZohoCreatorError)
    assert err.message == "issue"
