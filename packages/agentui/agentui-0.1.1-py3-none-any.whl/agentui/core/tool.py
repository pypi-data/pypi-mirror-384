from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import uuid


class PortType(Enum):
    """Defines the types of data that can flow between tools"""
    IMAGE = "image"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"
    ARRAY = "array"
    BOOLEAN = "boolean"
    DETECTIONS = "detections"  # PixelFlow Detections object
    ANY = "any"


class Port:
    """Represents an input or output port on a tool"""
    def __init__(self, name: str, port_type: PortType, description: str = ""):
        self.name = name
        self.type = port_type
        self.description = description

    def __repr__(self):
        return f"Port({self.name}: {self.type.value})"


class ToolOutput:
    """Represents an output from a tool"""
    def __init__(self, data: Any, port_type: PortType):
        self.data = data
        self.port_type = port_type

    @property
    def data_type(self) -> str:
        """Backward compatibility"""
        return self.port_type.value


class Tool(ABC):
    """Base class for all agent tools"""

    def __init__(self, tool_id: Optional[str] = None, **kwargs):
        self.id = tool_id or str(uuid.uuid4())
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, ToolOutput] = {}
        self.parameters = kwargs

    @property
    @abstractmethod
    def tool_type(self) -> str:
        """Return the type identifier for this tool"""
        pass

    @property
    @abstractmethod
    def input_ports(self) -> Dict[str, Port]:
        """Return input ports for this tool"""
        pass

    @property
    @abstractmethod
    def output_ports(self) -> Dict[str, Port]:
        """Return output ports for this tool"""
        pass

    @property
    def input_types(self) -> Dict[str, str]:
        """Backward compatibility - return input types as strings"""
        return {name: port.type.value for name, port in self.input_ports.items()}

    @property
    def output_types(self) -> Dict[str, str]:
        """Backward compatibility - return output types as strings"""
        return {name: port.type.value for name, port in self.output_ports.items()}

    def set_input(self, name: str, value: Any, port_type: Union[PortType, str]):
        """Set an input value for this tool"""
        if name not in self.input_ports:
            raise ValueError(f"Tool {self.tool_type} does not accept input '{name}'")

        # Convert string to PortType for backward compatibility
        if isinstance(port_type, str):
            port_type = PortType(port_type)

        expected_port = self.input_ports[name]
        if expected_port.type != PortType.ANY and port_type != expected_port.type:
            raise TypeError(f"Expected input type '{expected_port.type.value}' but got '{port_type.value}'")

        self.inputs[name] = ToolOutput(value, port_type)

    def get_output(self, name: str) -> Optional[ToolOutput]:
        """Get an output value from this tool"""
        return self.outputs.get(name)

    @abstractmethod
    def process(self) -> bool:
        """Execute the tool's processing logic. Returns True if successful."""
        pass

    def process_with_auto_batching(self) -> bool:
        """Process with automatic single/list handling"""
        # Check if any input is a list
        list_inputs = {}
        single_inputs = {}
        max_list_size = 1

        for name, tool_output in self.inputs.items():
            if isinstance(tool_output.data, list):
                list_inputs[name] = tool_output.data
                max_list_size = max(max_list_size, len(tool_output.data))
            else:
                single_inputs[name] = tool_output.data

        if not list_inputs:
            # No list inputs, process normally
            return self.process()

        # Batch processing needed
        batch_results = []
        for i in range(max_list_size):
            # Create temporary inputs for this batch item
            original_inputs = self.inputs.copy()

            for name, value in list_inputs.items():
                index = min(i, len(value) - 1)  # Use last item if list is shorter
                self.inputs[name] = ToolOutput(value[index], self.inputs[name].port_type)

            # Single inputs stay the same
            for name, value in single_inputs.items():
                self.inputs[name] = ToolOutput(value, self.inputs[name].port_type)

            # Process this batch item
            if not self.process():
                self.inputs = original_inputs
                return False

            # Collect outputs for this batch item
            batch_item_outputs = {}
            for output_name, output_value in self.outputs.items():
                batch_item_outputs[output_name] = output_value.data

            batch_results.append(batch_item_outputs)

            # Restore original inputs
            self.inputs = original_inputs

        # Combine batch results into list outputs
        for output_name in self.outputs.keys():
            output_list = [result[output_name] for result in batch_results]
            self.outputs[output_name] = ToolOutput(output_list, self.outputs[output_name].port_type)

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tool to dictionary"""
        return {
            'id': self.id,
            'type': self.tool_type,
            'parameters': self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tool':
        """Deserialize tool from dictionary"""
        return cls(tool_id=data['id'], **data.get('parameters', {}))

    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for UI"""
        return {
            "type": self.tool_type,
            "inputs": {name: {"type": port.type.value, "description": port.description}
                      for name, port in self.input_ports.items()},
            "outputs": {name: {"type": port.type.value, "description": port.description}
                       for name, port in self.output_ports.items()},
            "parameters": self.parameters
        }


# Simplified base classes

class InputTool(Tool):
    """Base class for input tools - can only output, no input connections"""

    @property
    def input_ports(self) -> Dict[str, Port]:
        return {}  # No inputs allowed

    def can_accept_input(self, port_name: str) -> bool:
        """Input tools cannot accept any inputs"""
        return False


class Connection:
    """Represents a connection between two tools"""

    def __init__(self, source_id: str, source_output: str, target_id: str, target_input: str):
        self.source_id = source_id
        self.source_output = source_output
        self.target_id = target_id
        self.target_input = target_input

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source_id,
            'sourceHandle': self.source_output,
            'target': self.target_id,
            'targetHandle': self.target_input
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Connection':
        return cls(
            source_id=data['source'],
            source_output=data.get('sourceHandle', 'image'),  # Default to 'image'
            target_id=data['target'],
            target_input=data.get('targetHandle', 'image')   # Default to 'image'
        )
