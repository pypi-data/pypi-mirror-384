"""Preprocessing helpers.

Utility functions to load images from various sources and encode them as
raw bytes for msgpack transport.
"""

import io
import logging
import os
from typing import Union, Any
import requests  # Add requests import

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_FORMATS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")


def load_image(image_input: Union[str, Image.Image, np.ndarray]) -> Image.Image:
    """Return a Pillow RGB image from multiple input types.

    Args:
        image_input: File path, URL, ``PIL.Image`` or NumPy array.

    Returns:
        Pillow image in RGB mode.
    """
    if isinstance(image_input, str):
        # Check if it's a URL
        if image_input.startswith(("http://", "https://")):
            try:
                logger.debug(f"Fetching image from URL: {image_input}")
                response = requests.get(image_input, timeout=10)
                response.raise_for_status()  # Raise an exception for bad status codes
                img_bytes = io.BytesIO(response.content)
                return Image.open(img_bytes).convert("RGB")
            except requests.exceptions.RequestException as e:
                raise IOError(
                    f"Failed to fetch image from URL {image_input}: {e}"
                ) from e
            except Exception as e:
                raise IOError(
                    f"Failed to load image from URL {image_input} after fetching: {e}"
                ) from e
        # Otherwise, assume it's a local file path
        elif not os.path.exists(image_input):
            raise FileNotFoundError(f"Image path does not exist: {image_input}")
        if not image_input.lower().endswith(SUPPORTED_IMAGE_FORMATS):
            raise ValueError(
                f"Unsupported image format: {image_input}. Supported: {SUPPORTED_IMAGE_FORMATS}"
            )
        try:
            return Image.open(image_input).convert("RGB")
        except Exception as e:
            raise IOError(f"Failed to load image from path {image_input}: {e}") from e
    elif isinstance(image_input, Image.Image):
        return image_input.convert("RGB")
    elif isinstance(image_input, np.ndarray):
        try:
            return Image.fromarray(image_input).convert("RGB")
        except Exception as e:
            raise ValueError(f"Failed to convert numpy array to PIL Image: {e}") from e
    raise TypeError(
        f"Unsupported image input type: {type(image_input)}. Supported: str, PIL.Image, np.ndarray."
    )


# Legacy base64 helpers removed – use image_to_bytes / array_to_npy_bytes instead

# ---------------------------------------------------------------------------
# MsgPack-friendly helpers (binary transport)
# ---------------------------------------------------------------------------

MSG_ENCODING_FORMAT = "PNG"  # lossless default for binary transport


def image_to_bytes(image: Image.Image, encoding_format: str = MSG_ENCODING_FORMAT) -> bytes:
    """Encode *image* as raw bytes (PNG/JPEG) for msgpack transport.

    Args:
        image: Pillow image.
        encoding_format: "PNG" (default) or "JPEG".

    Returns:
        Encoded image bytes.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("Input must be a PIL Image object.")

    buf = io.BytesIO()
    image.save(buf, format=encoding_format)
    return buf.getvalue()


def array_to_npy_bytes(array: np.ndarray) -> bytes:
    """Serialize NumPy array to raw .npy bytes for msgpack transport."""
    if not isinstance(array, np.ndarray):
        raise TypeError("array must be a NumPy ndarray")
    buf = io.BytesIO()
    # Use allow_pickle=False for security
    np.save(buf, array, allow_pickle=False)
    return buf.getvalue()


def _encode_nested_bytes(element: Any) -> Any:
    """Recursively convert NumPy arrays to .npy bytes for nested structures."""
    if isinstance(element, np.ndarray):
        return array_to_npy_bytes(element)
    elif isinstance(element, dict):
        return {k: _encode_nested_bytes(v) for k, v in element.items()}
    elif isinstance(element, (list, tuple)):
        return [_encode_nested_bytes(v) for v in element]
    else:
        return element


def encode_nested_bytes(data: Any) -> Any:
    """Public wrapper over :pyfunc:`_encode_nested_bytes`."""
    return _encode_nested_bytes(data)
