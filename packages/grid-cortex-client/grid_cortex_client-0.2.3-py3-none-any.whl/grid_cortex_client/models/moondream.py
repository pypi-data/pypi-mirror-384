# grid_cortex_client/src/grid_cortex_client/models/moondream.py
"""Moondream wrapper.

Vision-Language Model (VLM) powered by Moondream.

Takes image + text prompt and returns generated text response.
"""

from __future__ import annotations

from typing import Any, Dict, Union

import numpy as np
from PIL import Image

from ..preprocessing import load_image, image_to_bytes
from .base_model import BaseModel


class Moondream(BaseModel):
    """Vision-Language Model (Moondream).

    Preferred usage
    ---------------
    ```pycon
    >>> response = CortexClient().run("moondream", image_input=img, prompt="What do you see?")
    >>> print(response["output"])
    ```
    """

    name: str = "moondream"
    model_id: str = "moondream"

    # ------------------------------------------------------------------
    # BaseModel implementation
    # ------------------------------------------------------------------

    def preprocess(
        self,
        *,
        image_input: Union[str, Image.Image, np.ndarray],
        task: str,
        prompt: str = "",
        length: str = "normal",
    ) -> Dict[str, Any]:
        """Prepare JSON payload for Moondream.

        Args:
            image_input: Image (path/URL/PIL/ndarray).
            task: Task type ("vqa", "caption", "detect", "point").
            prompt: Text prompt/question about the image (required for vqa, detect, point).
            length: Caption length ("short" or "normal") - only for caption task.
        """
        pil = load_image(image_input)
        payload = {
            "image_input": image_to_bytes(pil, encoding_format="JPEG"),
            "task": task,
        }
        if prompt:
            payload["prompt"] = prompt
        if task == "caption" and length:
            payload["length"] = length
        return payload

    def postprocess(self, response_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:  # noqa: D401
        """Return *response_data* unchanged – backend already returns JSON."""
        return response_data

    def run(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        task: str,
        prompt: str = "",
        length: str = "normal",
        timeout: float | None = None,
    ) -> Dict[str, Any]:
        """Generate text response from image using Moondream.

        Args:
            image_input (Union[str, Image.Image, np.ndarray]): RGB image.
            task (str): Task type - "vqa" (Visual Question Answering), "caption" (Image Captioning), 
                       "detect" (Object Detection), or "point" (Pointing/Clickable points).
            prompt (str): Text prompt/question about the image (required for vqa, detect, point tasks).
            length (str): Caption length - "short" or "normal" (only for caption task).
            timeout (float | None): Optional HTTP timeout.

        Returns:
            Dict[str, Any]: Backend JSON response containing generated text or structured data.
            - For vqa/caption: {"output": "text response"}
            - For detect: {"output": {"boxes": [...], "scores": [...], "labels": [...]}}
            - For point: {"output": numpy array of (x,y) points}

        Raises:
            ValueError: If image cannot be loaded or required parameters are missing.
            RuntimeError: If no HTTP transport is configured.
            Exception: If the HTTP request fails.

        Examples:
            VQA (Visual Question Answering):
            >>> from grid_cortex_client import CortexClient, ModelType
            >>> import numpy as np
            >>> from PIL import Image
            >>> client = CortexClient()
            >>> image = np.array(Image.open("path/to/kitchen.jpg"))
            >>> result = client.run(ModelType.MOONDREAM, image_input=image, task="vqa", prompt="How many cups are on the table?")
            >>> print(result["output"])  # Text answer

            Image Captioning:
            >>> result = client.run(ModelType.MOONDREAM, image_input=image, task="caption", length="short")
            >>> print(result["output"])  # Text caption

            Object Detection:
            >>> result = client.run(ModelType.MOONDREAM, image_input=image, task="detect", prompt="cup, plate, bowl")
            >>> print(result["output"])  # Dict with boxes, scores, labels

            Pointing (clickable points):
            >>> result = client.run(ModelType.MOONDREAM, image_input=image, task="point", prompt="the red cup")
            >>> print(result["output"])  # Numpy array of (x,y) points
        """
        return super().run(
            image_input=image_input,
            task=task,
            prompt=prompt,
            length=length,
            timeout=timeout,
        )
