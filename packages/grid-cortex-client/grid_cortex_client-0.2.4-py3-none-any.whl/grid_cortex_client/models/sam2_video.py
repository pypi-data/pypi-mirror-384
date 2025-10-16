"""SAM2 Video Tracking WebSocket wrapper.

Stateful SAM-2 tracker for video sequences via WebSocket connection.
Maintains tracking state across frames for consistent object tracking.
"""

from __future__ import annotations

from typing import Any, Dict, Union

from ..ws import WebSocketSession
from .base_model import BaseModel


class SAM2Video(BaseModel):
    """Stateful SAM-2 tracker for video sequences via WebSocket.

    This model maintains tracking state across video frames, enabling consistent
    object tracking throughout a video sequence. Unlike stateless models, this
    requires establishing a WebSocket session and streaming frames.

    Workflow
    --------
    1. Call :py:meth:`init` to establish a WebSocket session
    2. Send first frame with initial points and labels
    3. Stream subsequent frames for continuous tracking
    4. Optionally add new objects mid-stream

    Examples
    --------
    >>> from grid_cortex_client import CortexClient, ModelType
    >>> import base64
    >>> import cv2
    >>> 
    >>> client = CortexClient()
    >>> 
    >>> # Start tracking session
    >>> with client.start_session(ModelType.SAM2VIDEO) as ws:
    ...     # First frame with initial points
    ...     frame_bgr = cv2.imread("frame1.jpg")
    ...     _, buf = cv2.imencode('.jpg', frame_bgr)
    ...     frame_b64 = base64.b64encode(buf).decode()
    ...     
    ...     ws.send_json({
    ...         "frame": frame_b64,
    ...         "points": [[585, 182], [600, 220]],
    ...         "labels": [1, 1]  # 1=positive, 0=negative
    ...     })
    ...     
    ...     # Get first tracking result
    ...     result = ws.recv_json()
    ...     print(f"Tracked {len(result['masks'])} objects")
    ...     
    ...     # Stream subsequent frames
    ...     for frame_path in ["frame2.jpg", "frame3.jpg"]:
    ...         frame_bgr = cv2.imread(frame_path)
    ...         _, buf = cv2.imencode('.jpg', frame_bgr)
    ...         frame_b64 = base64.b64encode(buf).decode()
    ...         
    ...         ws.send_json({"frame": frame_b64})
    ...         result = ws.recv_json()
    ...         print(f"Frame {result['frame_number']}: {len(result['masks'])} objects")
    """

    name: str = "sam2video"
    model_id: str = "sam2video"
    ROUTE_PREFIX: str = "/sam2-video"

    @classmethod
    def init(
        cls,
        client: "CortexClient",
        *,
        headers: Dict[str, str] | None = None,
        timeout: float | None = 30.0,
    ) -> WebSocketSession:
        """Initialize a WebSocket session for SAM2 video tracking.

        Parameters
        ----------
        client:
            CortexClient instance to use for the session.
        headers:
            Optional extra HTTP headers (e.g. {"x-api-key": "..."}).
        timeout:
            Socket timeout in seconds.

        Returns
        -------
        WebSocketSession
            A context-managed WebSocket session for streaming video frames.

        Examples
        --------
        >>> from grid_cortex_client import CortexClient, ModelType
        >>> client = CortexClient()
        >>> ws = SAM2Video.init(client)
        >>> with ws:
        ...     # Send frames and receive tracking results
        ...     pass
        """
        return client.start_session(cls.ROUTE_PREFIX, headers=headers, timeout=timeout)

    def preprocess(self, *args, **kwargs) -> Dict[str, Any]:
        """Not used for stateful models.

        Use :py:meth:`init` to get a WebSocket session instead.
        """
        raise RuntimeError(
            "SAM2Video is stateful and requires a WebSocket session. "
            "Use SAM2Video.init(client) to get a WebSocketSession, "
            "then stream frames via .send_json() / .recv_json()."
        )

    def postprocess(self, *args, **kwargs) -> Any:
        """Not used for stateful models.

        Use :py:meth:`init` to get a WebSocket session instead.
        """
        raise RuntimeError(
            "SAM2Video is stateful and requires a WebSocket session. "
            "Use SAM2Video.init(client) to get a WebSocketSession, "
            "then stream frames via .send_json() / .recv_json()."
        )

    def run(self, *args, **kwargs) -> Any:
        """Not used for stateful models.

        Use :py:meth:`init` to get a WebSocket session instead.
        """
        raise RuntimeError(
            "SAM2Video is stateful and requires a WebSocket session. "
            "Use SAM2Video.init(client) to get a WebSocketSession, "
            "then stream frames via .send_json() / .recv_json()."
        )