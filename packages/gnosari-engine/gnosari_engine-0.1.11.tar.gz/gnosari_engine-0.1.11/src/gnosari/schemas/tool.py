"""
Tool-related schemas for Gnosari AI Teams.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator

from .base import BaseIOSchema


class ToolDefinition(BaseIOSchema):
    """Schema for tool definition."""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    parameters: Dict[str, Any] = Field(description="Tool parameters schema")
    module: Optional[str] = Field(default=None, description="Python module path")
    class_name: Optional[str] = Field(default=None, description="Tool class name")
    version: Optional[str] = Field(default="1.0.0", description="Tool version")


class ToolExecutionRequest(BaseIOSchema):
    """Request schema for tool execution."""
    tool_name: str = Field(description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(description="Tool execution parameters")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Execution context")
    timeout: Optional[int] = Field(default=None, description="Execution timeout in seconds")


class ToolExecutionResponse(BaseIOSchema):
    """Response schema for tool execution."""
    tool_name: str = Field(description="Tool that was executed")
    parameters: Dict[str, Any] = Field(description="Parameters used")
    result: Any = Field(description="Tool execution result")
    status: str = Field(description="Execution status (success, error, timeout)")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: float = Field(description="Execution time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ToolRegistrationRequest(BaseIOSchema):
    """Request schema for registering a tool."""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    module: str = Field(description="Python module containing the tool")
    class_name: str = Field(description="Tool class name")
    parameters_schema: Dict[str, Any] = Field(description="JSON schema for tool parameters")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Tool configuration")
    tags: Optional[List[str]] = Field(default=None, description="Tool tags for categorization")


class ToolInfo(BaseIOSchema):
    """Information about a registered tool."""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    parameters_schema: Dict[str, Any] = Field(description="Tool parameters schema")
    is_available: bool = Field(description="Whether the tool is currently available")
    version: str = Field(description="Tool version")
    tags: List[str] = Field(description="Tool tags")
    usage_count: int = Field(description="Number of times tool has been used")
    last_used: Optional[str] = Field(default=None, description="Last usage timestamp")


class MCPServerConfig(BaseIOSchema):
    """Configuration for MCP servers."""
    name: str = Field(description="MCP server name")
    url: Optional[str] = Field(default=None, description="Server URL for HTTP connections")
    command: Optional[str] = Field(default=None, description="Command for stdio connections")
    connection_type: str = Field(default="sse", description="Connection type (sse, streamable_http, stdio)")
    args: Optional[List[str]] = Field(default=None, description="Command arguments for stdio")
    headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers")
    timeout: int = Field(default=30, description="Connection timeout")
    sse_read_timeout: int = Field(default=30, description="SSE read timeout")
    terminate_on_close: bool = Field(default=True, description="Terminate on connection close")
    client_session_timeout_seconds: int = Field(default=30, description="Client session timeout")


class MCPToolInfo(BaseIOSchema):
    """Information about tools from MCP servers."""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    server_name: str = Field(description="MCP server providing this tool")
    tool_schema: Dict[str, Any] = Field(description="Tool schema")
    is_available: bool = Field(description="Whether the tool is currently available")


class ToolUsageMetrics(BaseIOSchema):
    """Metrics for tool usage."""
    tool_name: str = Field(description="Tool name")
    total_executions: int = Field(description="Total number of executions")
    successful_executions: int = Field(description="Number of successful executions")
    failed_executions: int = Field(description="Number of failed executions")
    avg_execution_time: float = Field(description="Average execution time in seconds")
    last_used: Optional[str] = Field(default=None, description="Last usage timestamp")
    most_common_errors: List[str] = Field(description="Most common error messages")


class ToolRegistry(BaseIOSchema):
    """Schema for tool registry information."""
    builtin_tools: List[ToolInfo] = Field(description="Built-in tools")
    custom_tools: List[ToolInfo] = Field(description="Custom registered tools")
    mcp_tools: List[MCPToolInfo] = Field(description="Tools from MCP servers")
    total_tools: int = Field(description="Total number of available tools")
    registry_version: str = Field(description="Registry version")


class ToolSearchRequest(BaseIOSchema):
    """Request schema for searching tools."""
    query: Optional[str] = Field(default=None, description="Search query")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    category: Optional[str] = Field(default=None, description="Filter by category")
    available_only: bool = Field(default=True, description="Only return available tools")


class ToolSearchResponse(BaseIOSchema):
    """Response schema for tool search."""
    tools: List[ToolInfo] = Field(description="Matching tools")
    total_results: int = Field(description="Total number of results")
    query: Optional[str] = Field(description="Original search query")
    filters_applied: Dict[str, Any] = Field(description="Filters that were applied")


class BulkToolExecutionRequest(BaseIOSchema):
    """Request schema for executing multiple tools."""
    executions: List[ToolExecutionRequest] = Field(description="List of tool executions")
    parallel: bool = Field(default=True, description="Execute tools in parallel")
    stop_on_error: bool = Field(default=False, description="Stop execution if any tool fails")


class BulkToolExecutionResponse(BaseIOSchema):
    """Response schema for bulk tool execution."""
    executions: List[ToolExecutionResponse] = Field(description="Results of each execution")
    total_executions: int = Field(description="Total number of executions")
    successful_executions: int = Field(description="Number of successful executions")
    failed_executions: int = Field(description="Number of failed executions")
    total_execution_time: float = Field(description="Total execution time")
    stopped_early: bool = Field(description="Whether execution was stopped early due to error")