"""ZoeDepth wrapper.

Client-side helper for the monocular depth-estimation endpoint powered by
ZoeDepth.
"""

from __future__ import annotations

from typing import Any, Dict, Union

import numpy as np
from PIL import Image

from ..preprocessing import load_image, image_to_bytes
import numpy as np
from io import BytesIO
import numpy as np
from ..utils import unpackb
from .base_model import BaseModel


class ZoeDepth(BaseModel):
    """Monocular depth estimation (ZoeDepth).

    Preferred usage (through :class:`CortexClient`)
    ---------------------------------------------
    ```pycon
    >>> depth = CortexClient().run("zoedepth", image_input=img)
    >>> depth.values.shape
    (480, 640)
    ```

    Direct wrapper usage
    --------------------
    ```pycon
    >>> from grid_cortex_client.models.zoedepth import ZoeDepth
    >>> wrapper = ZoeDepth(transport=client.http_client)
    >>> depth = wrapper.run(image_input=img)
    ```

    Args (for :py:meth:`run`)
    ------------------------
    image_input: RGB image (path, URL, ``PIL.Image`` or ``np.ndarray``).

    Returns
    -------
    DepthMap
        Metric depth in metres (``float32``).

    Notes
    -----
    The lower-level :py:meth:`preprocess` and :py:meth:`postprocess` helpers are
    called automatically by :py:meth:`run` and are usually **not** needed by
    user code.
    """

    name: str = "zoedepth"
    model_id: str = "zoedepth"

    def __init__(self, *, transport=None) -> None:  # noqa: D401 simple ctor
        """Create a ZoeDepth wrapper.

        Args:
            transport: Optional shared HTTP transport injected by
                :class:`~grid_cortex_client.CortexClient`.
        """
        super().__init__(transport=transport)

    # ------------------------------------------------------------------
    # BaseModel interface
    # ------------------------------------------------------------------

    def preprocess(
        self,
        *,
        image_input: Union[str, Image.Image, np.ndarray],
    ) -> Dict[str, Any]:
        """Return msgpack-ready payload with raw image bytes under key "image"."""

        pil_img = load_image(image_input)
        return {"image_input": image_to_bytes(pil_img, encoding_format="JPEG")}

    def postprocess(
        self,
        response_data: Dict[str, Any],
        **_: Any,
    ) -> np.ndarray:
        """Decode backend JSON into a :class:`DepthMap` dataclass.

        Args:
            response_data: JSON dictionary from `/zoedepth/run` containing an
                ``"output"`` key with base-64 encoded NumPy bytes.

        Returns:
            Depth map as numpy array (H, W) with dtype float32.
            Values represent metric depth in meters.

        Raises:
            ValueError: If the payload is missing or cannot be decoded.
        """
        # Server returns list[dict], take first item
        if isinstance(response_data, list):
            response_dict = response_data[0]
        else:
            response_dict = response_data

        depth_bytes = response_dict.get("output")
        if not isinstance(depth_bytes, (bytes, bytearray, memoryview)):
            raise ValueError("'output' field missing or not bytes")

        arr = np.load(BytesIO(depth_bytes), allow_pickle=False)
        return arr.astype(np.float32)

    def run(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        timeout: float | None = None,
    ) -> np.ndarray:
        """Estimate depth from single RGB image.

        Args:
            image_input: RGB image as file path, URL, PIL Image, or numpy array.
            timeout: Optional timeout in seconds for the HTTP request.

        Returns:
            Depth map as numpy array (H, W) with dtype float32.
            Values represent metric depth in meters.

        Raises:
            ValueError: If image cannot be loaded.
            RuntimeError: If no HTTP transport is configured.
            Exception: If the HTTP request fails.

        Example:
            >>> from grid_cortex_client import CortexClient, ModelType
            >>> import numpy as np
            >>> from PIL import Image
            >>> client = CortexClient()
            >>> image = np.array(Image.open("cat.jpg"))
            >>> depth = client.run(ModelType.ZOEDEPTH, image_input=image)
            >>> print(depth.shape)  # (480, 640)
        """
        return super().run(
            image_input=image_input,
            timeout=timeout,
        )
