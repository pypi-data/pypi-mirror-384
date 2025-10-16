"""
AUTO-GENERATED enum of all model IDs for CortexClient.run().

Use with: client.run(ModelType.MODEL_NAME, **kwargs)

Run   python -m grid_cortex_client.tools.generate_enum
whenever you add/remove a model.  Never edit manually – GRID-Rake
needs this file to exist in the source tree so that Griffe can
scrape the rich doc-strings and examples.
"""
from enum import Enum


class ModelType(Enum):
    FOUNDATIONSTEREO = "foundationstereo"
    """
    Estimate depth from stereo pair using FoundationStereo.

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
    GRASPGEN = "graspgen"
    """
    Generate grasps from depth + segmentation using GraspGen.

    Args:
        depth_image (Union[str, Image.Image, np.ndarray]): Depth image.
        seg_image (Union[str, Image.Image, np.ndarray]): Segmentation mask.
        camera_intrinsics (Union[str, np.ndarray]): 3x3 camera intrinsics matrix.
        aux_args (Dict[str, Any]): Auxiliary parameters:
            - "num_grasps": Number of grasps to generate
            - "gripper_config": Gripper configuration string
            - "camera_extrinsics": 4x4 camera extrinsics matrix
        timeout (float | None): Optional HTTP timeout.

    Returns:
        tuple[np.ndarray, np.ndarray]: Tuple of (grasps, confidence):
            - grasps: Array of 4x4 grasp poses (N, 4, 4)
            - confidence: Array of confidence scores (N,)

    Raises:
        ValueError: If images cannot be loaded or parameters are invalid.
        RuntimeError: If no HTTP transport is configured.
        Exception: If the HTTP request fails.

    Examples:
        >>> from grid_cortex_client import CortexClient, ModelType
        >>> import numpy as np
        >>> from PIL import Image
        >>> client = CortexClient()
        >>> K = np.eye(3)
        >>> aux = {"num_grasps": 128, "gripper_config": "single_suction_cup_30mm", "camera_extrinsics": np.eye(4)}
        >>> depth_image = np.load("depth.npy")
        >>> seg_image = np.array(Image.open("seg.png"))
        >>> grasps, conf = client.run(ModelType.GRASPGEN, depth_image=depth_image, seg_image=seg_image, camera_intrinsics=K, aux_args=aux)
        >>> print(f"Generated {len(grasps)} grasps")
    """
    GSAM2 = "gsam2"
    """
    Segment objects in image using text prompt.

    Args:
        image_input (Union[str, Image.Image, np.ndarray]): RGB image as file path, URL, PIL Image, or numpy array.
        prompt (str): Text description of objects to segment.
        box_threshold (float | None): Optional confidence threshold (0.0-1.0) for filtering detections.
        text_threshold (float | None): Optional text confidence threshold (0.0-1.0).
        nms_threshold (float | None): Optional Non-Maximum-Suppression threshold (0.0-1.0).
        timeout (float | None): Optional timeout in seconds for the HTTP request.

    Returns:
        np.ndarray: Binary segmentation mask as numpy array (H, W) with dtype uint8.
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
    MOONDREAM = "moondream"
    """
    Generate text response from image using Moondream.

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
    ONEFORMER = "oneformer"
    """
    Segment an image using OneFormer.

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
    OWLV2 = "owlv2"
    """
    Detect objects in image using text prompt.

    Args:
        image_input (Union[str, Image.Image, np.ndarray]): RGB image as file path, URL, PIL Image, or numpy array.
        prompt (str): Text description of objects to detect.
        box_threshold (float | None): Optional confidence threshold (0.0-1.0) for filtering detections.
        timeout (float | None): Optional timeout in seconds for the HTTP request.

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
    SAM2 = "sam2"
    """
    Segment image with SAM-2 given point/box prompts.

    Args:
        image_input (Union[str, Image.Image, np.ndarray]): RGB image.
        prompts (List[List[int]]): List of ``[x, y]`` pixel coordinates.
        labels (List[int]): 1 = foreground, 0 = background per prompt.
        multimask_output (bool): If *True* returns multiple masks.
        mode (str): Endpoint mode; only "image" currently supported.
        timeout (float | None): HTTP timeout.

    Returns:
        Dict[str, Any]: Backend JSON containing encoded masks / scores.

    Examples:
        >>> from grid_cortex_client import CortexClient, ModelType
        >>> import numpy as np
        >>> from PIL import Image
        >>> client = CortexClient()
        >>> image = np.array(Image.open("cat.jpg"))
        >>> mask_json = client.run(
        ...     ModelType.SAM2,
        ...     image_input=image,
        ...     prompts=[[320, 240]],
        ...     labels=[1],
        ... )
    """
    SAM2VIDEO = "sam2video"
    """
    Not used for stateful models.

    Use :py:meth:`init` to get a WebSocket session instead.

    Examples:
        >>> from grid_cortex_client import CortexClient, ModelType
        >>> client = CortexClient()
        >>> result = client.run(ModelType.SAM2VIDEO, ...)
    """
    ZOEDEPTH = "zoedepth"
    """
    Estimate depth from single RGB image.

    Args:
        image_input (Union[str, Image.Image, np.ndarray]): RGB image as file path, URL, PIL Image, or numpy array.
        timeout (float | None): Optional timeout in seconds for the HTTP request.

    Returns:
        np.ndarray: Depth map as numpy array (H, W) with dtype float32.
            Values represent metric depth in meters.

    Raises:
        ValueError: If image cannot be loaded.
        RuntimeError: If no HTTP transport is configured.
        Exception: If the HTTP request fails.

    Example:
        >>> from grid_cortex_client import CortexClient, ModelType
        >>> import numpy as np
        >>> from PIL import Image
        >>> client = CortexClient()
        >>> image = np.array(Image.open("cat.jpg"))
        >>> depth = client.run(ModelType.ZOEDEPTH, image_input=image)
        >>> print(depth.shape)  # (480, 640)
    """
