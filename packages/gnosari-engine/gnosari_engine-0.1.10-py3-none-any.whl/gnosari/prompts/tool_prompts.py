"""Tool prompt generation for agent system prompts."""

from typing import List, Dict, Any


def get_tools_definition(agent_tools: List[str], tool_manager, real_tool_info: List[Dict] = None) -> List[str]:
    """Generate tool definitions for system prompt injection.
    
    Args:
        agent_tools: List of tool names for the agent
        tool_manager: Tool manager instance for getting tool information
        real_tool_info: Optional list of real tool info dicts extracted from built agent
        
    Returns:
        List of strings containing tool definitions and usage instructions
    """
    # If we have real tool info from the built agent, use that instead
    if real_tool_info:
        return _get_tools_definition_from_real_info(real_tool_info)
    
    # Fallback to the original logic
    if not agent_tools or not tool_manager:
        return []
    
    tool_sections = []
    tool_descriptions = []
    
    # Add tool descriptions
    for tool_name in agent_tools:
        try:
            # Get tool instance from registry
            tool_instance = tool_manager.registry.get(tool_name)
            tool_config = tool_manager.registry.get_config(tool_name)
            
            if tool_instance:
                # Tool name and description are now set from YAML config during registration
                tool_id = tool_config.get('id', tool_name) if tool_config else tool_name
                
                # Format as markdown list item (similar to knowledge bases)
                tool_info = f"- **{tool_instance.name}** (`{tool_id}`): {tool_instance.description}"
                tool_descriptions.append(tool_info)
            else:
                # Fallback if tool not found in registry
                tool_descriptions.append(f"- **{tool_name}**: Tool information unavailable")
                
        except Exception as e:
            # If tool loading fails, add a placeholder
            tool_descriptions.append(f"- **{tool_name}**: Tool information unavailable")

    if tool_descriptions:
        tool_sections.append("## Available Tools")
        tool_sections.extend(tool_descriptions)
        tool_sections.append("")

    return tool_sections


def _get_tools_definition_from_real_info(real_tool_info: List[Dict]) -> List[str]:
    """Generate tool definitions from real tool info extracted from built agent.
    
    Args:
        real_tool_info: List of tool info dicts with name, id, description
        
    Returns:
        List of strings containing tool definitions
    """
    if not real_tool_info:
        return []
    
    tool_sections = []
    tool_descriptions = []
    
    for tool_info in real_tool_info:
        tool_name = tool_info.get('name', 'Unknown Tool')
        tool_id = tool_info.get('id', 'unknown_id')
        tool_description = tool_info.get('description', 'No description available')
        
        # Format as markdown list item (same format as knowledge bases)
        formatted_tool = f"- **{tool_name}** (`{tool_id}`): {tool_description}"
        tool_descriptions.append(formatted_tool)
    
    if tool_descriptions:
        tool_sections.append("## Available Tools")
        tool_sections.extend(tool_descriptions)
        tool_sections.append("")
    
    return tool_sections



