"""Grasp model handler."""
import base64
import gzip
import io
import logging
from typing import Any, Dict

import numpy as np

from .base_model import BaseModel

logger = logging.getLogger(__name__)

def pack_npz(**arrays) -> bytes:
    """Pack numpy arrays into a gzipped-npz."""
    buf = io.BytesIO()
    np.savez_compressed(buf, **arrays)
    return gzip.compress(buf.getvalue())

class GraspModel(BaseModel):
    """
    Model handler for grasp generation models.

    Expected input_data keys for preprocess:
        - 'xyz' (np.ndarray): N_points x 3 point cloud.
        - 'rgb' (np.ndarray): N_points x 3 RGB values.
        - 'seg' (np.ndarray): N_points segmentation labels.
    Output:
        - A dictionary containing 'grasps' and 'confidence'.
    """

    def __init__(self, model_id: str):
        super().__init__(model_id)
        logger.info(f"GraspModel initialized for model_id: '{self.model_id}'")

    def preprocess(self, input_data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Preprocesses the input for a grasp model.

        Args:
            input_data: A dictionary containing the input data. Expected keys:
                'xyz' (np.ndarray): N_points x 3 point cloud.
                'rgb' (np.ndarray): N_points x 3 RGB values.
                'seg' (np.ndarray): N_points segmentation labels.
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary payload for the API request.
        """
        xyz = input_data.get('xyz')
        rgb = input_data.get('rgb')
        seg = input_data.get('seg')

        # --- Start of Edit ---
        # Validate segmentation data: ensure it's non-negative and finite
        valid_mask = (seg >= 0) & np.isfinite(seg)
        if not np.all(valid_mask):
            logger.warning(f"Found invalid segmentation values. Filtering {np.sum(~valid_mask)} points.")
            xyz = xyz[valid_mask]
            rgb = rgb[valid_mask]
            seg = seg[valid_mask]
        # --- End of Edit ---

        if xyz is None or rgb is None or seg is None:
            raise ValueError("'xyz', 'rgb', and 'seg' must be provided in input_data for GraspModel preprocessing.")

        logger.info(f"Preprocessing for GraspModel (model_id='{self.model_id}').")
        
        try:
            # Ensure correct dtypes before packing
            xyz = xyz.astype(np.float32)
            rgb = rgb.astype(np.uint8)
            seg = seg.astype(np.int64)

            packed_bytes = pack_npz(xyz=xyz, rgb=rgb, seg=seg)
            encoded_str = base64.b64encode(packed_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error during grasp input packing/encoding for GraspModel: {e}")
            raise ValueError(f"Failed to pack or encode grasp input: {e}") from e

        payload = {
            "pc_gz_b64": encoded_str,
        }
        
        logger.debug(f"GraspModel Preprocess payload created.")
        return payload

    def postprocess(self, response_data: Dict[str, Any], **kwargs: Any) -> Dict[str, np.ndarray]:
        """
        Postprocesses the grasp model's response.

        Args:
            response_data: The raw JSON response from the API.
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary with 'grasps' and 'confidence' numpy arrays.
        """
        logger.info(f"Postprocessing for GraspModel (model_id='{self.model_id}')")
        try:
            grasps = np.array(response_data["output"])
            confidence = np.array(response_data["confidence"])
            logger.debug(f"GraspModel Postprocess successful for model_id='{self.model_id}'.")
            return {"grasps": grasps, "confidence": confidence}
        except KeyError as e:
            logger.error(f"Postprocessing failed for GraspModel (model_id='{self.model_id}'): Missing key {e}")
            raise ValueError(f"Postprocessing failed, missing key in response: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during postprocessing for GraspModel (model_id='{self.model_id}'): {e}", exc_info=True)
            raise ValueError(f"Unexpected postprocessing error: {e}") from e

    def visualize(self, processed_output: Dict[str, np.ndarray], original_input: Any = None, **kwargs: Any) -> None:
        """
        (Optional) Visualizes the grasps.
        """
        logger.info(f"Visualize called for GraspModel (model_id='{self.model_id}').")
        print("Visualization for GraspModel is not implemented yet.")
        # Here you could add visualization logic, e.g., using Open3D or another library
        # For example:
        # grasps = processed_output.get('grasps')
        # if grasps is not None:
        #     print(f"Visualizing {len(grasps)} grasps.")
        pass
