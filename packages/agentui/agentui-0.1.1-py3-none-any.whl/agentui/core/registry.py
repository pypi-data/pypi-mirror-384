from typing import Dict, List, Type
from ..core.tool import Tool
from ..tools.base_tools import (
    MediaInputTool,
    ResizeTool,
    BlurTool,
    ConvertFormatTool,
    SaveImageTool,
    ImageToBase64Tool
)
from ..tools.cv_tools import (
    RotateTool,
    FlipTool,
    CropTool,
    BrightnessTool,
    ContrastTool,
    SharpenTool,
    EdgeDetectTool,
    DominantColorTool,
    QualityAnalysisTool,
    ObjectDetectTool,
    VisualizeDetectionsTool,
    BlendImagesTool
)

# Import pixelflow tools if available
try:
    from ..tools.pixelflow_tools import PIXELFLOW_TOOLS
    PIXELFLOW_AVAILABLE = True
except ImportError:
    PIXELFLOW_TOOLS = []
    PIXELFLOW_AVAILABLE = False

# Import model tools if available
try:
    from ..tools.model_tools import MODEL_TOOLS
    MODEL_TOOLS_AVAILABLE = True
except ImportError:
    MODEL_TOOLS = []
    MODEL_TOOLS_AVAILABLE = False


class ToolRegistry:
    """Registry for all available tool types"""

    def __init__(self):
        self._tools: Dict[str, Type[Tool]] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register all built-in tool types"""
        # Input/Output tools
        self.register(MediaInputTool)
        self.register(SaveImageTool)
        self.register(ImageToBase64Tool)

        # Basic processing
        self.register(ResizeTool)
        self.register(BlurTool)
        self.register(ConvertFormatTool)

        # Advanced transforms
        self.register(RotateTool)
        self.register(FlipTool)
        self.register(CropTool)

        # Adjustments
        self.register(BrightnessTool)
        self.register(ContrastTool)

        # Filters
        self.register(SharpenTool)
        self.register(EdgeDetectTool)

        # Analysis
        self.register(DominantColorTool)
        self.register(QualityAnalysisTool)

        # Detection (placeholder)
        self.register(ObjectDetectTool)

        # Combiners
        self.register(VisualizeDetectionsTool)
        self.register(BlendImagesTool)

        # PixelFlow tools (if available)
        if PIXELFLOW_AVAILABLE:
            for tool_class in PIXELFLOW_TOOLS:
                self.register(tool_class)

        # Model tools (if available)
        if MODEL_TOOLS_AVAILABLE:
            for tool_class in MODEL_TOOLS:
                self.register(tool_class)

    def register(self, tool_class: Type[Tool]):
        """Register a tool class"""
        tool_instance = tool_class()
        self._tools[tool_instance.tool_type] = tool_class

    def get_tool_class(self, tool_type: str) -> Type[Tool]:
        """Get tool class by type"""
        if tool_type not in self._tools:
            raise ValueError(f"Unknown tool type: {tool_type}")
        return self._tools[tool_type]

    def get_all_types(self) -> Dict[str, Type[Tool]]:
        """Get all registered tool types"""
        return self._tools.copy()

    def get_tool_info(self, tool_type: str) -> Dict[str, any]:
        """Get information about a tool type for the UI"""
        tool_class = self.get_tool_class(tool_type)
        instance = tool_class()

        return {
            'type': tool_type,
            'name': self._get_tool_name(tool_type),
            'inputs': instance.input_types,
            'outputs': instance.output_types,
            'parameters': self._get_default_parameters(tool_type),
            'ports': instance.get_tool_info(),
            'category': self._get_tool_category(tool_type),
            'description': self._get_tool_description(tool_type),
            'parameter_options': self._get_parameter_options(tool_type),
            'required_inputs': self.get_required_inputs(tool_type),
            'optional_inputs': self.get_optional_inputs(tool_type)
        }

    # Unified tool metadata - single source of truth
    TOOL_METADATA = {
        # Input/Output
        'MediaInput': {
            'name': 'Media Input',
            'category': 'Input/Output',
            'description': 'Load media (images, videos) from file or base64 data',
            'required_inputs': [],  # No inputs for input tools
            'optional_inputs': [],
            'parameters': {
                'path': '',
                'data': '',
                'resize_on_load': True,
                'max_width': 1920,
                'max_height': 1080
            }
        },
        'SaveImage': {
            'name': 'Save Image',
            'category': 'Input/Output',
            'description': 'Save image to file',
            'parameters': {
                'path': 'output.jpg',
                'quality': 95,
                'format': 'JPEG',
                'overwrite': True
            },
            'parameter_options': {
                'format': {
                    'type': 'select',
                    'options': [
                        {'value': 'JPEG', 'label': 'JPEG'},
                        {'value': 'PNG', 'label': 'PNG'},
                        {'value': 'WEBP', 'label': 'WebP'},
                        {'value': 'TIFF', 'label': 'TIFF'},
                        {'value': 'BMP', 'label': 'BMP'}
                    ]
                }
            }
        },
        'ImageToBase64': {
            'name': 'Image To Base64',
            'category': 'Input/Output',
            'description': 'Convert image to base64 string',
            'parameters': {
                'format': 'JPEG',
                'quality': 85
            }
        },

        # Transform
        'Resize': {
            'name': 'Resize',
            'category': 'Transform',
            'description': 'Resize image to specified dimensions',
            'required_inputs': ['image'],
            'optional_inputs': [],
            'parameters': {
                'width': 800,
                'height': 600,
                'maintain_aspect_ratio': True,
                'resample_method': 'LANCZOS'
            },
            'parameter_options': {
                'resample_method': {
                    'type': 'select',
                    'options': [
                        {'value': 'LANCZOS', 'label': 'LANCZOS (High Quality)'},
                        {'value': 'BILINEAR', 'label': 'BILINEAR'},
                        {'value': 'NEAREST', 'label': 'NEAREST (Fast)'},
                        {'value': 'BICUBIC', 'label': 'BICUBIC'}
                    ]
                }
            }
        },
        'Rotate': {
            'name': 'Rotate',
            'category': 'Transform',
            'description': 'Rotate image by angle',
            'parameters': {
                'angle': 0,
                'expand': True,
                'fill_color': '#000000',
                'center_x': 0.5,
                'center_y': 0.5
            }
        },
        'Flip': {
            'name': 'Flip',
            'category': 'Transform',
            'description': 'Flip image horizontally/vertically',
            'parameters': {
                'direction': 'horizontal',
                'preserve_original': False
            },
            'parameter_options': {
                'direction': {
                    'type': 'select',
                    'options': [
                        {'value': 'horizontal', 'label': 'Horizontal'},
                        {'value': 'vertical', 'label': 'Vertical'}
                    ]
                }
            }
        },
        'Crop': {
            'name': 'Crop',
            'category': 'Transform',
            'description': 'Crop image to rectangle',
            'parameters': {
                'x': 0,
                'y': 0,
                'width': 100,
                'height': 100,
                'use_percentage': False
            }
        },

        # Adjust
        'Brightness': {
            'name': 'Brightness',
            'category': 'Adjust',
            'description': 'Adjust image brightness',
            'parameters': {
                'factor': 1.0,
                'min_factor': 0.1,
                'max_factor': 3.0
            }
        },
        'Contrast': {
            'name': 'Contrast',
            'category': 'Adjust',
            'description': 'Adjust image contrast',
            'parameters': {
                'factor': 1.0,
                'min_factor': 0.1,
                'max_factor': 3.0
            }
        },
        'ConvertFormat': {
            'name': 'Convert Format',
            'category': 'Adjust',
            'description': 'Convert image color format',
            'parameters': {
                'format': 'RGB',
                'background_color': '#FFFFFF'
            },
            'parameter_options': {
                'format': {
                    'type': 'select',
                    'options': [
                        {'value': 'RGB', 'label': 'RGB'},
                        {'value': 'RGBA', 'label': 'RGBA'},
                        {'value': 'grayscale', 'label': 'Grayscale'},
                        {'value': 'L', 'label': 'Luminance (L)'},
                        {'value': 'CMYK', 'label': 'CMYK'}
                    ]
                }
            }
        },

        # Filter
        'Blur': {
            'name': 'Blur',
            'category': 'Filter',
            'description': 'Apply blur filter to image',
            'parameters': {
                'radius': 2.0,
                'iterations': 1,
                'blur_type': 'gaussian'
            },
            'parameter_options': {
                'blur_type': {
                    'type': 'select',
                    'options': [
                        {'value': 'gaussian', 'label': 'Gaussian'},
                        {'value': 'box', 'label': 'Box Blur'},
                        {'value': 'motion', 'label': 'Motion Blur'},
                        {'value': 'radial', 'label': 'Radial Blur'}
                    ]
                }
            }
        },
        'Sharpen': {
            'name': 'Sharpen',
            'category': 'Filter',
            'description': 'Sharpen image details',
            'parameters': {
                'factor': 1.0,
                'radius': 1.0,
                'threshold': 0
            }
        },
        'EdgeDetect': {
            'name': 'Edge Detect',
            'category': 'Filter',
            'description': 'Detect edges in image',
            'parameters': {
                'method': 'canny',
                'low_threshold': 50,
                'high_threshold': 150,
                'kernel_size': 3
            },
            'parameter_options': {
                'method': {
                    'type': 'select',
                    'options': [
                        {'value': 'canny', 'label': 'Canny'},
                        {'value': 'sobel', 'label': 'Sobel'},
                        {'value': 'laplacian', 'label': 'Laplacian'},
                        {'value': 'prewitt', 'label': 'Prewitt'},
                        {'value': 'roberts', 'label': 'Roberts Cross'}
                    ]
                }
            }
        },

        # Analysis
        'DominantColor': {
            'name': 'Dominant Color',
            'category': 'Analysis',
            'description': 'Extract dominant color from image',
            'parameters': {
                'num_colors': 5,
                'color_format': 'hex',
                'ignore_white': True,
                'ignore_black': True
            }
        },
        'QualityAnalysis': {
            'name': 'Quality Analysis',
            'category': 'Analysis',
            'description': 'Analyze image quality metrics',
            'parameters': {
                'check_blur': True,
                'check_brightness': True,
                'check_contrast': True,
                'blur_threshold': 100
            }
        },

        # Detection
        'ObjectDetect': {
            'name': 'Object Detect',
            'category': 'Detection',
            'description': 'Detect objects in image',
            'parameters': {
                'model': 'yolo',
                'confidence_threshold': 0.5,
                'nms_threshold': 0.4,
                'max_detections': 100
            },
            'parameter_options': {
                'model': {
                    'type': 'select',
                    'options': [
                        {'value': 'yolo', 'label': 'YOLO v5'},
                        {'value': 'ssd', 'label': 'SSD MobileNet'},
                        {'value': 'rcnn', 'label': 'R-CNN'},
                        {'value': 'yolo8', 'label': 'YOLO v8'},
                        {'value': 'detectron2', 'label': 'Detectron2'}
                    ]
                }
            }
        },

        # Combine
        'VisualizeDetections': {
            'name': 'Visualize Detections',
            'category': 'Combine',
            'description': 'Overlay detection results on image',
            'required_inputs': ['image', 'detections'],
            'optional_inputs': [],
            'parameters': {
                'box_color': '#00FF00',
                'box_thickness': 2,
                'label_font_size': 12,
                'show_confidence': True
            }
        },
        'BlendImages': {
            'name': 'Blend Images',
            'category': 'Combine',
            'description': 'Blend two images together',
            'required_inputs': ['background', 'foreground'],
            'optional_inputs': [],
            'parameters': {
                'alpha': 0.5,
                'blend_mode': 'normal',
                'resize_to_match': True
            },
            'parameter_options': {
                'blend_mode': {
                    'type': 'select',
                    'options': [
                        {'value': 'normal', 'label': 'Normal'},
                        {'value': 'multiply', 'label': 'Multiply'},
                        {'value': 'screen', 'label': 'Screen'},
                        {'value': 'overlay', 'label': 'Overlay'},
                        {'value': 'soft_light', 'label': 'Soft Light'},
                        {'value': 'hard_light', 'label': 'Hard Light'}
                    ]
                }
            }
        },

        # PixelFlow tools (external library integration)
        'DrawBoundingBoxes': {
            'name': 'Draw Bounding Boxes',
            'category': 'Annotation',
            'description': 'Draw bounding boxes around detected objects using pixelflow',
            'required_inputs': ['image', 'detections'],
            'optional_inputs': [],
            'parameters': {
                'thickness': 2,
                'color': [255, 0, 0]
            }
        },
        'AddLabels': {
            'name': 'Add Labels',
            'category': 'Annotation',
            'description': 'Add text labels to detected objects using pixelflow',
            'required_inputs': ['image', 'detections'],
            'optional_inputs': [],
            'parameters': {
                'font_size': 12,
                'color': [255, 255, 255],
                'background_color': [0, 0, 0, 128],
                'position': 'top'
            }
        },
        'BlurRegions': {
            'name': 'Blur Regions',
            'category': 'Privacy',
            'description': 'Blur specified regions for privacy protection using pixelflow',
            'required_inputs': ['image', 'detections'],
            'optional_inputs': [],
            'parameters': {
                'blur_intensity': 15,
                'kernel_size': 15
            }
        },
        'PixelateRegions': {
            'name': 'Pixelate Regions',
            'category': 'Privacy',
            'description': 'Pixelate specified regions for privacy protection using pixelflow',
            'required_inputs': ['image', 'detections'],
            'optional_inputs': [],
            'parameters': {
                'pixel_size': 20
            }
        },
        'DrawMasks': {
            'name': 'Draw Masks',
            'category': 'Annotation',
            'description': 'Draw segmentation masks on image using pixelflow',
            'required_inputs': ['image', 'detections'],
            'optional_inputs': [],
            'parameters': {
                'opacity': 0.5,
                'color': [255, 0, 0]
            }
        },
        'DrawPolygons': {
            'name': 'Draw Polygons',
            'category': 'Annotation',
            'description': 'Draw polygon shapes on image using pixelflow',
            'required_inputs': ['image', 'polygons'],
            'optional_inputs': [],
            'parameters': {
                'thickness': 2,
                'color': [0, 255, 0],
                'filled': False
            }
        },
        'ObjectTracker': {
            'name': 'Object Tracker',
            'category': 'Tracking',
            'description': 'Track objects across multiple frames using pixelflow',
            'required_inputs': ['image', 'detections'],
            'optional_inputs': [],
            'parameters': {
                'max_disappeared': 30,
                'max_distance': 50
            }
        },
        'ZoneAnalyzer': {
            'name': 'Zone Analyzer',
            'category': 'Analysis',
            'description': 'Analyze object presence in predefined zones using pixelflow',
            'required_inputs': ['image', 'detections', 'zone_definitions'],
            'optional_inputs': [],
            'parameters': {}
        },

        # Model tools (Mozo integration)
        'ObjectDetection': {
            'name': 'Object Detection',
            'category': 'Models',
            'description': 'Universal object detection supporting multiple frameworks (Detectron2, YOLOv8)',
            'required_inputs': ['image'],
            'optional_inputs': [],
            'parameters': {
                'framework': 'detectron2',
                'model_variant': 'faster_rcnn_R_50_FPN_3x',
                'confidence_threshold': 0.5,
                'device': 'cpu'
            },
            'parameter_options': {
                'framework': {
                    'type': 'select',
                    'options': [
                        {'value': 'detectron2', 'label': 'Detectron2'},
                        {'value': 'yolov8', 'label': 'YOLOv8'}
                    ]
                },
                'model_variant': {
                    'type': 'select',
                    'options': [
                        # Detectron2 models
                        {'value': 'faster_rcnn_R_50_FPN_3x', 'label': 'Faster R-CNN (ResNet-50)', 'framework': 'detectron2'},
                        {'value': 'faster_rcnn_R_101_FPN_3x', 'label': 'Faster R-CNN (ResNet-101)', 'framework': 'detectron2'},
                        {'value': 'retinanet_R_50_FPN_3x', 'label': 'RetinaNet (ResNet-50)', 'framework': 'detectron2'},
                        {'value': 'retinanet_R_101_FPN_3x', 'label': 'RetinaNet (ResNet-101)', 'framework': 'detectron2'},
                        # YOLOv8 models
                        {'value': 'yolov8n', 'label': 'YOLOv8 Nano (fastest)', 'framework': 'yolov8'},
                        {'value': 'yolov8s', 'label': 'YOLOv8 Small', 'framework': 'yolov8'},
                        {'value': 'yolov8m', 'label': 'YOLOv8 Medium (balanced)', 'framework': 'yolov8'},
                        {'value': 'yolov8l', 'label': 'YOLOv8 Large', 'framework': 'yolov8'},
                        {'value': 'yolov8x', 'label': 'YOLOv8 XLarge (most accurate)', 'framework': 'yolov8'}
                    ]
                },
                'device': {
                    'type': 'select',
                    'options': [
                        {'value': 'cpu', 'label': 'CPU'},
                        {'value': 'cuda', 'label': 'CUDA (GPU)'},
                        {'value': 'mps', 'label': 'MPS (Apple Silicon)'}
                    ]
                }
            }
        },
        'InstanceSegmentation': {
            'name': 'Instance Segmentation',
            'category': 'Models',
            'description': 'Universal instance segmentation supporting multiple frameworks (Detectron2, YOLOv8)',
            'required_inputs': ['image'],
            'optional_inputs': [],
            'parameters': {
                'framework': 'detectron2',
                'model_variant': 'mask_rcnn_R_50_FPN_3x',
                'confidence_threshold': 0.5,
                'device': 'cpu'
            },
            'parameter_options': {
                'framework': {
                    'type': 'select',
                    'options': [
                        {'value': 'detectron2', 'label': 'Detectron2'},
                        {'value': 'yolov8', 'label': 'YOLOv8'}
                    ]
                },
                'model_variant': {
                    'type': 'select',
                    'options': [
                        # Detectron2 models
                        {'value': 'mask_rcnn_R_50_FPN_3x', 'label': 'Mask R-CNN (ResNet-50)', 'framework': 'detectron2'},
                        {'value': 'mask_rcnn_R_101_FPN_3x', 'label': 'Mask R-CNN (ResNet-101)', 'framework': 'detectron2'},
                        {'value': 'mask_rcnn_X_101_32x8d_FPN_3x', 'label': 'Mask R-CNN (ResNeXt-101)', 'framework': 'detectron2'},
                        # YOLOv8 segmentation models
                        {'value': 'yolov8n-seg', 'label': 'YOLOv8 Nano Segmentation (fastest)', 'framework': 'yolov8'},
                        {'value': 'yolov8s-seg', 'label': 'YOLOv8 Small Segmentation', 'framework': 'yolov8'},
                        {'value': 'yolov8m-seg', 'label': 'YOLOv8 Medium Segmentation (balanced)', 'framework': 'yolov8'},
                        {'value': 'yolov8l-seg', 'label': 'YOLOv8 Large Segmentation', 'framework': 'yolov8'},
                        {'value': 'yolov8x-seg', 'label': 'YOLOv8 XLarge Segmentation (most accurate)', 'framework': 'yolov8'}
                    ]
                },
                'device': {
                    'type': 'select',
                    'options': [
                        {'value': 'cpu', 'label': 'CPU'},
                        {'value': 'cuda', 'label': 'CUDA (GPU)'},
                        {'value': 'mps', 'label': 'MPS (Apple Silicon)'}
                    ]
                }
            }
        },
        'DepthEstimation': {
            'name': 'Depth Estimation',
            'category': 'Detection',
            'description': 'Estimate depth from single image using Depth Anything',
            'required_inputs': ['image'],
            'optional_inputs': [],
            'parameters': {
                'model_variant': 'small',
                'device': 'cpu'
            },
            'parameter_options': {
                'model_variant': {
                    'type': 'select',
                    'options': [
                        {'value': 'small', 'label': 'Small (Fast, ~350MB)'},
                        {'value': 'base', 'label': 'Base (Balanced, ~1.3GB)'},
                        {'value': 'large', 'label': 'Large (Best Quality, ~1.3GB)'}
                    ]
                },
                'device': {
                    'type': 'select',
                    'options': [
                        {'value': 'cpu', 'label': 'CPU'},
                        {'value': 'cuda', 'label': 'CUDA (GPU)'},
                        {'value': 'mps', 'label': 'MPS (Apple Silicon)'}
                    ]
                }
            }
        }
    }

    def _get_default_parameters(self, tool_type: str) -> Dict[str, any]:
        """Get default parameters for a tool type"""
        return self.TOOL_METADATA.get(tool_type, {}).get('parameters', {})

    def _get_tool_category(self, tool_type: str) -> str:
        """Get category for a tool type"""
        return self.TOOL_METADATA.get(tool_type, {}).get('category', 'Other')


    def _get_tool_description(self, tool_type: str) -> str:
        """Get description for a tool type"""
        return self.TOOL_METADATA.get(tool_type, {}).get('description', 'Process image')

    def _get_tool_name(self, tool_type: str) -> str:
        """Get display name for a tool type"""
        return self.TOOL_METADATA.get(tool_type, {}).get('name', tool_type)

    def _get_parameter_options(self, tool_type: str) -> Dict[str, any]:
        """Get parameter options for a tool type"""
        return self.TOOL_METADATA.get(tool_type, {}).get('parameter_options', {})

    def get_required_inputs(self, tool_type: str) -> List[str]:
        """Get required inputs for a tool type"""
        return self.TOOL_METADATA.get(tool_type, {}).get('required_inputs', [])

    def get_optional_inputs(self, tool_type: str) -> List[str]:
        """Get optional inputs for a tool type"""
        return self.TOOL_METADATA.get(tool_type, {}).get('optional_inputs', [])

    def get_all_tool_info(self) -> Dict[str, Dict[str, any]]:
        """Get information about all tool types"""
        return {tool_type: self.get_tool_info(tool_type) for tool_type in self._tools.keys()}


# Global registry instance
registry = ToolRegistry()