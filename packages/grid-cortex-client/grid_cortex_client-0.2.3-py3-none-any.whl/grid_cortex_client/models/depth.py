\
"""Depth estimation model implementation."""
from io import BytesIO
from typing import Any, Dict, Union, Optional

import numpy as np
from PIL import Image

from .base_model import BaseModel
from ..preprocessing import load_image as general_load_image, image_to_bytes
from ..visualization import visualize_depth_map_rerun as general_visualize_depth_map_rerun


class DepthModel(BaseModel):
    """
    Handles depth estimation tasks by interacting with the Cortex API.
    """

    DEFAULT_MODEL_ID = "depth_estimation_model_id" # Placeholder, user should configure

    def __init__(self, model_id: Optional[str] = None):
        """
        Initializes the DepthModel.

        Args:
            model_id: The specific model ID for depth estimation if different from default.
                      This ID is sent to the generic /run endpoint.
        """
        super().__init__(model_id or self.DEFAULT_MODEL_ID)

    def preprocess(
        self,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepares the image for depth estimation using a dictionary of inputs.

        Args:
            input_data: A dictionary containing the input data. Expected key:
                'image_input' (Union[str, np.ndarray, Image.Image]): Path to the image,
                               a NumPy array, or a PIL Image object. (Required)

        Returns:
            A dictionary payload for the /run endpoint, including the model_id
            and the base64 encoded image.
            
        Raises:
            ValueError: If 'image_input' is not found in input_data.
        """
        image_input = input_data.get('image_input')
        if image_input is None:
            raise ValueError("'image_input' not found in input_data for DepthModel preprocessing.")

        # Use a default encoding format; resizing is not handled here.
        encoding_format = "JPEG" 

        pil_image = general_load_image(image_input)

        # Resizing logic based on target_width/target_height has been removed.
        # If resizing is needed, it should be done before calling the client,
        # or handled by the model server.

        buffered = io.BytesIO()
        pil_image.save(buffered, format=encoding_format)
        encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # The API expects 'image_input' at the top level of the payload for this specific model endpoint.
        # It also seems to expect 'model_id' and other parameters alongside 'image_input',
        # not nested under 'inputs'.
        # The error indicates 'image_input' should be a string.
        payload = {
            "model_id": self.model_id,
            "image_input": encoded_image
            # "encoding_format": encoding_format.lower() # This might be a separate top-level param or not needed
            # Any other model-specific parameters can be added here if they are top-level
        }
        # If the API expects image_base64 directly under image_input without a nested object:
        # payload = {
        #     "model_id": self.model_id,
        #     "image_input": encoded_image, # If image_input is just the base64 string
        #     # "encoding_format": encoding_format.lower() # This might be a separate top-level param
        # }
        # Based on the error "loc": ['body', 'image_input'], 'msg': 'Field required',
        # it implies 'image_input' is a required top-level field.
        # The exact structure of 'image_input' (string vs object) needs to be confirmed
        # if this change doesn't work. For now, assuming it's an object as per common practice.

        return payload

    def postprocess(self, response_data: Dict[str, Any], **kwargs: Any) -> np.ndarray:
        """
        Processes the API response to extract the depth map.

        Args:
            response_data: The JSON response from the API.
            **kwargs: Additional keyword arguments (not used).

        Returns:
            A NumPy array representing the depth map.
        """
        # Handle msgpack response - server returns list[dict] from batch endpoint
        if isinstance(response_data, list):
            response_data = response_data[0]
        
        depth_bytes = response_data.get("output")
        if not isinstance(depth_bytes, (bytes, bytearray, memoryview)):
            raise ValueError("'output' field missing or not bytes")
        
        arr = np.load(BytesIO(depth_bytes), allow_pickle=False)
        return arr.astype(np.float32)

    def visualize(
        self,
        depth_map: np.ndarray,
        original_image: Optional[Union[str, np.ndarray, Image.Image]] = None,
        **kwargs
    ) -> None:
        """
        Visualizes the depth map using Rerun.

        Args:
            depth_map: The depth map (NumPy array) to visualize.
            original_image: Optional original image for context.
            **kwargs: Additional arguments for Rerun visualization.
        """
        try:
            import rerun as rr # type: ignore
            rr.log("depth_map", rr.DepthImage(depth_map))
            if original_image is not None:
                pil_image = general_load_image(original_image)
                rr.log("original_image", rr.Image(np.array(pil_image)))
            print("Depth map visualized. Check your Rerun viewer.")
        except ImportError:
            print("Rerun SDK not installed. Skipping visualization.")
        except Exception as e:
            print(f"Error during Rerun visualization: {e}")

