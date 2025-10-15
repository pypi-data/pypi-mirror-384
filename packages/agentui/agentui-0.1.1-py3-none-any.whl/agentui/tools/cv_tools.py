"""
Computer Vision nodes for advanced image analysis and processing
"""

import os
import json
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from ..core.tool import (
    Tool, ToolOutput, Port, PortType
)
from ..pixelflow import transforms, filters, adjustments


# Transform nodes using PixelFlow
class RotateTool(Tool):
    """Rotate image by specified angle"""

    @property
    def tool_type(self) -> str:
        return "Rotate"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Output image")}

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data
            angle = self.parameters.get('angle', 0)

            rotated_image = transforms.rotate(image, angle)
            self.outputs["image"] = ToolOutput(rotated_image, PortType.IMAGE)
            return True
        except Exception as e:
            print(f"Rotate error: {e}")
            return False


class FlipTool(Tool):
    """Flip image horizontally or vertically"""

    @property
    def tool_type(self) -> str:
        return "Flip"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Output image")}

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data
            direction = self.parameters.get('direction', 'horizontal')

            if direction == 'horizontal':
                flipped_image = transforms.flip_horizontal(image)
            else:
                flipped_image = transforms.flip_vertical(image)

            self.outputs["image"] = ToolOutput(flipped_image, PortType.IMAGE)
            return True
        except Exception as e:
            print(f"Flip error: {e}")
            return False


class CropTool(Tool):
    """Crop image to specified rectangle"""

    @property
    def tool_type(self) -> str:
        return "Crop"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Output image")}

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data
            x = self.parameters.get('x', 0)
            y = self.parameters.get('y', 0)
            width = self.parameters.get('width', 100)
            height = self.parameters.get('height', 100)

            cropped_image = transforms.crop(image, x, y, width, height)
            self.outputs["image"] = ToolOutput(cropped_image, PortType.IMAGE)
            return True
        except Exception as e:
            print(f"Crop error: {e}")
            return False


class BrightnessTool(Tool):
    """Adjust image brightness"""

    @property
    def tool_type(self) -> str:
        return "Brightness"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Output image")}

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data
            factor = self.parameters.get('factor', 1.0)

            bright_image = adjustments.brightness(image, factor)
            self.outputs["image"] = ToolOutput(bright_image, PortType.IMAGE)
            return True
        except Exception as e:
            print(f"Brightness error: {e}")
            return False


class ContrastTool(Tool):
    """Adjust image contrast"""

    @property
    def tool_type(self) -> str:
        return "Contrast"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Output image")}

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data
            factor = self.parameters.get('factor', 1.0)

            contrast_image = adjustments.contrast(image, factor)
            self.outputs["image"] = ToolOutput(contrast_image, PortType.IMAGE)
            return True
        except Exception as e:
            print(f"Contrast error: {e}")
            return False


class SharpenTool(Tool):
    """Sharpen image"""

    @property
    def tool_type(self) -> str:
        return "Sharpen"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Output image")}

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data
            factor = self.parameters.get('factor', 1.0)

            sharp_image = filters.sharpen(image, factor)
            self.outputs["image"] = ToolOutput(sharp_image, PortType.IMAGE)
            return True
        except Exception as e:
            print(f"Sharpen error: {e}")
            return False


class EdgeDetectTool(Tool):
    """Detect edges in image"""

    @property
    def tool_type(self) -> str:
        return "EdgeDetect"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Output image")}

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data
            edge_image = filters.edge_detect(image)
            self.outputs["image"] = ToolOutput(edge_image, PortType.IMAGE)
            return True
        except Exception as e:
            print(f"EdgeDetect error: {e}")
            return False


# Analysis nodes
class DominantColorTool(Tool):
    """Extract dominant color from image"""

    @property
    def tool_type(self) -> str:
        return "DominantColor"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "color": Port("color", PortType.STRING, "Dominant color as hex"),
            "rgb": Port("rgb", PortType.JSON, "RGB values as object")
        }

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data

            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Get dominant color using color quantization
            # Resize for faster processing
            small_image = image.resize((150, 150))
            result = small_image.quantize(colors=1, method=2)
            palette = result.getpalette()

            # Get the dominant color (first color in 1-color palette)
            r, g, b = palette[0], palette[1], palette[2]

            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            rgb_obj = {"r": r, "g": g, "b": b}

            self.outputs["color"] = ToolOutput(hex_color, PortType.STRING)
            self.outputs["rgb"] = ToolOutput(rgb_obj, PortType.JSON)
            return True
        except Exception as e:
            print(f"DominantColor error: {e}")
            return False


