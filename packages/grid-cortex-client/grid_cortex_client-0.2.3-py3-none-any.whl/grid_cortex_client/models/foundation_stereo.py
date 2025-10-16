# grid_cortex_client/src/grid_cortex_client/models/foundation_stereo.py
"""FoundationStereo wrapper.

Stereo depth estimation powered by FoundationStereo.

Takes left/right stereo pair + camera intrinsics + baseline and returns
metric depth map.
"""

from __future__ import annotations

from typing import Any, Dict, Union

import numpy as np

from ..preprocessing import load_image, image_to_bytes, encode_nested_bytes
from io import BytesIO
from PIL import Image

from .base_model import BaseModel


class FoundationStereo(BaseModel):
    """Stereo depth estimation (FoundationStereo).

    Preferred usage
    ---------------
    ```pycon
    >>> depth = CortexClient().run(
    ...     "foundationstereo",
    ...     left_image=left_img, right_image=right_img,
    ...     aux_args={"K": K, "baseline": 0.1, "hiera": 0, "valid_iters": 32}
    ... )
    ```
    """

    name: str = "foundationstereo"
    model_id: str = "foundationstereo"

    # ------------------------------------------------------------------
    # BaseModel implementation
    # ------------------------------------------------------------------

    def preprocess(
        self,
        *,
        left_image: Union[str, Image.Image, np.ndarray],
        right_image: Union[str, Image.Image, np.ndarray],
        aux_args: Dict[str, Any] = None,
        # Backward compatibility: accept flat kwargs
        K: np.ndarray = None,
        baseline: float = None,
        hiera: Union[bool, int] = None,
        valid_iters: int = None,
    ) -> Dict[str, Any]:
        """Prepare msgpack payload for FoundationStereo.

        Args:
            left_image: Left stereo image.
            right_image: Right stereo image.
            aux_args: Dict with keys "K" (3x3 intrinsics), "baseline" (float),
                "hiera" (int), "valid_iters" (int).
            K, baseline, hiera, valid_iters: Backward compatibility - flat kwargs.
        """
        left_pil = load_image(left_image)
        right_pil = load_image(right_image)

        left_bytes = image_to_bytes(left_pil)
        right_bytes = image_to_bytes(right_pil)

        # Backward compatibility: build aux_args from flat kwargs if provided
        if aux_args is None:
            aux_args = {}
            if K is not None:
                aux_args["K"] = K
            if baseline is not None:
                aux_args["baseline"] = baseline
            if hiera is not None:
                aux_args["hiera"] = hiera
            if valid_iters is not None:
                aux_args["valid_iters"] = valid_iters

        # Send aux_args directly (msgpack-numpy will handle NumPy arrays)
        return {
            "left_image": left_bytes,
            "right_image": right_bytes,
            "aux_args": aux_args,
        }

    def postprocess(self, response_data: Dict[str, Any], **_: Any) -> np.ndarray:  # noqa: D401
        """Decode msgpack .npy depth bytes to np.ndarray."""
        if isinstance(response_data, list):
            response_data = response_data[0]
        
        depth_bytes = response_data.get("output")
        if not isinstance(depth_bytes, (bytes, bytearray, memoryview)):
            raise ValueError("'output' field missing or not bytes")
        
        arr = np.load(BytesIO(depth_bytes), allow_pickle=False)
        return arr.astype(np.float32)

    def run(
        self,
        left_image: Union[str, Image.Image, np.ndarray],
        right_image: Union[str, Image.Image, np.ndarray],
        aux_args: Dict[str, Any] = None,
        # Backward compatibility: accept flat kwargs
        K: np.ndarray = None,
        baseline: float = None,
        hiera: Union[bool, int] = None,
        valid_iters: int = None,
        timeout: float | None = None,
    ) -> np.ndarray:
        """Estimate depth from stereo pair using FoundationStereo.

        Args:
            left_image (Union[str, Image.Image, np.ndarray]): Left stereo image.
            right_image (Union[str, Image.Image, np.ndarray]): Right stereo image.
            aux_args (Dict[str, Any]): Camera parameters:
                - "K": 3x3 camera intrinsics matrix
                - "baseline": Stereo baseline in meters
                - "hiera": Hierarchy level (0-2)
                - "valid_iters": Number of valid iterations
            timeout (float | None): Optional HTTP timeout.

        Returns:
            np.ndarray: Depth map as numpy array (H, W) with dtype float32.
            Values represent metric depth in meters.

        Raises:
            ValueError: If images cannot be loaded or aux_args is invalid.
            RuntimeError: If no HTTP transport is configured.
            Exception: If the HTTP request fails.

        Examples:
            >>> from grid_cortex_client import CortexClient, ModelType
            >>> import numpy as np
            >>> from PIL import Image
            >>> client = CortexClient()
            >>> K = np.array([[525, 0, 320], [0, 525, 240], [0, 0, 1]], dtype=np.float32)
            >>> aux = {"K": K, "baseline": 0.1, "hiera": 0, "valid_iters": 32}
            >>> left_image = np.array(Image.open("left.jpg"))
            >>> right_image = np.array(Image.open("right.jpg"))
            >>> depth = client.run(ModelType.FOUNDATIONSTEREO, left_image=left_image, right_image=right_image, aux_args=aux)
            >>> print(depth.shape)  # (480, 640)
        """
        return super().run(
            left_image=left_image,
            right_image=right_image,
            aux_args=aux_args,
            K=K,
            baseline=baseline,
            hiera=hiera,
            valid_iters=valid_iters,
            timeout=timeout,
        )
