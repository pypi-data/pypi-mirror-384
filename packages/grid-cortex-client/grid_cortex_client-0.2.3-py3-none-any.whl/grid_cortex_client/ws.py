from __future__ import annotations

import json
import ssl
from typing import Any, Dict, Optional

import websocket  # type: ignore


class WebSocketSession:
    """Simple synchronous WebSocket session wrapper using *websocket-client*.

    This class is internal to *grid_cortex_client* and should not be instantiated
    directly.  Obtain a session via :pymeth:`grid_cortex_client.CortexClient.start_session`.
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float | None = 30.0,
    ) -> None:
        self._url = url
        self._headers = headers or {}
        self._timeout = timeout
        self._ws: websocket.WebSocket = self._connect()

    # ---------------------------------------------------------------------
    # Core API
    # ---------------------------------------------------------------------

    def send_json(self, payload: Dict[str, Any]) -> None:  # noqa: D401
        """Send a JSON payload over the websocket."""
        self._ws.send(json.dumps(payload))

    def recv_json(self) -> Dict[str, Any]:  # noqa: D401
        """Receive a JSON payload from the websocket (blocking)."""
        msg = self._ws.recv()
        return json.loads(msg)

    def close(self) -> None:
        """Close the underlying websocket connection."""
        self._ws.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> websocket.WebSocket:
        ws = websocket.create_connection(
            self._url,
            header=[f"{k}: {v}" for k, v in self._headers.items()],
            timeout=self._timeout,
            sslopt={"cert_reqs": ssl.CERT_NONE},
            enable_multithread=True,
        )
        return ws

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------

    def __enter__(self):  # noqa: D401
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: D401
        self.close()
        return False
