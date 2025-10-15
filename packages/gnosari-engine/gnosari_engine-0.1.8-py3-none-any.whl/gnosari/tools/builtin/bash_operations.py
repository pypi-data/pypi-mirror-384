"""
Bash Operations Tool - Using OpenAI Agents SDK FunctionTool
"""

import logging
import asyncio
import json
import os
import subprocess
import shlex
from pathlib import Path
from typing import Any, Optional, Literal, List, Dict
from pydantic import BaseModel, Field, field_validator
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import SyncTool


class BashOperationArgs(BaseModel):
    """Arguments for the bash operations tool."""
    command: str = Field(..., description="Bash command to execute")
    working_directory: Optional[str] = Field(default=None, description="Working directory for command execution (relative to base directory)")
    timeout: Optional[int] = Field(default=30, description="Command timeout in seconds (max 300)")
    capture_output: Optional[bool] = Field(default=True, description="Whether to capture and return command output")
    
    @field_validator('command')
    @classmethod
    def validate_command(cls, v):
        """Validate command for basic security."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        
        # Note: Dangerous pattern validation is handled in the tool instance
        # based on unsafe_mode setting. This validator only checks for empty commands.
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout is within reasonable bounds."""
        if v is not None and (v <= 0 or v > 300):
            raise ValueError("Timeout must be between 1 and 300 seconds")
        return v
    
    @field_validator('working_directory')
    @classmethod
    def validate_working_directory(cls, v):
        """Validate working directory path."""
        # Note: Path validation is handled in the tool instance
        # based on unsafe_mode setting. This validator is minimal.
        return v
    
    class Config:
        extra = "forbid"
    


