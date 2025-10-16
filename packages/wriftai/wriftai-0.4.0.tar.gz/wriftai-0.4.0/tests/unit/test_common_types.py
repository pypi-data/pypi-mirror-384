import enum as enum_module
import importlib
import sys
import typing as typing_module

import pytest


@pytest.mark.parametrize("test_py_minor_version", [10, 11])
def test_StrEnum_import(
    monkeypatch: pytest.MonkeyPatch, test_py_minor_version: int
) -> None:
    # Simulate Python version to test conditional imports in common_types
    monkeypatch.setattr(sys, "version_info", (3, test_py_minor_version, 0))

    # Inject a mock StrEnum to allow import when simulating Python >= 3.11
    monkeypatch.setattr(enum_module, "StrEnum", enum_module.Enum, raising=False)

    # Stub typing.NotRequired if missing in simulated Python >= 3.11
    if (
        test_py_minor_version >= 11
        and not hasattr(typing_module, "NotRequired")
        and not hasattr(typing_module, "Unpack")
    ):
        monkeypatch.setattr(typing_module, "NotRequired", object(), raising=False)
        monkeypatch.setattr(typing_module, "Unpack", object(), raising=False)

    import wriftai.common_types

    mod = importlib.reload(wriftai.common_types)

    assert hasattr(mod, "StrEnum")
    assert hasattr(mod, "NotRequired")
    assert hasattr(mod, "Unpack")
