"""Model wrapper package.

Automatically exposes all subclasses of :class:`grid_cortex_client.models.base_model.BaseModel`
found in sibling modules.  This removes the need to update this file every
time a new model is added.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Type

from .base_model import BaseModel, registry  # re-export

# ---------------------------------------------------------------------------
# Dynamic discovery of wrappers
# ---------------------------------------------------------------------------


def _discover_wrappers() -> Dict[str, Type[BaseModel]]:
    wrappers: Dict[str, Type[BaseModel]] = {}
    package = __name__
    for module_info in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
        name = module_info.name
        if name.startswith("__") or name in {"base_model", "enums"}:
            continue
        module = importlib.import_module(f"{package}.{name}")
        for attr in vars(module).values():
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseModel)
                and attr is not BaseModel
            ):
                wrappers[attr.__name__] = attr
    return wrappers


_WRAPPERS = _discover_wrappers()

# Re-export discovered wrapper classes at package level
globals().update(_WRAPPERS)
__all__ = ["BaseModel", "registry", *sorted(_WRAPPERS.keys())]
