"""Grid Cortex Python client.

This package provides :class:`CortexClient` for high-level model inference.
Use :class:`ModelType` enum to specify which model to run.
"""

import os

# Public API first (ruff E402)
from .model_type import ModelType  # re-export static enum

if os.environ.get("GRID_CORTEX_SKIP_PUBLIC_API") != "1":
    from .cortex_client import CortexClient

# Configure the library logger to be silent by default **after** imports to satisfy E402.
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "CortexClient",
    "ModelType",
]
