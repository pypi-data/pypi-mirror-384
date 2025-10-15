"""
PixelFlow Integration nodes for computer vision processing

This module provides agentui nodes that wrap the external pixelflow library
for annotation, tracking, and spatial analysis capabilities.

See PIXELFLOW.md for detailed documentation of the pixelflow library.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image

from ..core.tool import Tool, ToolOutput, Port, PortType

# Try to import pixelflow library
try:
    import pixelflow
    PIXELFLOW_AVAILABLE = True
except ImportError:
    PIXELFLOW_AVAILABLE = False
    print("Warning: pixelflow library not installed. Install with: pip install pixelflow")


class PixelFlowToolBase(Tool):
    """Base class for nodes using the external pixelflow library"""

    def __init__(self, node_id: Optional[str] = None, **kwargs):
        super().__init__(node_id, **kwargs)
        if not PIXELFLOW_AVAILABLE:
            raise ImportError("PixelFlow nodes require the pixelflow library. Install with: pip install pixelflow")


# Annotation Nodes
class DrawBoundingBoxes(PixelFlowToolBase):
    """Draw bounding boxes on image using pixelflow"""

    @property
    def tool_type(self) -> str:
        return "DrawBoundingBoxes"

    @property
    def category(self) -> str:
        return "Annotation"

    @property
    def description(self) -> str:
        return "Draw bounding boxes around detected objects"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image"),
            "detections": Port("detections", PortType.DETECTIONS, "Detection results with boxes")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "annotated_image": Port("annotated_image", PortType.IMAGE, "Image with bounding boxes")
        }


    def process(self) -> bool:
        try:
            if "image" not in self.inputs or "detections" not in self.inputs:
                return False

            image = self.inputs["image"].data
            detections = self.inputs["detections"].data

            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Draw bounding boxes using pixelflow
            # Note: PixelFlow expects BGR format and colors as list of tuples
            color_param = self.parameters.get("color", [255, 0, 0])
            colors = [tuple(color_param)] if color_param else None

            annotated = pixelflow.annotate.box(
                image=image,
                detections=detections,
                thickness=self.parameters.get("thickness", 2),
                colors=colors
            )

            # Convert back to PIL Image if needed
            if isinstance(annotated, np.ndarray):
                annotated = Image.fromarray(annotated)

            self.outputs["annotated_image"] = ToolOutput(annotated, PortType.IMAGE)
            return True

        except Exception as e:
            print(f"DrawBoundingBoxes error: {e}")
            import traceback
            traceback.print_exc()
            return False


class AddLabels(PixelFlowToolBase):
    """Add text labels to detections using pixelflow"""

    @property
    def tool_type(self) -> str:
        return "AddLabels"

    @property
    def category(self) -> str:
        return "Annotation"

    @property
    def description(self) -> str:
        return "Add text labels to detected objects"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image"),
            "detections": Port("detections", PortType.DETECTIONS, "Detection results with labels")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "labeled_image": Port("labeled_image", PortType.IMAGE, "Image with labels")
        }


    def process(self) -> bool:
        try:
            if "image" not in self.inputs or "detections" not in self.inputs:
                return False

            image = self.inputs["image"].data
            detections = self.inputs["detections"].data

            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Add labels using pixelflow
            labeled = pixelflow.annotate.label(
                image=image,
                detections=detections,
                font_size=self.parameters.get("font_size", 12),
                text_color=tuple(self.parameters.get("color", [255, 255, 255])),
                background_color=tuple(self.parameters.get("background_color", [0, 0, 0, 128])),
                position=self.parameters.get("position", "top")
            )

            # Convert back to PIL Image if needed
            if isinstance(labeled, np.ndarray):
                labeled = Image.fromarray(labeled)

            self.outputs["labeled_image"] = ToolOutput(labeled, PortType.IMAGE)
            return True

        except Exception as e:
            print(f"AddLabels error: {e}")
            return False


class BlurRegions(PixelFlowToolBase):
    """Apply blur effect to specified regions using pixelflow"""

    @property
    def tool_type(self) -> str:
        return "BlurRegions"

    @property
    def category(self) -> str:
        return "Privacy"

    @property
    def description(self) -> str:
        return "Blur specified regions for privacy protection"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image"),
            "detections": Port("detections", PortType.DETECTIONS, "Regions to blur")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "blurred_image": Port("blurred_image", PortType.IMAGE, "Image with blurred regions")
        }


    def process(self) -> bool:
        try:
            if "image" not in self.inputs or "detections" not in self.inputs:
                return False

            image = self.inputs["image"].data
            detections = self.inputs["detections"].data

            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Apply blur using pixelflow
            blurred = pixelflow.annotate.blur(
                image=image,
                detections=detections,
                intensity=self.parameters.get("blur_intensity", 15),
                kernel_size=self.parameters.get("kernel_size", 15)
            )

            # Convert back to PIL Image if needed
            if isinstance(blurred, np.ndarray):
                blurred = Image.fromarray(blurred)

            self.outputs["blurred_image"] = ToolOutput(blurred, PortType.IMAGE)
            return True

        except Exception as e:
            print(f"BlurRegions error: {e}")
            return False


class PixelateRegions(PixelFlowToolBase):
    """Apply pixelation effect to specified regions using pixelflow"""

    @property
    def tool_type(self) -> str:
        return "PixelateRegions"

    @property
    def category(self) -> str:
        return "Privacy"

    @property
    def description(self) -> str:
        return "Pixelate specified regions for privacy protection"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image"),
            "detections": Port("detections", PortType.DETECTIONS, "Regions to pixelate")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "pixelated_image": Port("pixelated_image", PortType.IMAGE, "Image with pixelated regions")
        }


    def process(self) -> bool:
        try:
            if "image" not in self.inputs or "detections" not in self.inputs:
                return False

            image = self.inputs["image"].data
            detections = self.inputs["detections"].data

            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Apply pixelation using pixelflow
            pixelated = pixelflow.annotate.pixelate(
                image=image,
                detections=detections,
                pixel_size=self.parameters.get("pixel_size", 20)
            )

            # Convert back to PIL Image if needed
            if isinstance(pixelated, np.ndarray):
                pixelated = Image.fromarray(pixelated)

            self.outputs["pixelated_image"] = ToolOutput(pixelated, PortType.IMAGE)
            return True

        except Exception as e:
            print(f"PixelateRegions error: {e}")
            return False


class DrawMasks(PixelFlowToolBase):
    """Draw segmentation masks using pixelflow"""

    @property
    def tool_type(self) -> str:
        return "DrawMasks"

    @property
    def category(self) -> str:
        return "Annotation"

    @property
    def description(self) -> str:
        return "Draw segmentation masks on image"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image"),
            "detections": Port("detections", PortType.DETECTIONS, "Detection results with masks")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "masked_image": Port("masked_image", PortType.IMAGE, "Image with masks")
        }


    def process(self) -> bool:
        try:
            if "image" not in self.inputs or "detections" not in self.inputs:
                return False

            image = self.inputs["image"].data
            detections = self.inputs["detections"].data

            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Draw masks using pixelflow
            masked = pixelflow.annotate.mask(
                image=image,
                detections=detections,
                opacity=self.parameters.get("opacity", 0.5),
                color=tuple(self.parameters.get("color", [255, 0, 0]))
            )

            # Convert back to PIL Image if needed
            if isinstance(masked, np.ndarray):
                masked = Image.fromarray(masked)

            self.outputs["masked_image"] = ToolOutput(masked, PortType.IMAGE)
            return True

        except Exception as e:
            print(f"DrawMasks error: {e}")
            return False


class DrawPolygons(PixelFlowToolBase):
    """Draw polygon shapes using pixelflow"""

    @property
    def tool_type(self) -> str:
        return "DrawPolygons"

    @property
    def category(self) -> str:
        return "Annotation"

    @property
    def description(self) -> str:
        return "Draw polygon shapes on image"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image"),
            "polygons": Port("polygons", PortType.JSON, "Polygon coordinates")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "annotated_image": Port("annotated_image", PortType.IMAGE, "Image with polygons")
        }


    def process(self) -> bool:
        try:
            if "image" not in self.inputs or "polygons" not in self.inputs:
                return False

            image = self.inputs["image"].data
            polygons = self.inputs["polygons"].data

            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Draw polygons using pixelflow
            annotated = pixelflow.annotate.polygon(
                image=image,
                polygons=polygons,
                thickness=self.parameters.get("thickness", 2),
                color=tuple(self.parameters.get("color", [0, 255, 0])),
                filled=self.parameters.get("filled", False)
            )

            # Convert back to PIL Image if needed
            if isinstance(annotated, np.ndarray):
                annotated = Image.fromarray(annotated)

            self.outputs["annotated_image"] = ToolOutput(annotated, PortType.IMAGE)
            return True

        except Exception as e:
            print(f"DrawPolygons error: {e}")
            return False


# Tracking Node
class ObjectTracker(PixelFlowToolBase):
    """Track objects across frames using pixelflow"""

    def __init__(self, node_id: Optional[str] = None, **kwargs):
        super().__init__(node_id, **kwargs)
        self.tracker = None

    @property
    def tool_type(self) -> str:
        return "ObjectTracker"

    @property
    def category(self) -> str:
        return "Tracking"

    @property
    def description(self) -> str:
        return "Track objects across multiple frames"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Current frame"),
            "detections": Port("detections", PortType.DETECTIONS, "Current frame detections")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "tracked_objects": Port("tracked_objects", PortType.JSON, "Tracked objects with IDs")
        }


    def process(self) -> bool:
        try:
            if "image" not in self.inputs or "detections" not in self.inputs:
                return False

            image = self.inputs["image"].data
            detections = self.inputs["detections"].data

            # Initialize tracker if not already done
            if self.tracker is None:
                self.tracker = pixelflow.tracker.Tracker(
                    max_disappeared=self.parameters.get("max_disappeared", 30),
                    max_distance=self.parameters.get("max_distance", 50)
                )

            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Update tracker with new detections
            tracked_objects = self.tracker.update(detections, image)

            self.outputs["tracked_objects"] = ToolOutput(tracked_objects, PortType.JSON)
            return True

        except Exception as e:
            print(f"ObjectTracker error: {e}")
            return False


# Spatial Analysis Nodes
class ZoneAnalyzer(PixelFlowToolBase):
    """Analyze object presence in defined zones using pixelflow"""

    def __init__(self, node_id: Optional[str] = None, **kwargs):
        super().__init__(node_id, **kwargs)
        self.zones = None

    @property
    def tool_type(self) -> str:
        return "ZoneAnalyzer"

    @property
    def category(self) -> str:
        return "Analysis"

    @property
    def description(self) -> str:
        return "Analyze object presence in predefined zones"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image"),
            "detections": Port("detections", PortType.DETECTIONS, "Object detections"),
            "zone_definitions": Port("zone_definitions", PortType.JSON, "Zone polygon definitions")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "zone_analysis": Port("zone_analysis", PortType.JSON, "Zone occupancy analysis"),
            "annotated_image": Port("annotated_image", PortType.IMAGE, "Image with zones drawn")
        }

    def process(self) -> bool:
        try:
            if "image" not in self.inputs or "detections" not in self.inputs or "zone_definitions" not in self.inputs:
                return False

            image = self.inputs["image"].data
            detections = self.inputs["detections"].data
            zone_definitions = self.inputs["zone_definitions"].data

            # Initialize zones if not already done
            if self.zones is None:
                self.zones = pixelflow.Zones(zone_definitions)

            # Convert PIL Image to numpy array if needed
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Analyze zones
            zone_analysis = self.zones.analyze(detections)

            # Draw zones on image
            annotated = pixelflow.annotate.zones(
                image=image,
                zones=self.zones,
                show_labels=True
            )

            # Convert back to PIL Image if needed
            if isinstance(annotated, np.ndarray):
                annotated = Image.fromarray(annotated)

            self.outputs["zone_analysis"] = ToolOutput(zone_analysis, PortType.JSON)
            self.outputs["annotated_image"] = ToolOutput(annotated, PortType.IMAGE)
            return True

        except Exception as e:
            print(f"ZoneAnalyzer error: {e}")
            return False


# Export available nodes
PIXELFLOW_TOOLS = [
    DrawBoundingBoxes,
    AddLabels,
    BlurRegions,
    PixelateRegions,
    DrawMasks,
    DrawPolygons,
    ObjectTracker,
    ZoneAnalyzer
] if PIXELFLOW_AVAILABLE else []