"""Abstract base class for model wrappers.

This version adds:

1. A metaclass that automatically registers every concrete subclass in a
   global registry so that ``CortexClient`` can discover available wrappers
   without manual bookkeeping.
2. An optional ``transport`` parameter that allows the shared HTTP
   implementation held by :class:`~grid_cortex_client.cortex_client.CortexClient`
   to be injected.  The transport object must expose ``post_json(path, json)`` –
   exactly what the existing ``HTTPClient`` already provides.
3. A concrete :py:meth:`run` implementation that performs the common
   *preprocess → HTTP POST → postprocess* chain.  Individual wrappers may still
   override ``run`` if they need custom behavior, but most can inherit it.
"""

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, Optional, ClassVar, Type


_REGISTRY: dict[str, "type[BaseModel]"] = {}


class _ModelMeta(ABCMeta):
    """Metaclass that auto-registers subclasses keyed by ``model_id``."""

    def __init__(cls, name: str, bases: tuple[type, ...], ns: dict[str, Any]):  # type: ignore[override]
        super().__init__(name, bases, ns)

        model_id: Optional[str] = getattr(cls, "model_id", None)
        # Only register *concrete* subclasses that declare a model_id.
        if model_id and not name.startswith("Base"):
            key = model_id.lower()
            if key in _REGISTRY:
                raise RuntimeError(
                    f"Duplicate model_id '{model_id}' for {cls.__name__} and {_REGISTRY[key].__name__}."
                )
            _REGISTRY[key] = cls  # type: ignore[assignment]


class BaseModel(ABC, metaclass=_ModelMeta):
    """
    Interface for all client-side wrappers.

    Concrete subclasses must implement

    * :py:meth:`preprocess`
    * :py:meth:`postprocess`

    They *may* override :py:meth:`run` and :py:meth:`visualize` if the default
    behaviour is insufficient.
    """

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    model_id: ClassVar[str]  # subclasses *must* set

    def __init__(self, *, transport: Optional[Any] = None):
        """Create a wrapper.

        Args:
            transport: Shared HTTP transport injected by :class:`CortexClient`.
                The object must provide ``post(path: str, json: dict, timeout: float | None = None)``.
                If *None*, the wrapper will raise :class:`RuntimeError` when :py:meth:`run` is used.
        """
        if not hasattr(self, "model_id"):
            raise TypeError(
                "Concrete wrapper class must define a class attribute 'model_id'."
            )

        self._transport = transport

    # ------------------------------------------------------------------
    # Required hooks
    # ------------------------------------------------------------------

    @abstractmethod
    def preprocess(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """Convert raw input into JSON payload.

        Concrete implementations should accept flexible Python objects (file
        paths, ``np.ndarray``, ``PIL.Image`` …) and return a dictionary that can
        be serialized with :pyfunc:`json.dumps`.
        """
        pass

    @abstractmethod
    def postprocess(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """Convert server JSON into a convenient Python object."""
        pass

    # ------------------------------------------------------------------
    # Default helpers
    # ------------------------------------------------------------------

    def run(self, timeout: float | None = None, **kwargs) -> Any:  # noqa: D401 simple method
        """End-to-end inference helper.

        Typical wrappers do *not* need to override this method – the default
        simply chains :py:meth:`preprocess` → HTTP POST → :py:meth:`postprocess`.
        """

        if self._transport is None:
            raise RuntimeError(
                "This wrapper was instantiated without a transport. "
                "Use CortexClient.run(), or pass a transport explicitly."
            )

        payload = self.preprocess(**kwargs)  # type: ignore[arg-type]
        payload.setdefault("model_id", self.model_id)

        endpoint = f"/{self.model_id}/run"
        raw = self._transport.post(endpoint, json=payload, timeout=timeout)
        return self.postprocess(raw)

    def visualize(
        self, processed_output: Any, original_input: Optional[Any] = None, **kwargs
    ) -> None:  # noqa: D401
        """Optional visualisation hook – no-op by default."""

        from pprint import (
            pprint,
        )  # local import to avoid unnecessary dependency at import time

        print(f"[visualize] '{self.model_id}' output (debug-print only):")
        pprint(processed_output)


# ------------------------------------------------------------------
# Helper exposed for other modules
# ------------------------------------------------------------------


def registry() -> dict[str, Type[BaseModel]]:  # noqa: D401 helper func
    """Return mapping *model_id → wrapper class*.  Used by CortexClient."""

    return _REGISTRY.copy()
