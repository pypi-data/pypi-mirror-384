"""
Coding Agent Tool - Integrates with external coding agents like cursor-agent
"""

import logging
import asyncio
import json
import subprocess
import os
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import SyncTool


class CodingAgentArgs(BaseModel):
    """Arguments for the coding agent tool."""
    message: str = Field(..., description="The message/prompt to send to the coding agent")
    
    class Config:
        extra = "forbid"


class CodingAgentTool(SyncTool):
    """Coding Agent Tool that interfaces with external coding agents like cursor-agent."""
    
    def __init__(self, 
                 agent_name: str = "cursor",
                 timeout: int = 300,  # 5 minutes default
                 working_directory: Optional[str] = None):
        """Initialize the coding agent tool.
        
        Args:
            agent_name: Name of the coding agent to use (currently only 'cursor' supported)
            timeout: Timeout for agent execution in seconds
            working_directory: Working directory for agent execution (defaults to current directory)
        """
        # Call parent constructor
        super().__init__(
            name="coding_agent",
            description=f"Execute coding tasks using {agent_name} agent",
            input_schema=CodingAgentArgs
        )
        
        self.agent_name = agent_name.lower()
        self.timeout = timeout
        self.working_directory = working_directory
        
        # Validate agent name
        if self.agent_name not in ["cursor"]:
            raise ValueError(f"Unsupported agent: {agent_name}. Supported agents: cursor")
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Create the FunctionTool
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=CodingAgentArgs.model_json_schema(),
            on_invoke_tool=self._run_coding_agent
        )
    
    def _get_agent_command(self, message: str) -> list[str]:
        """Get the command to execute for the specific agent.
        
        Args:
            message: The message to send to the agent
            
        Returns:
            List of command parts
        """
        if self.agent_name == "cursor":
            return ["cursor-agent", "--force", "-p", message]
        else:
            raise ValueError(f"Unsupported agent: {self.agent_name}")
    
    async def _execute_agent_command(self, command: list[str], ctx: RunContextWrapper[Any]) -> tuple[int, str, str]:
        """Execute the coding agent command and monitor output in real-time.
        
        Args:
            command: Command to execute
            ctx: Run context wrapper for streaming updates
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            self.logger.info(f"🔧 Executing coding agent: {' '.join(command)}")
            
            # Determine working directory
            cwd = self.working_directory if self.working_directory else os.getcwd()
            self.logger.info(f"📁 Working directory: {cwd}")
            
            # Start the process
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Monitor output in real-time
            stdout_lines = []
            stderr_lines = []
            completed = False
            current_content = ""
            
            async def read_stream(stream, lines_list, stream_name):
                """Read from a stream line by line and stream cursor-agent messages."""
                nonlocal completed, current_content
                
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    
                    line_text = line.decode('utf-8', errors='replace').rstrip()
                    lines_list.append(line_text)
                    
                    # Try to parse as JSON and handle cursor-agent messages
                    if line_text.strip():
                        try:
                            json_data = json.loads(line_text)
                            message_type = json_data.get("type")
                            
                            if message_type == "system":
                                subtype = json_data.get("subtype")
                                if subtype == "init":
                                    # Log initialization message
                                    session_id = json_data.get("session_id", "unknown")
                                    cwd = json_data.get("cwd", "unknown")
                                    model = json_data.get("model", "unknown")
                                    self.logger.info(f"🚀 Cursor agent initialized (session: {session_id[-8:]}, model: {model})")
                                    print(f"\n🚀 Cursor agent initialized (session: {session_id[-8:]}, model: {model})\n")
                                        
                            elif message_type == "user":
                                # Log user message
                                user_msg = json_data.get("message", {})
                                content = user_msg.get("content", [])
                                if content and isinstance(content, list):
                                    text = content[0].get("text", "") if content[0].get("type") == "text" else ""
                                    if text:
                                        self.logger.info(f"👤 User: {text}")
                                        print(f"\n👤 User: {text}\n")
                                        # Add separator line for better readability
                                        print("🤖 Assistant: ", end="", flush=True)
                                            
                            elif message_type == "assistant":
                                # Stream assistant response chunks
                                assistant_msg = json_data.get("message", {})
                                content = assistant_msg.get("content", [])
                                if content and isinstance(content, list):
                                    text = content[0].get("text", "") if content[0].get("type") == "text" else ""
                                    if text:
                                        current_content += text
                                        # Print the incremental content with proper formatting
                                        print(text, end='', flush=True)
                                            
                            elif message_type == "result":
                                # Handle completion
                                subtype = json_data.get("subtype")
                                if subtype == "success":
                                    self.logger.info("✅ Cursor agent completed successfully")
                                    result_text = json_data.get("result", "")
                                    print(f"\n\n✅ Task completed successfully")
                                    completed = True
                                    break
                                    
                        except json.JSONDecodeError:
                            # Not JSON, might be plain text output
                            if stream_name == "STDOUT" and line_text:
                                self.logger.debug(f"Plain output: {line_text}")
                                # Format plain text output with proper spacing
                                print(f"\n📄 {line_text}")
                            elif stream_name == "STDERR" and line_text:
                                # Handle stderr output
                                self.logger.warning(f"Error output: {line_text}")
                                print(f"\n⚠️ {line_text}")
            
            # Create tasks for reading both streams
            stdout_task = asyncio.create_task(
                read_stream(process.stdout, stdout_lines, "STDOUT")
            )
            stderr_task = asyncio.create_task(
                read_stream(process.stderr, stderr_lines, "STDERR")
            )
            
            # Wait for process completion or timeout
            try:
                # Wait for both stream reading tasks and process completion
                await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task, process.wait()),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                self.logger.error(f"❌ Coding agent timeout after {self.timeout} seconds")
                print(f"\n\n❌ Timeout: Process exceeded {self.timeout} seconds")
                process.kill()
                await process.wait()
                return -1, "", f"Process timed out after {self.timeout} seconds"
            
            # Get final output
            stdout_text = "\n".join(stdout_lines)
            stderr_text = "\n".join(stderr_lines)
            
            if process.returncode == 0:
                self.logger.info(f"✅ Coding agent completed successfully")
            else:
                self.logger.warning(f"⚠️ Coding agent completed with exit code: {process.returncode}")
            
            return process.returncode, stdout_text, stderr_text
            
        except Exception as e:
            self.logger.error(f"❌ Coding agent execution failed: {str(e)}")
            print(f"\n\n❌ Execution Error: {str(e)}")
            return -1, "", str(e)
    
    def _extract_result_from_output(self, stdout: str) -> str:
        """Extract the final result from the coding agent output.
        
        Args:
            stdout: Standard output from the coding agent
            
        Returns:
            Extracted result or full output if no result found
        """
        try:
            # Look for the last result message in JSON format
            lines = stdout.strip().split('\n')
            for line in reversed(lines):
                line = line.strip()
                if line:
                    try:
                        json_data = json.loads(line)
                        if (json_data.get("type") == "result" and 
                            json_data.get("subtype") == "success" and 
                            "result" in json_data):
                            return json_data["result"]
                    except json.JSONDecodeError:
                        continue
            
            # If no result found, return the full output
            return stdout
            
        except Exception as e:
            self.logger.warning(f"Failed to extract result: {str(e)}")
            return stdout
    
    async def _run_coding_agent(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Execute the coding agent.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing CodingAgentArgs
            
        Returns:
            Coding agent response as string
        """
        try:
            # Parse arguments
            parsed_args = CodingAgentArgs.model_validate_json(args)
            
            self.logger.info(f"🤖 CODING AGENT STARTED - {self.agent_name.upper()}")
            self.logger.debug(f"Message: {parsed_args.message}")
            
            # Get agent command
            command = self._get_agent_command(parsed_args.message)
            
            # Execute the command
            exit_code, stdout, stderr = await self._execute_agent_command(command, ctx)
            
            # Process results
            if exit_code == 0:
                result = self._extract_result_from_output(stdout)
                self.logger.info(f"✅ CODING AGENT SUCCESSFUL")
                return f"Coding agent completed successfully.\n\nFinal result:\n{result}"
            else:
                error_msg = stderr if stderr else "Unknown error"
                self.logger.error(f"❌ CODING AGENT FAILED - Exit code: {exit_code}")
                return f"Coding agent failed with exit code {exit_code}.\n\nError details:\n{error_msg}"
                    
        except ValueError as e:
            self.logger.error(f"❌ CODING AGENT FAILED with validation error: {str(e)}")
            return f"Validation error: {str(e)}"
        except Exception as e:
            self.logger.error(f"❌ CODING AGENT FAILED with unexpected error: {str(e)}")
            return f"Unexpected error: {str(e)}"
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool instance
        """
        return self.tool


def get_default_coding_agent_tool() -> FunctionTool:
    """Get a default coding agent tool instance.
    
    Returns:
        FunctionTool instance
    """
    return CodingAgentTool().get_tool()