class QualityAnalysisTool(Tool):
    """Analyze image quality metrics"""

    @property
    def tool_type(self) -> str:
        return "QualityAnalysis"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {
            "quality_score": Port("quality_score", PortType.NUMBER, "Overall quality score 0-1"),
            "metrics": Port("metrics", PortType.JSON, "Detailed quality metrics")
        }

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data

            # Simple quality metrics (placeholder implementation)
            width, height = image.size
            pixel_count = width * height

            # Convert to grayscale for analysis
            gray = image.convert('L')
            pixels = np.array(gray)

            # Calculate metrics
            sharpness = np.var(pixels)  # Variance as sharpness measure
            brightness = np.mean(pixels) / 255.0
            contrast = np.std(pixels) / 255.0

            # Normalize sharpness (simple heuristic)
            sharpness_score = min(sharpness / 1000.0, 1.0)

            # Calculate overall quality score
            quality_score = (sharpness_score + contrast) / 2.0

            metrics = {
                "sharpness": float(sharpness_score),
                "brightness": float(brightness),
                "contrast": float(contrast),
                "resolution": {"width": width, "height": height},
                "pixel_count": pixel_count
            }

            self.outputs["quality_score"] = ToolOutput(quality_score, PortType.NUMBER)
            self.outputs["metrics"] = ToolOutput(metrics, PortType.JSON)
            return True
        except Exception as e:
            print(f"QualityAnalysis error: {e}")
            return False


# Placeholder detection node (would require ML model)
class ObjectDetectTool(Tool):
    """Detect objects in image using YOLO (placeholder)"""

    @property
    def tool_type(self) -> str:
        return "ObjectDetect"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"detections": Port("detections", PortType.JSON, "Detection results")}

    def process(self) -> bool:
        try:
            if "image" not in self.inputs:
                return False

            image = self.inputs["image"].data

            # Placeholder detection results
            # In real implementation, this would use YOLO or other model
            detections = [
                {
                    "class": "person",
                    "confidence": 0.85,
                    "bbox": [100, 100, 200, 300]  # x, y, width, height
                },
                {
                    "class": "car",
                    "confidence": 0.92,
                    "bbox": [300, 150, 150, 100]
                }
            ]

            self.outputs["detections"] = ToolOutput(detections, PortType.JSON)
            return True
        except Exception as e:
            print(f"ObjectDetect error: {e}")
            return False


# Combiner nodes
class VisualizeDetectionsTool(Tool):
    """Draw detection boxes on image"""

    @property
    def tool_type(self) -> str:
        return "VisualizeDetections"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "image": Port("image", PortType.IMAGE, "Input image"),
            "detections": Port("detections", PortType.JSON, "Detection results")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Annotated image")}

    def process(self) -> bool:
        try:
            if "image" not in self.inputs or "detections" not in self.inputs:
                return False

            image = self.inputs["image"].data.copy()
            detections = self.inputs["detections"].data

            draw = ImageDraw.Draw(image)

            for detection in detections:
                bbox = detection.get("bbox", [0, 0, 0, 0])
                class_name = detection.get("class", "unknown")
                confidence = detection.get("confidence", 0.0)

                x, y, w, h = bbox

                # Draw bounding box
                draw.rectangle([x, y, x + w, y + h], outline="red", width=2)

                # Draw label
                label = f"{class_name}: {confidence:.2f}"
                draw.text((x, y - 20), label, fill="red")

            self.outputs["image"] = ToolOutput(image, PortType.IMAGE)
            return True
        except Exception as e:
            print(f"VisualizeDetections error: {e}")
            return False


class BlendImagesTool(Tool):
    """Blend two images together"""

    @property
    def tool_type(self) -> str:
        return "BlendImages"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {
            "background": Port("background", PortType.IMAGE, "Background image"),
            "foreground": Port("foreground", PortType.IMAGE, "Foreground image")
        }

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Blended image")}

    def process(self) -> bool:
        try:
            if "background" not in self.inputs or "foreground" not in self.inputs:
                return False

            bg = self.inputs["background"].data
            fg = self.inputs["foreground"].data
            alpha = self.parameters.get('alpha', 0.5)

            # Resize foreground to match background
            fg_resized = fg.resize(bg.size)

            # Blend images
            blended = Image.blend(bg, fg_resized, alpha)

            self.outputs["image"] = ToolOutput(blended, PortType.IMAGE)
            return True
        except Exception as e:
            print(f"BlendImages error: {e}")
            return False