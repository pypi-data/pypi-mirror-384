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
        """Return *response_data* unchanged (backend already JSON)."""
        return response_data

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
