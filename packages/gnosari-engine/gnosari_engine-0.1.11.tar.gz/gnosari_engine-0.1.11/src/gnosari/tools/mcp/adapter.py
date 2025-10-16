"""
MCP tool adapter for integrating MCP server tools with Gnosari.
"""

import json
from typing import Any, Dict
from pydantic import BaseModel

from ..base import BaseTool
from .client import MCPClient


class MCPToolArgs(BaseModel):
    """Generic arguments for MCP tools."""
    pass


class MCPToolAdapter(BaseTool[MCPToolArgs, Any]):
    """
    Adapter that wraps MCP server tools as Gnosari BaseTool instances.
    """
    
    def __init__(self, mcp_client: MCPClient, tool_name: str, tool_description: str, tool_schema: Dict[str, Any]):
        """
        Initialize the MCP tool adapter.
        
        Args:
            mcp_client: MCP client instance
            tool_name: Name of the MCP tool
            tool_description: Description of the MCP tool
            tool_schema: JSON schema for the tool's parameters
        """
        # Create dynamic Pydantic model from schema
        input_schema = self._create_input_schema_from_json(tool_schema)
        
        super().__init__(
            name=tool_name,
            description=tool_description,
            input_schema=input_schema
        )
        
        self.mcp_client = mcp_client
        self.tool_schema = tool_schema
    
    def _create_input_schema_from_json(self, json_schema: Dict[str, Any]) -> type[BaseModel]:
        """
        Create a Pydantic model from JSON schema.
        
        Args:
            json_schema: JSON schema dictionary
            
        Returns:
            Dynamically created Pydantic model class
        """
        # Simple implementation - could be enhanced to handle complex schemas
        from pydantic import create_model
        
        fields = {}
        properties = json_schema.get('properties', {})
        required = json_schema.get('required', [])
        
        for field_name, field_info in properties.items():
            field_type = self._json_type_to_python_type(field_info.get('type', 'string'))
            default_value = ... if field_name in required else None
            fields[field_name] = (field_type, default_value)
        
        return create_model(f"{self.name}Input", **fields)
    
    def _json_type_to_python_type(self, json_type: str) -> type:
        """Map JSON schema types to Python types."""
        type_mapping = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        return type_mapping.get(json_type, str)
    
    async def run(self, input_data: MCPToolArgs) -> Any:
        """
        Execute the MCP tool.
        
        Args:
            input_data: Validated input data
            
        Returns:
            Result from the MCP tool
        """
        # Convert input data to dictionary
        args_dict = input_data.dict() if hasattr(input_data, 'dict') else {}
        
        # Call the MCP tool
        result = await self.mcp_client.call_tool(self.name, args_dict)
        
        return result


def create_mcp_tools_from_server(mcp_client: MCPClient) -> list[MCPToolAdapter]:
    """
    Create MCP tool adapters from an MCP server.
    
    Args:
        mcp_client: Connected MCP client
        
    Returns:
        List of MCP tool adapters
    """
    tools = []
    
    # This would be implemented once we have the MCP protocol details
    # For now, return empty list
    
    return tools