"""OWLv2 wrapper.

Client-side helper for the OWLv2 zero-shot object-detection endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, Union

import numpy as np

from ..preprocessing import load_image, image_to_bytes

from .base_model import BaseModel


class OWLv2(BaseModel):
    """Zero-shot open-vocabulary object detection (OWLv2).

    Preferred usage
    ---------------
    ```pycon
    >>> dets = CortexClient().run("owlv2", image_input=img, prompt="cat")
    >>> dets["scores"][:3]
    [0.83, 0.79, 0.61]
    ```

    Direct wrapper usage
    --------------------
    ```pycon
    >>> from grid_cortex_client.models.owlv2 import OWLv2
    >>> dets = OWLv2(transport=client.http_client).run(image_input=img, prompt="cat")
    ```

    Args (for :py:meth:`run`)
    ------------------------
    image_input: RGB image (path/URL/PIL/ndarray).
    prompt: Text prompt (single class description).
    box_threshold: Optional confidence filter.

    Returns
    -------
    dict
        ``{"boxes": [...], "scores": [...], "labels": [...]}``

    Notes
    -----
    See :py:meth:`preprocess` and :py:meth:`postprocess` for low-level details.
    """

    name: str = "owlv2"
    model_id: str = "owlv2"

    def __init__(self, *, transport=None) -> None:  # noqa: D401
        """Create an OWLv2 wrapper.

        Args:
            transport: Optional shared HTTP transport.
        """
        super().__init__(transport=transport)

    # ------------------------------------------------------------------
    # BaseModel implementation
    # ------------------------------------------------------------------

    def preprocess(
        self,
        *,
        image_input: Union[str, Image.Image, np.ndarray],
        prompt: str,
        box_threshold: float | None = None,
    ) -> Dict[str, Any]:
        """Return JSON payload for the OWLv2 endpoint.

        Args:
            image_input: Image to analyse (path, URL, ``PIL.Image`` or
                ``np.ndarray``).
            prompt: Text prompt describing the object class to detect (single
                string, *not* list).
            box_threshold: Optional confidence threshold in the range 0-1.

        Returns:
            Dictionary ready to be sent as JSON to `/owlv2/run`.

        Raises:
            ValueError: If the image cannot be loaded.
        """
        pil = load_image(image_input)
        payload: Dict[str, Any] = {
            "image_input": image_to_bytes(pil, encoding_format="JPEG"),
            "prompt": prompt,
        }
        if box_threshold is not None:
            payload["box_threshold"] = box_threshold
        return payload

    # The backend returns {"output": <b64_json_str>} where json contains boxes,
    # scores, labels.
    def postprocess(self, response_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        """Convert raw JSON response into NumPy-friendly lists.

        Args:
            response_data: Dictionary returned by the `/owlv2/run` route. Must
                contain an ``"output"`` key with a base-64-encoded JSON string.

        Returns:
            A dictionary with keys ``boxes`` (``List[List[float]]``), ``scores``
            (``List[float]``) and ``labels`` (``List[int]``).

        Raises:
            ValueError: If the response payload is malformed.
        """
        if not isinstance(response_data, dict):
            raise ValueError("Response must be a dict.")
        return response_data

    def run(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        prompt: str,
        box_threshold: float | None = None,
        timeout: float | None = None,
    ) -> Dict[str, Any]:
        """Detect objects in image using text prompt.

        Args:
            image_input: RGB image as file path, URL, PIL Image, or numpy array.
            prompt: Text description of objects to detect.
            box_threshold: Optional confidence threshold (0.0-1.0) for filtering detections.
            timeout: Optional timeout in seconds for the HTTP request.

        Returns:
            Dictionary with keys:
                - "boxes": List of bounding boxes as [x1, y1, x2, y2] coordinates
                - "scores": List of confidence scores (0.0-1.0)
                - "labels": List of label indices

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
            >>> dets = client.run(ModelType.OWLV2, image_input=image, prompt="a cat")
            >>> print(f"Found {len(dets['boxes'])} objects")
        """
        return super().run(
            image_input=image_input,
            prompt=prompt,
            box_threshold=box_threshold,
            timeout=timeout,
        )
