"""Unit tests for base model utilities."""

from __future__ import annotations

from enum import Enum

import pytest

from zoho_creator_sdk.models.base import (
    CreatorBaseModel,
    ModelWithMetadata,
    validate_enum_value,
)


class SimpleEnum(Enum):
    OK = "ok"


class SimpleModel(CreatorBaseModel):
    value: str


def test_validate_enum_value() -> None:
    validator = validate_enum_value(SimpleEnum)

    assert validator("ok") is SimpleEnum.OK

    with pytest.raises(ValueError) as exc:
        validator("nope")

    assert "Invalid SimpleEnum" in str(exc.value)


def test_model_with_metadata_has_default_metadata() -> None:
    model = ModelWithMetadata()

    assert model.metadata is not None
    assert model.model_dump()["metadata"]
