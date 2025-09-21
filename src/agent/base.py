"""
Base Agent Class for Anonymization
"""

class Agent:
    """Base agent class for anonymization operations"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.memory = None
        self.tools = []
    
    def execute(self, task):
        """Execute a given task"""
        raise NotImplementedError("Subclasses must implement execute method")

class ToolUser:
    """Base class for tool usage"""
    
    def __init__(self):
        self.available_tools = []
    
    def register_tool(self, tool):
        """Register a tool for use"""
        self.available_tools.append(tool)
    
    def use_tool(self, tool_name, *args, **kwargs):
        """Use a specific tool"""
        for tool in self.available_tools:
            if tool.name == tool_name:
                return tool.execute(*args, **kwargs)
        raise ValueError(f"Tool {tool_name} not found")
