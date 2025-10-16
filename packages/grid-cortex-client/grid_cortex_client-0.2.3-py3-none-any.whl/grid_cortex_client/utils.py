# This file is currently empty but kept for future utility functions

# -------------------- MsgPack helpers --------------------
from typing import Any


try:
    import msgpack  # type: ignore
    import msgpack_numpy as mnp  # type: ignore

    mnp.patch()  # Enable NumPy support automatically

    def packb(obj: Any) -> bytes:  # noqa: D401 simple wrapper
        """Pack *obj* to msgpack bytes with numpy support."""
        return msgpack.packb(obj, default=mnp.encode, use_bin_type=True)

    def unpackb(data: bytes) -> Any:  # noqa: D401 simple wrapper
        """Unpack msgpack *data* with numpy support."""
        return msgpack.unpackb(data, object_hook=mnp.decode, raw=False, strict_map_key=False)

except ModuleNotFoundError:  # pragma: no cover – optional dep

    def _missing() -> None:  # type: ignore
        raise ImportError("msgpack and msgpack_numpy are required for binary transport. Install them with `pip install msgpack msgpack-numpy`. ")

    # Stub functions raising helpful error if msgpack not installed
    def packb(_obj: Any) -> bytes:  # type: ignore
        _missing()

    def unpackb(_data: bytes) -> Any:  # type: ignore
        _missing()