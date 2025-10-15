"""
Enhanced Bash Tool - Supports multiple commands and advanced features
"""

import logging
import asyncio
import json
import os
import subprocess
import shlex
from pathlib import Path
from typing import Any, Optional, Literal, List, Dict, Union
from pydantic import BaseModel, Field, field_validator
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import SyncTool


class BashArgs(BaseModel):
    """Arguments for the enhanced bash tool."""
    # Support both single command and multiple commands
    command: Optional[str] = Field(default=None, description="Single bash command to execute")
    commands: Optional[List[str]] = Field(default=None, description="List of bash commands to execute in sequence")
    
    # Execution options
    working_directory: Optional[str] = Field(default=None, description="Working directory for command execution (relative to base directory)")
    timeout: Optional[int] = Field(default=30, description="Command timeout in seconds (max 300)")
    capture_output: Optional[bool] = Field(default=True, description="Whether to capture and return command output")
    stop_on_error: Optional[bool] = Field(default=True, description="Stop execution on first error when running multiple commands")
    env_vars: Optional[Dict[str, str]] = Field(default=None, description="Additional environment variables for command execution")
    
    @field_validator('command', 'commands')
    @classmethod
    def validate_command_input(cls, v, info):
        """Ensure at least one command input is provided."""
        values = info.data
        if not v and not values.get('command') and not values.get('commands'):
            raise ValueError("Either 'command' or 'commands' must be provided")
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout is within reasonable bounds."""
        if v is not None and (v <= 0 or v > 300):
            raise ValueError("Timeout must be between 1 and 300 seconds")
        return v
    
    class Config:
        extra = "forbid"


class BashTool(SyncTool):
    """Enhanced Bash Tool that supports multiple commands and advanced features."""
    
    def __init__(
        self,
        base_directory: str = "./workspace",
        allowed_commands: Optional[List[str]] = None,
        blocked_commands: Optional[List[str]] = None,
        max_output_size: int = 1024 * 1024,  # 1MB default
        unsafe_mode: bool = False,
        commands: Optional[List[str]] = None,  # Pre-configured commands
        timeout: Optional[int] = 30,  # Default timeout
        env_vars: Optional[Dict[str, str]] = None  # Default environment variables
    ):
        """Initialize the enhanced bash tool.
        
        Args:
            base_directory: Base directory for command execution
            allowed_commands: List of allowed command prefixes (e.g., ['git', 'npm', 'python']). None allows all.
            blocked_commands: List of blocked command prefixes (e.g., ['rm', 'sudo'])
            max_output_size: Maximum output size in bytes
            unsafe_mode: If True, disables ALL safety mechanisms
            commands: Pre-configured list of commands to execute (can be overridden at runtime)
            timeout: Default timeout for commands
            env_vars: Default environment variables
        """
        # Call parent constructor
        super().__init__(
            name="bash",
            description="Execute bash commands with support for multiple commands, environment variables, and command chaining",
            input_schema=BashArgs
        )
        
        self.base_directory = Path(base_directory).resolve()
        self.allowed_commands = allowed_commands
        self.blocked_commands = blocked_commands or []
        self.max_output_size = max_output_size
        self.unsafe_mode = unsafe_mode
        self.default_commands = commands
        self.default_timeout = timeout
        self.default_env_vars = env_vars or {}
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Log warning if unsafe mode is enabled
        if self.unsafe_mode:
            self.logger.warning("⚠️ UNSAFE MODE ENABLED - ALL SECURITY MECHANISMS DISABLED")
        
        # Ensure base directory exists
        self.base_directory.mkdir(parents=True, exist_ok=True)
        
        # Create the FunctionTool
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=BashArgs.model_json_schema(),
            on_invoke_tool=self._run_bash
        )
    
    def _substitute_env_vars(self, command: str) -> str:
        """Substitute environment variables in command."""
        # Expand environment variables in the command
        # This handles ${VAR} and $VAR syntax
        expanded = os.path.expandvars(command)
        return expanded
    
    def _validate_dangerous_patterns(self, command: str) -> None:
        """Validate command against dangerous patterns."""
        if self.unsafe_mode:
            return
        
        dangerous_patterns = [
            'rm -rf /',
            'dd if=',
            'mkfs',
            'fdisk',
            'format',
            'sudo rm',
            '> /dev/',
            'chmod 777',
            'chown root',
            'passwd',
            'su -',
            'sudo su'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                raise ValueError(f"Command contains potentially dangerous pattern: {pattern}")
    
    def _validate_command_permissions(self, command: str) -> None:
        """Validate command against allowed/blocked lists."""
        if self.unsafe_mode:
            return
        
        command_parts = shlex.split(command)
        if not command_parts:
            raise ValueError("Empty command")
        
        command_name = command_parts[0].lower()
        
        # Check blocked commands first
        if self.blocked_commands:
            for blocked in self.blocked_commands:
                if command_name.startswith(blocked.lower()):
                    raise ValueError(f"Command '{command_name}' is blocked")
        
        # Check allowed commands if specified
        if self.allowed_commands:
            allowed = False
            for allowed_cmd in self.allowed_commands:
                if command_name.startswith(allowed_cmd.lower()):
                    allowed = True
                    break
            
            if not allowed:
                raise ValueError(f"Command '{command_name}' is not in allowed commands list")
    
    def _validate_working_directory(self, working_dir: Optional[str]) -> Path:
        """Validate and resolve working directory."""
        if working_dir is None:
            return self.base_directory
        
        # In unsafe mode, allow absolute paths
        if self.unsafe_mode:
            if working_dir.startswith('/'):
                full_path = Path(working_dir).resolve()
            else:
                full_path = (self.base_directory / working_dir).resolve()
            
            full_path.mkdir(parents=True, exist_ok=True)
            return full_path
        
        # Safe mode - restrict to base directory
        full_path = (self.base_directory / working_dir).resolve()
        
        # Ensure the path is within the base directory
        try:
            full_path.relative_to(self.base_directory)
        except ValueError:
            raise ValueError(f"Working directory '{working_dir}' is outside the allowed base directory")
        
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
    
    async def _execute_command(self, command: str, working_dir: Path, timeout: int, 
                               capture_output: bool, env_vars: Dict[str, str]) -> tuple[int, str, str]:
        """Execute a single bash command asynchronously.
        
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Substitute environment variables in command
            expanded_command = self._substitute_env_vars(command)
            
            # Prepare environment
            env = os.environ.copy()
            env.update(self.default_env_vars)  # Apply default env vars
            if env_vars:
                env.update(env_vars)  # Apply runtime env vars
            
            # Log the command
            self.logger.info(f"🔧 Executing: {expanded_command}")
            self.logger.info(f"📁 Working directory: {working_dir}")
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                expanded_command,
                cwd=working_dir,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                env=env
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                self.logger.error(f"❌ Command timeout after {timeout} seconds")
                return -1, "", f"Command timed out after {timeout} seconds"
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # Check output size
            total_size = len(stdout_text.encode('utf-8')) + len(stderr_text.encode('utf-8'))
            if total_size > self.max_output_size:
                self.logger.error(f"❌ Output too large: {total_size} bytes")
                return -1, "", f"Output too large ({total_size} bytes). Maximum: {self.max_output_size}"
            
            if process.returncode == 0:
                self.logger.info(f"✅ Command success - Exit code: 0")
            else:
                self.logger.warning(f"⚠️ Command completed with exit code: {process.returncode}")
            
            return process.returncode, stdout_text, stderr_text
            
        except Exception as e:
            self.logger.error(f"❌ Command execution failed: {str(e)}")
            return -1, "", str(e)
    
    async def _run_bash(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Execute bash commands based on configuration and runtime arguments.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing BashArgs
            
        Returns:
            Command execution results as string
        """
        try:
            # Parse arguments
            parsed_args = BashArgs.model_validate_json(args)
            
            # Determine which commands to run
            if self.default_commands:
                # Use pre-configured commands if available
                commands_to_run = self.default_commands
            elif parsed_args.commands:
                # Use runtime-provided command list
                commands_to_run = parsed_args.commands
            elif parsed_args.command:
                # Single command
                commands_to_run = [parsed_args.command]
            else:
                return "Error: No commands specified"
            
            # Get execution parameters
            working_dir = self._validate_working_directory(parsed_args.working_directory)
            timeout = parsed_args.timeout or self.default_timeout or 30
            capture_output = parsed_args.capture_output
            stop_on_error = parsed_args.stop_on_error
            env_vars = parsed_args.env_vars or {}
            
            # Execute commands
            results = []
            for i, command in enumerate(commands_to_run, 1):
                # Validate command
                self._validate_dangerous_patterns(command)
                self._validate_command_permissions(command)
                
                # Execute command
                exit_code, stdout, stderr = await self._execute_command(
                    command, working_dir, timeout, capture_output, env_vars
                )
                
                # Store result
                result = {
                    "command_number": i,
                    "command": command,
                    "exit_code": exit_code,
                    "stdout": stdout.strip() if stdout else "",
                    "stderr": stderr.strip() if stderr else ""
                }
                results.append(result)
                
                # Check if we should stop on error
                if stop_on_error and exit_code != 0:
                    self.logger.warning(f"Stopping execution due to error in command {i}")
                    break
            
            # Format output
            output_parts = []
            output_parts.append(f"Executed {len(results)} of {len(commands_to_run)} commands")
            output_parts.append(f"Working directory: {working_dir.relative_to(self.base_directory)}")
            
            for result in results:
                output_parts.append(f"\n--- Command {result['command_number']} ---")
                output_parts.append(f"Command: {result['command']}")
                output_parts.append(f"Exit code: {result['exit_code']}")
                
                if capture_output:
                    if result['stdout']:
                        output_parts.append(f"STDOUT:\n{result['stdout']}")
                    if result['stderr']:
                        output_parts.append(f"STDERR:\n{result['stderr']}")
            
            return "\n".join(output_parts)
            
        except ValueError as e:
            self.logger.error(f"❌ Validation error: {str(e)}")
            return f"Validation error: {str(e)}"
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {str(e)}")
            return f"Unexpected error: {str(e)}"
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool instance
        """
        return self.tool


def get_default_bash_tool() -> FunctionTool:
    """Get a default bash tool instance.
    
    Returns:
        FunctionTool instance
    """
    return BashTool().get_tool()