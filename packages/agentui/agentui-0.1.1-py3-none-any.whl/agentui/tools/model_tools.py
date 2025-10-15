"""
ML Model nodes for object detection, segmentation, and other computer vision tasks.

This module integrates the Mozo library for model serving with PixelFlow for
unified detection output format.

See mozo.md and pixelflow.md for detailed documentation.
"""

from typing import Dict, Any, Optional
import numpy as np
from PIL import Image
import cv2

from ..core.tool import Tool, ToolOutput, Port, PortType

# Try to import mozo library
try:
    from mozo.manager import ModelManager
    MOZO_AVAILABLE = True
except ImportError:
    MOZO_AVAILABLE = False
    print("Warning: mozo library not installed. Install with: pip install mozo")

# Try to import pixelflow library
try:
    import pixelflow as pf
    PIXELFLOW_AVAILABLE = True
except ImportError:
    PIXELFLOW_AVAILABLE = False
    print("Warning: pixelflow library not installed. Install with: pip install pixelflow")


class MozoModelToolBase(Tool):
    """
    Base class for nodes using the Mozo model serving library.

    Provides:
    - Shared ModelManager instance (singleton pattern)
    - Image format conversion helpers (PIL ↔ numpy)
    - Model lifecycle management
    """

    # Shared ModelManager instance across all model nodes
    _model_manager: Optional[ModelManager] = None

    def __init__(self, node_id: Optional[str] = None, **kwargs):
        super().__init__(node_id, **kwargs)

        if not MOZO_AVAILABLE:
            raise ImportError(
                "Mozo model nodes require the mozo library. "
                "Install with: pip install mozo"
            )

        if not PIXELFLOW_AVAILABLE:
            raise ImportError(
                "Mozo model nodes require the pixelflow library. "
                "Install with: pip install pixelflow"
            )

        # Initialize shared model manager if not already done
        if MozoModelToolBase._model_manager is None:
            MozoModelToolBase._model_manager = ModelManager()

    @property
    def model_manager(self) -> ModelManager:
        """Get the shared model manager instance"""
        return MozoModelToolBase._model_manager

    @staticmethod
    def pil_to_cv2(image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV numpy array (BGR format)"""
        # Convert to RGB first (in case it's RGBA, L, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert to numpy array (RGB)
        np_image = np.array(image)

        # Convert RGB to BGR for OpenCV
        cv2_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

        return cv2_image

    @staticmethod
    def cv2_to_pil(image: np.ndarray) -> Image.Image:
        """Convert OpenCV numpy array (BGR) to PIL Image"""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_image)

        return pil_image

    @classmethod
    def cleanup_models(cls, inactive_seconds: int = 600) -> int:
        """
        Clean up inactive models to free memory.

        Args:
            inactive_seconds: Unload models not used in this many seconds

        Returns:
            Number of models unloaded
        """
        if cls._model_manager is not None:
            return cls._model_manager.cleanup_inactive_models(inactive_seconds)
        return 0

    @classmethod
    def unload_all_models(cls) -> int:
        """Unload all loaded models"""
        if cls._model_manager is not None:
            return cls._model_manager.unload_all_models()
        return 0


class ObjectDetection(MozoModelToolBase):
    """
    Universal object detection supporting multiple frameworks via Mozo.

    Supports:
    - Detectron2: Faster R-CNN, RetinaNet, and other detection architectures
    - YOLOv8: Nano, Small, Medium, Large, XLarge variants

    Output format: PixelFlow Detections (unified format for all frameworks)

    Note: Model variants are defined in registry.py NODE_METADATA (single source of truth)
    """

    @property
    def tool_type(self) -> str:
        return "ObjectDetection"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image (PIL Image)")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "detections": Port("detections", PortType.DETECTIONS, "Detected objects (PixelFlow Detections)")
        }

    def process(self) -> bool:
        try:
            # Get input image
            if "image" not in self.inputs:
                print(f"{self.node_type}: No input image")
                return False

            pil_image = self.inputs["image"].data

            # Get parameters
            framework = self.parameters.get('framework', 'detectron2')
            model_variant = self.parameters.get('model_variant', 'faster_rcnn_R_50_FPN_3x')
            confidence_threshold = self.parameters.get('confidence_threshold', 0.5)
            device = self.parameters.get('device', 'cpu')

            # Convert PIL Image to OpenCV format (BGR numpy array)
            cv2_image = self.pil_to_cv2(pil_image)

            # Get model from Mozo (lazy loads if needed)
            print(f"{self.node_type}: Loading model '{framework}/{model_variant}' on {device}...")
            model = self.model_manager.get_model(framework, model_variant)

            # Run prediction - returns PixelFlow Detections
            print(f"{self.node_type}: Running inference...")
            detections = model.predict(cv2_image)

            # Filter by confidence threshold
            if confidence_threshold > 0.0:
                detections = detections.filter_by_confidence(confidence_threshold)

            print(f"{self.node_type}: Found {len(detections)} detections")

            # Set outputs
            # Note: We output the PixelFlow Detections object directly
            # It can be converted to dict/json later if needed
            self.outputs["detections"] = ToolOutput(detections, PortType.DETECTIONS)

            return True

        except Exception as e:
            print(f"{self.node_type} error: {e}")
            import traceback
            traceback.print_exc()
            return False


class InstanceSegmentation(MozoModelToolBase):
    """
    Universal instance segmentation supporting multiple frameworks via Mozo.

    Supports:
    - Detectron2: Mask R-CNN variants (R50, R101, X101)
    - YOLOv8: Segmentation variants (yolov8n-seg, yolov8s-seg, etc.)

    Output includes:
    - Bounding boxes
    - Segmentation masks (binary masks or polygons)
    - Class labels and confidence scores

    Output format: PixelFlow Detections (unified format for all frameworks)

    Note: Model variants are defined in registry.py NODE_METADATA (single source of truth)
    """

    @property
    def tool_type(self) -> str:
        return "InstanceSegmentation"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image (PIL Image)")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "detections": Port("detections", PortType.DETECTIONS, "Detected objects with masks (PixelFlow Detections)")
        }

    def process(self) -> bool:
        try:
            # Get input image
            if "image" not in self.inputs:
                print(f"{self.node_type}: No input image")
                return False

            pil_image = self.inputs["image"].data

            # Get parameters
            framework = self.parameters.get('framework', 'detectron2')
            model_variant = self.parameters.get('model_variant', 'mask_rcnn_R_50_FPN_3x')
            confidence_threshold = self.parameters.get('confidence_threshold', 0.5)
            device = self.parameters.get('device', 'cpu')

            # Convert PIL Image to OpenCV format
            cv2_image = self.pil_to_cv2(pil_image)

            # Get model from Mozo
            print(f"{self.node_type}: Loading model '{framework}/{model_variant}' on {device}...")
            model = self.model_manager.get_model(framework, model_variant)

            # Run prediction
            print(f"{self.node_type}: Running inference...")
            detections = model.predict(cv2_image)

            # Filter by confidence
            if confidence_threshold > 0.0:
                detections = detections.filter_by_confidence(confidence_threshold)

            # Count detections with masks
            mask_count = sum(1 for det in detections if det.masks)
            print(f"{self.node_type}: Found {len(detections)} detections ({mask_count} with masks)")

            # Set outputs
            self.outputs["detections"] = ToolOutput(detections, PortType.DETECTIONS)

            return True

        except Exception as e:
            print(f"{self.node_type} error: {e}")
            import traceback
            traceback.print_exc()
            return False


class DepthEstimation(MozoModelToolBase):
    """
    Monocular depth estimation using Depth Anything models via Mozo.

    Outputs:
    - Depth map as grayscale image (PIL Image)
    - Normalized depth values (0=near, 255=far)

    Available models:
    - small: Fast, lower memory (~350MB)
    - base: Balanced speed/accuracy (~1.3GB)
    - large: Highest accuracy (~1.3GB)
    """

    @property
    def tool_type(self) -> str:
        return "DepthEstimation"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image (PIL Image)")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "depth_map": Port("depth_map", PortType.IMAGE, "Depth map (grayscale PIL Image)")
        }

    def process(self) -> bool:
        try:
            # Get input image
            if "image" not in self.inputs:
                print(f"{self.node_type}: No input image")
                return False

            pil_image = self.inputs["image"].data

            # Get parameters
            model_variant = self.parameters.get('model_variant', 'small')
            device = self.parameters.get('device', 'cpu')

            # Convert PIL Image to OpenCV format
            cv2_image = self.pil_to_cv2(pil_image)

            # Get model from Mozo
            print(f"{self.node_type}: Loading model 'depth_anything/{model_variant}' on {device}...")
            model = self.model_manager.get_model('depth_anything', model_variant)

            # Run prediction - returns PIL Image (depth map)
            print(f"{self.node_type}: Running inference...")
            depth_map = model.predict(cv2_image)

            print(f"{self.node_type}: Depth map generated (size: {depth_map.size})")

            # Set output
            self.outputs["depth_map"] = ToolOutput(depth_map, PortType.IMAGE)

            return True

        except Exception as e:
            print(f"{self.node_type} error: {e}")
            import traceback
            traceback.print_exc()
            return False


# Export available model nodes
MODEL_TOOLS = [
    ObjectDetection,
    InstanceSegmentation,
    DepthEstimation
] if MOZO_AVAILABLE and PIXELFLOW_AVAILABLE else []
