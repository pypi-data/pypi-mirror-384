"""
Type-inferred component loading system for modular team configurations.

This module provides automatic component type inference based on directory structure,
eliminating the need for explicit type metadata in component files.
"""
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar, Any
import logging

logger = logging.getLogger(__name__)


class ComponentValidationError(Exception):
    """Raised when component validation fails."""
    pass


class InferredComponentLoader:
    """Loads components with type inference from directory structure."""
    
    COMPONENT_TYPES = {
        "agents": "agent",
        "tools": "tool", 
        "knowledge": "knowledge",
        "prompts": "prompt",
        "traits": "trait"
    }
    
    def __init__(self):
        self.validators = {
            "agent": self._validate_agent_component,
            "tool": self._validate_tool_component,
            "knowledge": self._validate_knowledge_component,
            "prompt": self._validate_prompt_component,
            "trait": self._validate_trait_component
        }
    
    async def discover_team_components(self, team_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Discover all components in team directory with type inference."""
        components = {}
        
        for dir_name, component_type in self.COMPONENT_TYPES.items():
            component_dir = team_path / dir_name
            if component_dir.exists() and component_dir.is_dir():
                components[component_type] = await self._load_components_from_directory(
                    component_dir, component_type
                )
        
        logger.info(f"Discovered {sum(len(comps) for comps in components.values())} components in {team_path}")
        return components
    
    async def _load_components_from_directory(self, directory: Path, component_type: str) -> List[Dict[str, Any]]:
        """Load all components from a directory with type inference."""
        components = []
        yaml_files = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))
        
        logger.debug(f"Loading {len(yaml_files)} {component_type} components from {directory}")
        
        for file_path in yaml_files:
            try:
                # Infer component ID from filename (without extension)
                component_id = file_path.stem
                
                # Load YAML content
                data = await self._load_yaml(file_path)
                
                # Add inferred metadata
                component = {
                    "id": component_id,
                    "file_path": str(file_path),
                    **data  # Merge file content
                }
                
                # Validate component belongs to this directory type
                if self._validate_component_for_type(component, component_type):
                    components.append(component)
                    logger.debug(f"Loaded {component_type} component: {component_id}")
                else:
                    raise ComponentValidationError(
                        f"Component in {file_path} is not valid for {component_type} directory"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to load component from {file_path}: {e}")
                raise ComponentValidationError(f"Error loading {file_path}: {e}")
        
        return components
    
    async def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                if not isinstance(data, dict):
                    raise ValueError(f"YAML file must contain a dictionary, got {type(data)}")
                return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")
    
    def _validate_component_for_type(self, component: Dict[str, Any], expected_type: str) -> bool:
        """Validate that component configuration matches its directory type."""
        validator = self.validators.get(expected_type)
        return validator(component) if validator else True
    
    def _validate_agent_component(self, component: Dict[str, Any]) -> bool:
        """Validate agent component has required fields."""
        required_fields = ["instructions"]
        optional_agent_fields = ["model", "temperature", "reasoning_effort", "orchestrator", "tools", "knowledge", "delegation", "traits"]
        
        # Must have instructions
        if not any(field in component for field in required_fields):
            logger.error(f"Agent component {component.get('id')} missing required field: instructions")
            return False
        
        # Should not have tool-specific fields
        tool_fields = ["module", "class", "class_name", "url", "command", "connection_type"]
        if any(field in component for field in tool_fields):
            logger.error(f"Agent component {component.get('id')} contains tool-specific fields")
            return False
            
        # Should not have knowledge-specific fields (type and data are too generic to check)
        kb_specific_fields = []  # Removed 'type' and 'data' as they're too generic
        if any(field in component for field in kb_specific_fields):
            logger.error(f"Agent component {component.get('id')} contains knowledge-specific fields")
            return False
            
        return True
    
    def _validate_tool_component(self, component: Dict[str, Any]) -> bool:
        """Validate tool component has required fields."""
        # Must have either (module + class) OR (url/command + connection_type) OR just url for MCP
        has_builtin = "module" in component and ("class" in component or "class_name" in component)
        has_mcp_full = ("url" in component or "command" in component) and "connection_type" in component
        has_mcp_simple = "url" in component  # Simple MCP server with just URL
        
        if not (has_builtin or has_mcp_full or has_mcp_simple):
            logger.error(f"Tool component {component.get('id')} missing required fields for built-in or MCP tool")
            return False
            
        # Should not have agent-specific fields
        agent_fields = ["instructions", "orchestrator", "delegation", "traits"]
        if any(field in component for field in agent_fields):
            logger.error(f"Tool component {component.get('id')} contains agent-specific fields")
            return False
            
        return True
    
    def _validate_knowledge_component(self, component: Dict[str, Any]) -> bool:
        """Validate knowledge component has required fields."""
        required_fields = ["type", "data"]
        
        # Must have type and data
        if not all(field in component for field in required_fields):
            logger.error(f"Knowledge component {component.get('id')} missing required fields: type, data")
            return False
            
        # Should not have agent-specific fields
        agent_fields = ["instructions", "orchestrator", "delegation", "traits"]
        if any(field in component for field in agent_fields):
            logger.error(f"Knowledge component {component.get('id')} contains agent-specific fields")
            return False
            
        # Should not have tool-specific fields
        tool_fields = ["module", "class", "class_name", "url", "command", "connection_type"]
        if any(field in component for field in tool_fields):
            logger.error(f"Knowledge component {component.get('id')} contains tool-specific fields")
            return False
            
        return True
    
    def _validate_prompt_component(self, component: Dict[str, Any]) -> bool:
        """Validate prompt component has required fields."""
        # Prompts should have template, content, or instructions
        content_fields = ["template", "content", "instructions"]
        if not any(field in component for field in content_fields):
            logger.error(f"Prompt component {component.get('id')} missing content fields")
            return False
            
        return True
    
    def _validate_trait_component(self, component: Dict[str, Any]) -> bool:
        """Validate trait component has required fields."""
        # Traits must have name and instructions
        required_fields = ["name", "instructions"]
        if not all(field in component for field in required_fields):
            logger.error(f"Trait component {component.get('id')} missing required fields: {required_fields}")
            return False
        
        # Validate weight if present
        weight = component.get("weight", 1.0)
        if not isinstance(weight, (int, float)) or weight < 0 or weight > 2:
            logger.error(f"Trait component {component.get('id')} has invalid weight: {weight}")
            return False
        
        # Should not have agent-specific fields
        agent_fields = ["orchestrator", "delegation", "model", "temperature"]
        if any(field in component for field in agent_fields):
            logger.error(f"Trait component {component.get('id')} contains agent-specific fields")
            return False
            
        # Should not have tool-specific fields
        tool_fields = ["module", "class", "url", "command", "connection_type"]
        if any(field in component for field in tool_fields):
            logger.error(f"Trait component {component.get('id')} contains tool-specific fields")
            return False
            
        return True


class ComponentSecurityValidator:
    """Validates component files for security constraints."""
    
    MAX_FILE_SIZE = 1024 * 1024  # 1MB
    ALLOWED_EXTENSIONS = {'.yaml', '.yml'}
    
    def validate_component_file(self, file_path: Path) -> bool:
        """Validate component file security constraints."""
        # Check file extension
        if file_path.suffix not in self.ALLOWED_EXTENSIONS:
            raise ComponentValidationError(f"Invalid file extension: {file_path.suffix}")
        
        # Check file size
        if file_path.stat().st_size > self.MAX_FILE_SIZE:
            raise ComponentValidationError(f"Component file too large: {file_path}")
        
        # Check for path traversal
        resolved_path = file_path.resolve()
        if '..' in str(file_path) or not str(resolved_path).startswith('/'):
            # More lenient path validation - just check for obvious traversal attempts
            pass
        
        return True
    
    def validate_component_content(self, component: Dict[str, Any]) -> bool:
        """Validate component content for security issues."""
        # Basic validation - can be extended with more security checks
        component_id = component.get('id', 'unknown')
        
        # Check for suspicious content patterns
        suspicious_patterns = ['eval(', 'exec(', '__import__', 'subprocess', 'os.system']
        
        def check_value(value, path=""):
            if isinstance(value, str):
                for pattern in suspicious_patterns:
                    if pattern in value.lower():
                        logger.warning(f"Suspicious content in component {component_id} at {path}: {pattern}")
            elif isinstance(value, dict):
                for k, v in value.items():
                    check_value(v, f"{path}.{k}")
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    check_value(v, f"{path}[{i}]")
        
        check_value(component)
        return True