class BashOperationsTool(SyncTool):
    """Configurable Bash Operations Tool that can be used in YAML configurations."""
    
    def __init__(self, 
                 base_directory: str = "./workspace",
                 allowed_commands: Optional[List[str]] = None,
                 blocked_commands: Optional[List[str]] = None,
                 max_output_size: int = 1024 * 1024,  # 1MB default
                 unsafe_mode: bool = False):
        """Initialize the configurable bash operations tool.
        
        Args:
            base_directory: Base directory for command execution
            allowed_commands: List of allowed command prefixes (e.g., ['git', 'npm', 'python']). None allows all.
            blocked_commands: List of blocked command prefixes (e.g., ['rm', 'sudo'])
            max_output_size: Maximum output size in bytes
            unsafe_mode: If True, disables ALL safety mechanisms (dangerous pattern blocking, command filtering, path validation)
        """
        # Call parent constructor first
        super().__init__(
            name="bash_operations",
            description="Execute bash commands in a secure environment",
            input_schema=BashOperationArgs
        )
        
        self.base_directory = Path(base_directory).resolve()
        self.allowed_commands = allowed_commands
        self.blocked_commands = blocked_commands or []
        self.max_output_size = max_output_size
        self.unsafe_mode = unsafe_mode
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Log warning if unsafe mode is enabled
        if self.unsafe_mode:
            self.logger.warning("⚠️ UNSAFE MODE ENABLED - ALL SECURITY MECHANISMS DISABLED")
            self.logger.warning("⚠️ This allows execution of ANY command including potentially destructive ones")
        
        # Ensure base directory exists
        self.base_directory.mkdir(parents=True, exist_ok=True)
        
        # Create the FunctionTool
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=BashOperationArgs.model_json_schema(),
            on_invoke_tool=self._run_bash_operation
        )
    
    def _validate_dangerous_patterns(self, command: str) -> None:
        """Validate command against dangerous patterns (unless in unsafe mode)."""
        # Skip validation in unsafe mode
        if self.unsafe_mode:
            return
            
        # Block potentially dangerous commands
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
            'sudo su',
            'eval',
            'exec',
            '$()',
            '`',
            'curl -s | bash',
            'wget -O - | bash',
            'python -c "import os; os.system',
            'perl -e',
            'ruby -e'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                raise ValueError(f"Command contains potentially dangerous pattern: {pattern}")
    
    def _validate_command_permissions(self, command: str) -> None:
        """Validate command against allowed/blocked lists."""
        # Skip all validation in unsafe mode
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
                raise ValueError(f"Command '{command_name}' is not in allowed commands list: {self.allowed_commands}")
    
    def _validate_working_directory(self, working_dir: Optional[str]) -> Path:
        """Validate and resolve working directory within base directory."""
        if working_dir is None:
            return self.base_directory
        
        # In unsafe mode, allow absolute paths and directory traversal
        if self.unsafe_mode:
            if working_dir.startswith('/'):
                # Absolute path in unsafe mode
                full_path = Path(working_dir).resolve()
            else:
                # Relative path in unsafe mode (still relative to base directory)
                full_path = (self.base_directory / working_dir).resolve()
            
            # Create directory if it doesn't exist
            full_path.mkdir(parents=True, exist_ok=True)
            return full_path
        
        # Safe mode - restrict to base directory
        # Resolve the full path
        full_path = (self.base_directory / working_dir).resolve()
        
        # Ensure the path is within the base directory (security check)
        try:
            full_path.relative_to(self.base_directory)
        except ValueError:
            raise ValueError(f"Working directory '{working_dir}' is outside the allowed base directory")
        
        # Create directory if it doesn't exist
        full_path.mkdir(parents=True, exist_ok=True)
        
        return full_path
    
    async def _run_bash_operation(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Execute the bash command.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing BashOperationArgs
            
        Returns:
            Command execution result as string
        """
        try:
            # Parse arguments
            parsed_args = BashOperationArgs.model_validate_json(args)
            
            # Validate dangerous patterns (unless in unsafe mode)
            self._validate_dangerous_patterns(parsed_args.command)
            
            # Validate command permissions
            self._validate_command_permissions(parsed_args.command)
            
            # Validate and resolve working directory
            working_dir = self._validate_working_directory(parsed_args.working_directory)
            
            self.logger.info(f"🔧 BASH OPERATION - Executing: {parsed_args.command}")
            self.logger.info(f"📁 Working directory: {working_dir}")
            
            return await self._execute_command(
                parsed_args.command,
                working_dir,
                parsed_args.timeout,
                parsed_args.capture_output,
                None
            )
                
        except ValueError as e:
            self.logger.error(f"❌ BASH OPERATION FAILED with validation error: {str(e)}")
            return f"Validation error: {str(e)}"
        except Exception as e:
            self.logger.error(f"❌ BASH OPERATION FAILED with unexpected error: {str(e)}")
            return f"Unexpected error: {str(e)}"
    
    async def _execute_command(self, command: str, working_dir: Path, timeout: int, 
                             capture_output: bool, env_vars: Optional[Dict[str, str]]) -> str:
        """Execute the bash command asynchronously with streaming output."""
        try:
            # Prepare environment
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            # Execute command in a subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=working_dir,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                env=env
            )
            
            # Stream output in real-time if capture_output is enabled
            stdout_lines = []
            stderr_lines = []
            
            if capture_output and process.stdout and process.stderr:
                # Stream both stdout and stderr concurrently
                try:
                    await asyncio.wait_for(
                        self._stream_output(process, stdout_lines, stderr_lines),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    # Kill the process if it times out
                    process.kill()
                    await process.wait()
                    self.logger.error(f"❌ COMMAND TIMEOUT after {timeout} seconds")
                    return f"Error: Command timed out after {timeout} seconds"
            else:
                # Fallback to original behavior if not capturing output
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    self.logger.error(f"❌ COMMAND TIMEOUT after {timeout} seconds")
                    return f"Error: Command timed out after {timeout} seconds"
                
                if stdout:
                    stdout_lines = stdout.decode('utf-8', errors='replace').splitlines()
                if stderr:
                    stderr_lines = stderr.decode('utf-8', errors='replace').splitlines()
            
            # Wait for process to complete
            await process.wait()
            
            # Check total output size
            stdout_text = '\n'.join(stdout_lines)
            stderr_text = '\n'.join(stderr_lines)
            total_output_size = len(stdout_text.encode('utf-8')) + len(stderr_text.encode('utf-8'))
            
            if total_output_size > self.max_output_size:
                self.logger.error(f"❌ OUTPUT TOO LARGE: {total_output_size} bytes")
                return f"Error: Command output too large ({total_output_size} bytes). Maximum allowed: {self.max_output_size} bytes"
            
            # Format result
            result_parts = []
            result_parts.append(f"Command: {command}")
            result_parts.append(f"Working directory: {working_dir.relative_to(self.base_directory)}")
            result_parts.append(f"Exit code: {process.returncode}")
            
            if capture_output:
                if stdout_text:
                    result_parts.append(f"STDOUT:\n{stdout_text}")
                
                if stderr_text:
                    result_parts.append(f"STDERR:\n{stderr_text}")
            
            result = "\n\n".join(result_parts)
            
            if process.returncode == 0:
                self.logger.info(f"✅ COMMAND SUCCESS - Exit code: 0")
            else:
                self.logger.warning(f"⚠️ COMMAND COMPLETED with non-zero exit code: {process.returncode}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ COMMAND EXECUTION FAILED: {str(e)}")
            return f"Error executing command: {str(e)}"
    
    async def _stream_output(self, process, stdout_lines: List[str], stderr_lines: List[str]) -> None:
        """Stream stdout and stderr in real-time, logging each line as it comes."""
        async def read_stdout():
            """Read and log stdout lines in real-time."""
            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_text = line.decode('utf-8', errors='replace').rstrip('\n\r')
                    if line_text:  # Only log non-empty lines
                        self.logger.info(f"📤 STDOUT: {line_text}")
                        stdout_lines.append(line_text)
        
        async def read_stderr():
            """Read and log stderr lines in real-time.""" 
            if process.stderr:
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    line_text = line.decode('utf-8', errors='replace').rstrip('\n\r')
                    if line_text:  # Only log non-empty lines
                        self.logger.warning(f"📤 STDERR: {line_text}")
                        stderr_lines.append(line_text)
        
        # Run both readers concurrently
        await asyncio.gather(read_stdout(), read_stderr())
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool instance
        """
        return self.tool


def get_default_bash_operations_tool() -> FunctionTool:
    """Get a default bash operations tool instance.
    
    Returns:
        FunctionTool instance
    """
    return BashOperationsTool().get_tool()