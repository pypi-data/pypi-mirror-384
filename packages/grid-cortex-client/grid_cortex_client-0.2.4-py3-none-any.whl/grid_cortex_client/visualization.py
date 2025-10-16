# filepath: /home/pranay/GRID/Grid-Cortex-Infra/grid-cortex-client/src/grid_cortex_client/visualization.py
from typing import Any, Optional
import numpy as np
import logging

# visualization.py
logger = logging.getLogger(__name__)

try:
    import rerun as rr

    RERUN_AVAILABLE = True
except ImportError:
    RERUN_AVAILABLE = False
    logger.info("rerun-sdk not installed. Rerun visualization will be disabled.")


def check_rerun_available():
    if not RERUN_AVAILABLE:
        logger.warning("Rerun SDK not installed. Skipping visualization.")
    return RERUN_AVAILABLE


def visualize_depth_map_rerun(
    image_input: Any,
    depth_map: np.ndarray,
    application_id: str = "grid_cortex_client.depth_estimation",
    recording_id: Optional[str] = None,
    log_input_image: bool = True,
):
    """Visualizes an input image and its depth map using Rerun."""
    if not check_rerun_available():
        return

    try:
        logger.info(f"Initializing Rerun: {application_id}")
        rr.init(application_id, recording_id=recording_id)
        rr.spawn(port=9876)  # Default Rerun port

        if log_input_image:
            # Lazy import to avoid potential circular dependency issues if preprocessing grows
            from .preprocessing import load_image

            try:
                pil_image = load_image(image_input)
                rr.log("input_image", rr.Image(np.array(pil_image)))
                logger.info("Logged input image to Rerun.")
            except Exception as e:
                logger.error(f"Failed to log input image to Rerun: {e}")

        rr.log("depth_map", rr.DepthImage(depth_map))
        logger.info(
            "Logged depth map to Rerun. View at Rerun viewer (e.g., http://127.0.0.1:9876)."
        )
    except Exception as e:
        logger.error(f"Error during Rerun visualization: {e}")
