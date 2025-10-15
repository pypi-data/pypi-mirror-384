import json
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from .tool import Tool, Connection


class Workflow:
    """Manages and executes an agent workflow of connected tools"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.connections: List[Connection] = []

    def add_tool(self, tool: Tool):
        """Add a tool to the workflow"""
        self.tools[tool.id] = tool

    def add_connection(self, connection: Connection):
        """Add a connection between tools"""
        self.connections.append(connection)

    def get_execution_order(self) -> List[str]:
        """Get tools in topologically sorted order for execution"""
        # Build adjacency list
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        # Initialize all tools with 0 in-degree
        for tool_id in self.tools:
            in_degree[tool_id] = 0

        # Build graph and calculate in-degrees
        for conn in self.connections:
            graph[conn.source_id].append(conn.target_id)
            in_degree[conn.target_id] += 1

        # Topological sort using Kahn's algorithm
        queue = deque([tool_id for tool_id in self.tools if in_degree[tool_id] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.tools):
            raise ValueError("Workflow contains cycles")

        return result

    def get_terminal_tools(self) -> List[str]:
        """Get tools that have no outgoing connections (terminal tools)"""
        tools_with_outgoing = set()
        for conn in self.connections:
            tools_with_outgoing.add(conn.source_id)

        return [tool_id for tool_id in self.tools.keys() if tool_id not in tools_with_outgoing]

    def execute(self) -> Dict[str, Any]:
        """Execute the agent workflow and return results from terminal tools"""
        execution_order = self.get_execution_order()
        all_results = {}
        terminal_tools = self.get_terminal_tools()

        for tool_id in execution_order:
            tool = self.tools[tool_id]

            # Set inputs from connected tools
            for conn in self.connections:
                if conn.target_id == tool_id:
                    source_tool = self.tools[conn.source_id]
                    output = source_tool.get_output(conn.source_output)
                    if output:
                        tool.set_input(conn.target_input, output.data, output.data_type)

            # Execute the tool with auto-batching if available, otherwise use regular process
            if hasattr(tool, 'process_with_auto_batching'):
                success = tool.process_with_auto_batching()
            else:
                success = tool.process()

            if not success:
                raise RuntimeError(f"Tool {tool_id} ({tool.tool_type}) failed to execute")

            all_results[tool_id] = {
                'type': tool.tool_type,
                'outputs': {name: output.data for name, output in tool.outputs.items()},
                'is_terminal': tool_id in terminal_tools
            }

        # Return all results for UI inspection
        return all_results

    def to_json(self) -> str:
        """Export workflow to JSON (Svelte Flow compatible format)"""
        # Keep 'nodes' key for Svelte Flow compatibility
        nodes_data = []
        edges_data = []

        for tool in self.tools.values():
            nodes_data.append({
                'id': tool.id,
                'type': tool.tool_type,
                'data': {
                    'label': tool.tool_type,
                    'parameters': tool.parameters
                },
                'position': {'x': 0, 'y': 0}  # Default position
            })

        for conn in self.connections:
            edges_data.append(conn.to_dict())

        return json.dumps({
            'nodes': nodes_data,  # Svelte Flow format uses 'nodes'
            'edges': edges_data
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str, tool_registry: Dict[str, type]) -> 'Workflow':
        """Create workflow from JSON"""
        data = json.loads(json_str)
        workflow = cls()

        # Create tools from 'nodes' key (Svelte Flow format)
        for node_data in data['nodes']:
            # Check if this is a Svelte Flow format with toolType in data
            if 'data' in node_data and 'toolType' in node_data['data']:
                tool_type = node_data['data']['toolType']
                parameters = node_data['data'].get('parameters', {})
            # Backward compatibility: check for nodeType
            elif 'data' in node_data and 'nodeType' in node_data['data']:
                tool_type = node_data['data']['nodeType']
                parameters = node_data['data'].get('parameters', {})
            else:
                tool_type = node_data['type']
                parameters = node_data.get('parameters', {})

            if tool_type not in tool_registry:
                raise ValueError(f"Unknown tool type: {tool_type}")

            tool_class = tool_registry[tool_type]
            tool = tool_class(tool_id=node_data['id'], **parameters)
            workflow.add_tool(tool)

        # Create connections
        for edge_data in data['edges']:
            connection = Connection.from_dict(edge_data)
            workflow.add_connection(connection)

        return workflow