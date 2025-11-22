"""
Model Context Protocol (MCP) Server
====================================

This module implements a Model Context Protocol server for the MediSync system.
MCP allows tools to be registered, managed, and accessed through a standardized interface.

The server manages:
1. Tool Registration - Register available tools
2. Resource Management - Manage tool resources and context
3. Tool Invocation - Execute tools with parameters
4. Response Handling - Format and return tool results
5. Error Management - Handle tool errors gracefully

Author: MediSync Team
Date: November 2025
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum
import json
import uuid
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Types of tools available in MCP."""
    BUILTIN = "builtin"              # Streamlit, Pandas, etc.
    CUSTOM = "custom"                # OCR, KG, custom utilities
    API = "api"                       # External APIs (Gemini, etc.)
    OPEN_API = "open_api"            # Open/standard APIs


class ParameterType(Enum):
    """Parameter types for tool inputs."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class Parameter:
    """Tool parameter definition."""
    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "required": self.required,
            "default": self.default,
        }


@dataclass
class ToolDefinition:
    """Defines a tool in the MCP system."""
    name: str
    description: str
    tool_type: ToolType
    handler: Callable
    parameters: List[Parameter] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "version": self.version,
            "parameters": [p.to_dict() for p in self.parameters],
            "tags": self.tags,
        }


@dataclass
class ToolInvocation:
    """Record of a tool invocation."""
    tool_name: str
    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status: str = "pending"  # pending, executing, completed, failed
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "invocation_id": self.invocation_id,
            "timestamp": self.timestamp,
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
            "status": self.status,
            "duration_ms": self.duration_ms,
        }


class Resource:
    """Represents a resource managed by MCP."""
    
    def __init__(
        self,
        resource_id: str,
        name: str,
        resource_type: str,
        data: Dict[str, Any],
        tags: Optional[List[str]] = None
    ):
        self.resource_id = resource_id
        self.name = name
        self.resource_type = resource_type
        self.data = data
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.accessed_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "name": self.name,
            "type": self.resource_type,
            "data": self.data,
            "tags": self.tags,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
        }


class MCPServer:
    """
    Model Context Protocol Server
    
    Manages tool registration, invocation, and resource lifecycle.
    """
    
    def __init__(self, server_name: str = "MediSync MCP Server", version: str = "1.0.0"):
        """Initialize MCP Server."""
        self.server_name = server_name
        self.version = version
        self.server_id = str(uuid.uuid4())
        
        # Tool management
        self.tools: Dict[str, ToolDefinition] = {}
        self.tool_invocations: List[ToolInvocation] = []
        
        # Resource management
        self.resources: Dict[str, Resource] = {}
        self.resource_types: set = set()
        
        # Tool aliases for backward compatibility
        self.tool_aliases: Dict[str, str] = {}
        
        # Statistics
        self.stats = {
            "total_invocations": 0,
            "successful_invocations": 0,
            "failed_invocations": 0,
            "total_resources": 0,
        }
        
        logger.info(f"MCP Server {server_name} ({self.server_id}) initialized")
    
    def register_tool(
        self,
        tool_def: ToolDefinition,
        aliases: Optional[List[str]] = None
    ) -> str:
        """
        Register a tool with the MCP server.
        
        Args:
            tool_def: Tool definition
            aliases: Alternative names for the tool
            
        Returns:
            Tool name (ID)
        """
        if tool_def.name in self.tools:
            logger.warning(f"Tool {tool_def.name} already registered, overwriting")
        
        self.tools[tool_def.name] = tool_def
        
        # Register aliases
        if aliases:
            for alias in aliases:
                self.tool_aliases[alias] = tool_def.name
                logger.info(f"Tool alias '{alias}' -> '{tool_def.name}'")
        
        logger.info(
            f"Tool registered: {tool_def.name} "
            f"({tool_def.tool_type.value}) - {tool_def.description}"
        )
        
        return tool_def.name
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        if tool_name not in self.tools:
            logger.warning(f"Tool {tool_name} not found")
            return False
        
        del self.tools[tool_name]
        
        # Remove aliases
        aliases_to_remove = [
            alias for alias, name in self.tool_aliases.items()
            if name == tool_name
        ]
        for alias in aliases_to_remove:
            del self.tool_aliases[alias]
        
        logger.info(f"Tool unregistered: {tool_name}")
        return True
    
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get a tool by name (handles aliases)."""
        # Check direct name
        if tool_name in self.tools:
            return self.tools[tool_name]
        
        # Check aliases
        if tool_name in self.tool_aliases:
            actual_name = self.tool_aliases[tool_name]
            return self.tools.get(actual_name)
        
        return None
    
    def list_tools(
        self,
        tool_type: Optional[ToolType] = None,
        tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available tools.
        
        Args:
            tool_type: Filter by tool type
            tag: Filter by tag
            
        Returns:
            List of tool definitions
        """
        tools_list = []
        
        for tool_def in self.tools.values():
            # Filter by type
            if tool_type and tool_def.tool_type != tool_type:
                continue
            
            # Filter by tag
            if tag and tag not in tool_def.tags:
                continue
            
            tools_list.append(tool_def.to_dict())
        
        return tools_list
    
    def invoke_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Invoke a tool with given parameters.
        
        Args:
            tool_name: Name of tool to invoke
            parameters: Tool parameters
            
        Returns:
            Tuple of (success, result_dict)
        """
        import time
        
        # Create invocation record
        invocation = ToolInvocation(tool_name=tool_name, parameters=parameters)
        self.tool_invocations.append(invocation)
        
        try:
            # Get tool
            tool_def = self.get_tool(tool_name)
            if not tool_def:
                error_msg = f"Tool not found: {tool_name}"
                logger.error(error_msg)
                invocation.error = error_msg
                invocation.status = "failed"
                self.stats["failed_invocations"] += 1
                return False, {"error": error_msg}
            
            # Validate parameters
            required_params = {p.name for p in tool_def.parameters if p.required}
            provided_params = set(parameters.keys())
            
            missing = required_params - provided_params
            if missing:
                error_msg = f"Missing required parameters: {missing}"
                logger.error(error_msg)
                invocation.error = error_msg
                invocation.status = "failed"
                self.stats["failed_invocations"] += 1
                return False, {"error": error_msg}
            
            # Execute tool
            invocation.status = "executing"
            start_time = time.time()
            
            result = tool_def.handler(**parameters)
            
            invocation.duration_ms = (time.time() - start_time) * 1000
            invocation.result = result
            invocation.status = "completed"
            
            self.stats["total_invocations"] += 1
            self.stats["successful_invocations"] += 1
            
            logger.info(
                f"Tool {tool_name} invoked successfully "
                f"({invocation.duration_ms:.2f}ms)"
            )
            
            return True, result
            
        except Exception as e:
            invocation.error = str(e)
            invocation.status = "failed"
            self.stats["total_invocations"] += 1
            self.stats["failed_invocations"] += 1
            logger.error(f"Tool invocation failed: {str(e)}")
            return False, {"error": str(e)}
    
    def create_resource(
        self,
        name: str,
        resource_type: str,
        data: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> Resource:
        """
        Create and register a resource.
        
        Args:
            name: Resource name
            resource_type: Type of resource
            data: Resource data
            tags: Tags for organizing resources
            
        Returns:
            Created resource
        """
        resource_id = str(uuid.uuid4())
        resource = Resource(
            resource_id=resource_id,
            name=name,
            resource_type=resource_type,
            data=data,
            tags=tags or []
        )
        
        self.resources[resource_id] = resource
        self.resource_types.add(resource_type)
        self.stats["total_resources"] += 1
        
        logger.info(f"Resource created: {name} ({resource_type})")
        
        return resource
    
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by ID."""
        resource = self.resources.get(resource_id)
        if resource:
            resource.accessed_at = datetime.now().isoformat()
        return resource
    
    def list_resources(
        self,
        resource_type: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available resources.
        
        Args:
            resource_type: Filter by resource type
            tag: Filter by tag
            
        Returns:
            List of resource data
        """
        resources_list = []
        
        for resource in self.resources.values():
            # Filter by type
            if resource_type and resource.resource_type != resource_type:
                continue
            
            # Filter by tag
            if tag and tag not in resource.tags:
                continue
            
            resources_list.append(resource.to_dict())
        
        return resources_list
    
    def delete_resource(self, resource_id: str) -> bool:
        """Delete a resource."""
        if resource_id not in self.resources:
            logger.warning(f"Resource {resource_id} not found")
            return False
        
        del self.resources[resource_id]
        logger.info(f"Resource deleted: {resource_id}")
        return True
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information."""
        return {
            "server_id": self.server_id,
            "server_name": self.server_name,
            "version": self.version,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "statistics": {
                **self.stats,
                "invocation_success_rate": (
                    self.stats["successful_invocations"] / max(self.stats["total_invocations"], 1) * 100
                ),
            },
        }
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export server metrics."""
        return {
            "server_info": self.get_server_info(),
            "tools": self.list_tools(),
            "invocations": [inv.to_dict() for inv in self.tool_invocations[-100:]],  # Last 100
            "resources": self.list_resources(),
        }


# Global MCP Server instance (singleton pattern)
_mcp_instance: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """Get or create the global MCP Server instance."""
    global _mcp_instance
    if _mcp_instance is None:
        _mcp_instance = MCPServer()
    return _mcp_instance


def reset_mcp_server() -> None:
    """Reset the global MCP Server instance (for testing)."""
    global _mcp_instance
    _mcp_instance = None
