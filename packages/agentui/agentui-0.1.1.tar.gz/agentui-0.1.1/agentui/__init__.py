__version__ = "0.1.1"
__author__ = "Datamarkin"

from .core.workflow import Workflow
from .core.registry import registry
from .core.tool import Tool, Connection

__all__ = ['Workflow', 'registry', 'Tool', 'Connection']

def hello():
    return "Welcome to AgentUI!"