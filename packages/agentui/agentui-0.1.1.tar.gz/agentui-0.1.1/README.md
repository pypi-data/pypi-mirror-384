# AgentUI

Visual workflow builder for computer vision and AI. Create image processing pipelines by connecting tools in a drag-and-drop interface, then export and run them programmatically.

**Part of the [Datamarkin](https://datamarkin.com) ecosystem** - Built on [PixelFlow](https://pixelflow.datamarkin.com) and [Mozo](https://mozo.datamarkin.com) for production-ready computer vision.

## What It Is

AgentUI is a web-first tool builder that lets you:
- **Build visually**: Drag and drop tools on a canvas to create workflows
- **Connect tools**: Wire outputs to inputs with type-safe connections
- **Execute**: Run workflows in the browser and see results instantly
- **Export**: Save workflows as JSON for version control and programmatic execution
- **Integrate**: Use as a Python library in your own applications

Think of it as a visual programming environment for computer vision tasks.

## Quick Start

```bash
# Install
pip install agentui

# Start the server
python -m agentui.api.server

# Open http://localhost:8000 in your browser
```

That's it. The UI is already bundled - no separate build step needed.

## What You Can Build

### ML-Powered Tools
- **Object Detection**: Detect objects using YOLOv8 or Detectron2 (80 COCO classes)
- **Instance Segmentation**: Get pixel-level masks for detected objects
- **Depth Estimation**: Generate depth maps from single images (Depth Anything)

### Image Processing
- **Transforms**: Resize, rotate, flip, crop images
- **Adjustments**: Brightness, contrast, sharpening
- **Effects**: Blur, edge detection, color analysis
- **Blending**: Combine multiple images

### Annotation & Privacy
- **Draw Detections**: Bounding boxes, labels, masks, polygons
- **Privacy Protection**: Blur or pixelate regions automatically
- **Object Tracking**: Track objects across video frames
- **Zone Analysis**: Monitor object presence in defined areas

### Input/Output
- **Load**: Images from files or base64 data
- **Save**: Export processed images to disk
- **Web Display**: Convert images to base64 for browser display

## Usage

### Web Interface

1. **Add tools**: Drag tools from the left palette onto the canvas
2. **Connect**: Click and drag from output ports to input ports
3. **Configure**: Select a tool to edit its parameters in the right panel
4. **Execute**: Click "Run Workflow" to process
5. **View Results**: See outputs in the results panel
6. **Export**: Save your workflow as JSON

### Programmatic Usage

```python
from agentui.core.workflow import Workflow
from agentui.core.registry import registry

# Load a workflow created in the UI
with open('my_workflow.json') as f:
    workflow_json = f.read()

# Execute it
workflow = Workflow.from_json(workflow_json, registry.get_all_types())
results = workflow.execute()

# Access results from terminal tools (tools with no outgoing connections)
for tool_id, result in results.items():
    if result['is_terminal']:
        print(f"Tool {tool_id} outputs:")
        for output_name, output_data in result['outputs'].items():
            print(f"  {output_name}: {type(output_data)}")
```

### Creating Workflows in Code

```python
from agentui.core.workflow import Workflow
from agentui.core.node import Connection
from agentui.nodes.base_nodes import MediaInputNode, ResizeNode, SaveImageNode

# Create tools
input_tool = MediaInputNode(path='input.jpg')
resize_tool = ResizeNode(width=800, height=600)
save_tool = SaveImageNode(path='output.jpg')

# Build workflow
workflow = Workflow()
workflow.add_node(input_tool)
workflow.add_node(resize_tool)
workflow.add_node(save_tool)

# Connect tools
workflow.add_connection(Connection(input_tool.id, "image", resize_tool.id, "image"))
workflow.add_connection(Connection(resize_tool.id, "image", save_tool.id, "image"))

# Execute
results = workflow.execute()
```

## The Datamarkin Ecosystem

AgentUI integrates two powerful libraries:

- **[PixelFlow](https://pixelflow.datamarkin.com)**: Computer vision primitives (annotation, tracking, spatial analysis)
- **[Mozo](https://mozo.datamarkin.com)**: Universal model serving (object detection, segmentation, depth estimation)

These libraries are maintained by the same team and designed to work together seamlessly.

## Development

### UI Development

Only needed if you're modifying the UI:

```bash
cd ui
npm install
npm run dev  # Development server with hot reload at http://localhost:5173

# When done
npm run build  # Builds to ../agentui/static/
```

### Adding Custom Tools

Tools are Python classes that inherit from `Node`:

```python
from agentui.core.node import Node, NodeOutput, Port, PortType

class MyCustomTool(Node):
    @property
    def node_type(self) -> str:
        return "MyCustomTool"

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Input image")}

    @property
    def output_ports(self) -> Dict[str, Port]:
        return {"image": Port("image", PortType.IMAGE, "Output image")}

    def process(self) -> bool:
        image = self.inputs["image"].data
        # Do something with the image
        self.outputs["image"] = NodeOutput(processed_image, PortType.IMAGE)
        return True
```

Tools are automatically discovered by the registry. See `CLAUDE.md` for detailed development guidance.

## Installation for Development

```bash
git clone <repository-url>
cd agentui

# Python setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# Start server
python -m agentui.api.server

# Optional: UI development (only if modifying Svelte code)
cd ui
npm install
npm run build
```

## Roadmap

Future additions will focus on:
- Additional ML models (OCR, classification, keypoint detection)
- Vision-language models (GPT-4V, Claude, Gemini, Qwen-VL)
- Cloud storage integrations (S3, GCS, Azure)
- Advanced tracking and analytics
- Real-time streaming workflows


## Documentation

- **[CLAUDE.md](CLAUDE.md)**: Complete developer guide and architecture documentation
- **[INSTALLATION.md](INSTALLATION.md)**: Detailed installation and troubleshooting
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System design and component details

## Requirements

- Python 3.9+
- Optional: Node.js 18+ (only for UI development)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please check `CLAUDE.md` for development guidelines and architecture overview.

---

**Built by [Datamarkin](https://datamarkin.com)** - Making computer vision accessible through visual workflows.
