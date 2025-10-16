"""GSAM-2 wrapper.

Provides client-side preprocessing and post-processing for the Grounded-SAM 2
(GSAM2) segmentation endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, Union

import numpy as np
from PIL import Image
import io

from ..preprocessing import load_image, image_to_bytes

from .base_model import BaseModel


class GSAM2(BaseModel):
    """Image segmentation with Grounded-SAM 2.

    Converts an RGB input image and a *textual* prompt to the JSON payload
    expected by the `/gsam2/run` endpoint, then decodes the returned PNG mask
    into a :class:`~grid_cortex_client.types.Mask` dataclass.

    Example
    -------

    Preferred usage (through :class:`CortexClient`)
    ---------------------------------------------
    ```pycon
    >>> import numpy as np
    >>> from PIL import Image
    >>> from grid_cortex_client import CortexClient
    >>> img = np.array(Image.open("path/to/image.jpg"))
    >>> mask = CortexClient().run("gsam2", image_input=img, prompt="textual prompt")
    >>> mask.data.shape
    (480, 640)
    ```

    Direct wrapper usage
    --------------------
    ```pycon
    >>> from grid_cortex_client.models.gsam2 import GSAM2
    >>> mask = GSAM2(transport=client.http_client).run(image_input=img, prompt="textual prompt")
    ```

    Args (for :py:meth:`run`)
    ------------------------
    image_input: RGB image to segment.
    prompt: Text prompt describing the object.
    box_threshold / text_threshold / nms_threshold: Optional thresholds.

    Returns
    -------
    Mask
        Binary mask (``uint8``) with foreground = 255.

    Notes
    -----
    Low-level details are in :py:meth:`preprocess` and :py:meth:`postprocess`.
    """

    name: str = "gsam2"
    model_id: str = "gsam2"

    def __init__(self, *, transport=None) -> None:  # noqa: D401
        """Create a GSAM-2 wrapper.

        Args:
            transport: Optional shared HTTP transport.
        """
        super().__init__(transport=transport)

    def preprocess(
        self,
        *,
        image_input: Union[str, Image.Image, np.ndarray],
        prompt: str,
        box_threshold: float | None = None,
        text_threshold: float | None = None,
        nms_threshold: float | None = None,
    ) -> Dict[str, Any]:
        """Prepare JSON payload for the GSAM-2 endpoint.

        Args:
            image_input: Image to analyse (file path, URL, ``PIL.Image`` or
                ``np.ndarray``).
            prompt: Text prompt describing the object to segment.
            box_threshold: Optional confidence threshold for detections.
            text_threshold: Optional text confidence threshold.
            nms_threshold: Optional Non-Maximum-Suppression threshold.

        Returns:
            JSON-serialisable dictionary consumed by the `/gsam2/run` route.

        Raises:
            ValueError: If the image cannot be loaded.
        """
        pil = load_image(image_input)
        encoded_img = image_to_bytes(pil, encoding_format="JPEG")
        payload: Dict[str, Any] = {
            "image_input": encoded_img,
            "prompt": prompt,
        }
        if box_threshold is not None:
            payload["box_threshold"] = box_threshold
        if text_threshold is not None:
            payload["text_threshold"] = text_threshold
        if nms_threshold is not None:
            payload["nms_threshold"] = nms_threshold
        return payload

    def postprocess(
        self, response_data: Dict[str, Any], mask_key: str = "output", **_: Any
    ) -> np.ndarray:
        """Decode base-64 PNG mask into a :class:`Mask` dataclass.

        Args:
            response_data: Raw JSON dictionary from the server.
            mask_key: Key in ``response_data`` that stores the mask string.

        Returns:
            Binary segmentation mask as numpy array (H, W) with dtype uint8.
            Foreground pixels are 255, background pixels are 0.

        Raises:
            ValueError: If *mask_key* is missing from the response.
        """
        if mask_key not in response_data:
            raise ValueError("Mask key missing in response.")
        
        # Server now returns raw PNG bytes (not base64)
        mask_bytes = response_data[mask_key]
        pil_img = Image.open(io.BytesIO(mask_bytes))
        pil_img.load()
        return np.array(pil_img, dtype=np.uint8)

    def run(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        prompt: str,
        box_threshold: float | None = None,
        text_threshold: float | None = None,
        nms_threshold: float | None = None,
        timeout: float | None = None,
    ) -> np.ndarray:
        """Segment objects in image using text prompt.

        Args:
            image_input: RGB image as file path, URL, PIL Image, or numpy array.
            prompt: Text description of objects to segment.
            box_threshold: Optional confidence threshold (0.0-1.0) for filtering detections.
            text_threshold: Optional text confidence threshold (0.0-1.0).
            nms_threshold: Optional Non-Maximum-Suppression threshold (0.0-1.0).
            timeout: Optional timeout in seconds for the HTTP request.

        Returns:
            Binary segmentation mask as numpy array (H, W) with dtype uint8.
            Foreground pixels are 255, background pixels are 0.

        Raises:
            ValueError: If image cannot be loaded or prompt is empty.
            RuntimeError: If no HTTP transport is configured.
            Exception: If the HTTP request fails.

        Examples:
            >>> from grid_cortex_client import CortexClient, ModelType
            >>> import numpy as np
            >>> from PIL import Image
            >>> client = CortexClient()
            >>> image = np.array(Image.open("cat.jpg"))
            >>> mask = client.run(ModelType.GSAM2, image_input=image, prompt="a cat")
            >>> print(mask.shape)  # (480, 640)
        """
        return super().run(
            image_input=image_input,
            prompt=prompt,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
            nms_threshold=nms_threshold,
            timeout=timeout,
        )
