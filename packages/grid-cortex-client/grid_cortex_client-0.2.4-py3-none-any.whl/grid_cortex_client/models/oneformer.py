# grid_cortex_client/src/grid_cortex_client/models/oneformer.py
"""OneFormer wrapper.

Unified image segmentation (panoptic / semantic / instance) powered by
OneFormer.
"""

from __future__ import annotations

from typing import Any, Dict, Union

import numpy as np
from PIL import Image

from ..preprocessing import load_image, image_to_bytes

from .base_model import BaseModel


class OneFormer(BaseModel):
    """Unified segmentation (OneFormer).

    Supports *panoptic*, *semantic* and *instance* modes.

    Preferred usage
    ---------------
    ```pycon
    >>> masks = CortexClient().run("oneformer", image_input=img, mode="panoptic")
    ```

    The returned value depends on the *mode* chosen by the backend.
    """

    name: str = "oneformer"
    model_id: str = "oneformer"

    # ------------------------------------------------------------------
    # Pre- / post- processing
    # ------------------------------------------------------------------

    def preprocess(
        self,
        *,
        image_input: Union[str, Image.Image, np.ndarray],
        mode: str = "panoptic",
    ) -> Dict[str, Any]:
        """Prepare JSON payload for OneFormer.

        Args:
            image_input: Image (path / URL / PIL / ndarray).
            mode: Segmentation mode – "panoptic" | "semantic" | "instance".
        """
        pil = load_image(image_input)
        return {"image_input": image_to_bytes(pil, encoding_format="JPEG"), "mode": mode}

    def postprocess(self, response_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:  # noqa: D401
        """Decode PNG bytes returned by the backend into a numpy array.

        The service responds with a dictionary containing:

        - ``output``: PNG-encoded segmentation mask (bytes)
        - ``label_map``: ``Dict[int, str]`` mapping label IDs → names
        - ``latency_ms``: Inference latency in milliseconds

        For convenience we convert the PNG blob to a ``np.ndarray`` (``uint8``)
        before returning it, so the caller gets the same type that *GSAM-2*
        returns.
        """

        # The view functions always wrap the result in a list when batch
        # inference is enabled.  Unwrap if necessary.
        if isinstance(response_data, list):
            response_data = response_data[0]

        import io
        from PIL import Image

        png_bytes = response_data.get("output")
        if isinstance(png_bytes, (bytes, bytearray)):
            pil_img = Image.open(io.BytesIO(png_bytes))
            pil_img.load()
            mask_np = np.array(pil_img, dtype=np.uint8)
        else:  # Already an array (unlikely but be defensive)
            mask_np = np.asarray(png_bytes, dtype=np.uint8)

        # Preserve extra metadata for caller (latency, label_map…)
        return {
            "output": mask_np,
            "label_map": response_data.get("label_map", {}),
            "latency_ms": response_data.get("latency_ms"),
        }

    def run(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        mode: str = "panoptic",
        timeout: float | None = None,
    ) -> Dict[str, Any]:
        """Segment an image using OneFormer.

        Args:
            image_input (Union[str, Image.Image, np.ndarray]): RGB input image.
            mode (str): "panoptic", "semantic" or "instance".
            timeout (float | None): Optional HTTP timeout.

        Returns:
            Dict[str, Any]: Backend-specific segmentation output.

        Examples:
            >>> from grid_cortex_client import CortexClient, ModelType
            >>> import numpy as np
            >>> from PIL import Image
            >>> client = CortexClient()
            >>> image = np.array(Image.open("cat.jpg"))
            >>> result = client.run(ModelType.ONEFORMER, image_input=image, mode="semantic")
        """
        return super().run(image_input=image_input, mode=mode, timeout=timeout)
