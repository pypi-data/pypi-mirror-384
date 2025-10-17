# Copyright (c) Microsoft. All rights reserved.

import importlib
from typing import Any

PACKAGE_NAME = "agent_framework_a2a"
PACKAGE_EXTRA = "a2a"
_IMPORTS = ["__version__", "A2AAgent"]


def __getattr__(name: str) -> Any:
    if name in _IMPORTS:
        try:
            return getattr(importlib.import_module(PACKAGE_NAME), name)
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                f"The '{PACKAGE_EXTRA}' extra is not installed, please do `pip install agent-framework-{PACKAGE_EXTRA}`"
            ) from exc
    raise AttributeError(f"Module {PACKAGE_NAME} has no attribute {name}.")


def __dir__() -> list[str]:
    return _IMPORTS
