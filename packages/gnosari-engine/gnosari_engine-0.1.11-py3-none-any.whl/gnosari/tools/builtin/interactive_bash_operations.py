"""
Interactive Bash Operations Tool - Using OpenAI Agents SDK FunctionTool
Allows agents to interact with blocking/interactive terminal processes
"""

import logging
import asyncio
import json
import os
import subprocess
import shlex
import time
from pathlib import Path
from typing import Any, Optional, List, Dict, Union
from pydantic import BaseModel, Field, field_validator
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import SyncTool
import threading
import queue

# Global registry for interactive bash tool instances
_interactive_bash_tools_registry = []

class InteractiveBashArgs(BaseModel):
    """Arguments for the interactive bash operations tool."""
    action: str = Field(..., description="Action to perform: 'start_session', 'check_session', 'send_input', 'terminate_session'")
    
    # For start_session
    command: Optional[str] = Field(default=None, description="Bash command to execute (required for start_session)")
    working_directory: Optional[str] = Field(default=None, description="Working directory for command execution")
    
    # For check_session, send_input, terminate_session
    session_id: Optional[str] = Field(default=None, description="Session ID (required for check_session, send_input, terminate_session)")
    
    # For send_input
    input_text: Optional[str] = Field(default=None, description="Text to send to the interactive process")
    special_keys: Optional[List[str]] = Field(default=None, description="Special keys to send (e.g., ['down', 'down', 'enter'])")
    key_sequence: Optional[str] = Field(default=None, description="Raw escape sequence to send (advanced usage)")
    
    # For check_session
    read_timeout: Optional[int] = Field(default=10, description="How long to wait for new output (seconds)")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is one of the supported actions."""
        valid_actions = ['start_session', 'check_session', 'send_input', 'terminate_session']
        if v not in valid_actions:
            raise ValueError(f"Action must be one of: {valid_actions}")
        return v
    
    @field_validator('read_timeout')
    @classmethod
    def validate_read_timeout(cls, v):
        """Validate read timeout is within reasonable bounds."""
        if v is not None and (v <= 0 or v > 300):  # Max 5 minutes for reading
            raise ValueError("Read timeout must be between 1 and 300 seconds")
        return v
    
    def model_post_init(self, __context) -> None:
        """Validate action-specific required fields."""
        if self.action == 'start_session':
            if not self.command or not self.command.strip():
                raise ValueError("Command is required for start_session action")
        
        elif self.action in ['check_session', 'send_input', 'terminate_session']:
            if not self.session_id:
                raise ValueError(f"Session ID is required for {self.action} action")
        
        elif self.action == 'send_input':
            if not (self.input_text or self.special_keys or self.key_sequence):
                raise ValueError("At least one of input_text, special_keys, or key_sequence is required for send_input action")
    
    class Config:
        extra = "forbid"


class InteractiveSession:
    """Represents an interactive bash session that can handle ongoing processes."""
    
    def __init__(self, session_id: str, process: asyncio.subprocess.Process, 
                 working_dir: Path, command: str):
        self.session_id = session_id
        self.process = process
        self.working_dir = working_dir
        self.command = command
        self.created_at = time.time()
        self.last_activity = time.time()
        self.last_check = time.time()
        self.output_buffer = []
        self.new_output_since_check = []  # Output since last check_session
        self.total_output_length = 0
        self.is_waiting_for_input = False
        self.prompt_detected = None
        self.status = "running"  # running, waiting, completed, error
        self._lock = asyncio.Lock()  # Prevent concurrent access
        
    def is_alive(self) -> bool:
        """Check if the process is still running."""
        return self.process.returncode is None
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = time.time()
    
    async def add_output(self, output: str):
        """Add new output to the session."""
        async with self._lock:
            self.output_buffer.append(output)
            self.new_output_since_check.append(output)
            self.total_output_length += len(output)
            self.update_activity()
    
    async def get_new_output_since_check(self) -> str:
        """Get output that's new since last check and clear the buffer."""
        async with self._lock:
            new_output = ''.join(self.new_output_since_check)
            self.new_output_since_check = []
            self.last_check = time.time()
            return new_output
    
    def get_recent_output(self, max_chars: int = 2000) -> str:
        """Get recent output (for context)."""
        full_output = ''.join(self.output_buffer)
        if len(full_output) <= max_chars:
            return full_output
        return "..." + full_output[-max_chars:]
    
    async def cleanup(self):
        """Clean up the session."""
        # Terminate process if still alive
        if self.is_alive():
            try:
                # First, try to close stdin cleanly
                if self.process.stdin and not self.process.stdin.is_closing():
                    try:
                        self.process.stdin.write_eof()
                        await self.process.stdin.drain()
                        self.process.stdin.close()
                        await self.process.stdin.wait_closed()
                    except:
                        pass
                
                # Send terminate signal
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=3)
            except asyncio.TimeoutError:
                # If graceful termination failed, force kill
                self.process.kill()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=2)
                except:
                    pass
            except:
                pass
        
        # Ensure all pipes are closed
        try:
            if self.process.stdin and not self.process.stdin.is_closing():
                self.process.stdin.close()
                await self.process.stdin.wait_closed()
        except:
            pass
        
        try:
            if self.process.stdout and not self.process.stdout.at_eof():
                self.process.stdout.close()
        except:
            pass
            
        try:
            if self.process.stderr and not self.process.stderr.at_eof():
                self.process.stderr.close()
        except:
            pass
        
        # Force close the transport if available
        try:
            if hasattr(self.process, '_transport') and self.process._transport:
                self.process._transport.close()
        except:
            pass


class InteractiveBashOperationsTool(SyncTool):
    """Interactive Bash Operations Tool that can handle blocking/interactive processes."""
    
    def __init__(self, 
                 base_directory: str = "./workspace",
                 allowed_commands: Optional[List[str]] = None,
                 blocked_commands: Optional[List[str]] = None,
                 max_output_size: int = 1024 * 1024 * 5,  # 5MB default for interactive output
                 unsafe_mode: bool = False,
                 session_timeout: int = 3600):  # 1 hour default session timeout
        """Initialize the interactive bash operations tool.
        
        Args:
            base_directory: Base directory for command execution
            allowed_commands: List of allowed command prefixes
            blocked_commands: List of blocked command prefixes
            max_output_size: Maximum output size in bytes
            unsafe_mode: If True, disables safety mechanisms
            session_timeout: Timeout for inactive sessions in seconds
        """
        # Call parent constructor first
        super().__init__(
            name="interactive_bash",
            description="Execute interactive bash commands and respond to prompts",
            input_schema=InteractiveBashArgs
        )
        
        self.base_directory = Path(base_directory).resolve()
        self.allowed_commands = allowed_commands
        self.blocked_commands = blocked_commands or []
        self.max_output_size = max_output_size
        self.unsafe_mode = unsafe_mode
        self.session_timeout = session_timeout
        
        # Session management
        self.sessions: Dict[str, InteractiveSession] = {}
        self.session_counter = 0
        
        # Key mappings for special keys
        self.key_mappings = {
            # Arrow keys
            "up": "\033[A",
            "down": "\033[B",
            "right": "\033[C", 
            "left": "\033[D",
            
            # Control keys
            "enter": "\r",
            "tab": "\t",
            "escape": "\033",
            "space": " ",
            "backspace": "\b",
            "delete": "\033[3~",
            
            # Navigation keys
            "home": "\033[H",
            "end": "\033[F",
            "page_up": "\033[5~",
            "page_down": "\033[6~",
            "insert": "\033[2~",
            
            # Function keys
            "f1": "\033OP", "f2": "\033OQ", "f3": "\033OR", "f4": "\033OS",
            "f5": "\033[15~", "f6": "\033[17~", "f7": "\033[18~", "f8": "\033[19~",
            "f9": "\033[20~", "f10": "\033[21~", "f11": "\033[23~", "f12": "\033[24~",
            
            # Common combinations
            "ctrl_c": "\003",
            "ctrl_d": "\004",
            "ctrl_z": "\032",
            "ctrl_a": "\001",
            "ctrl_e": "\005",
        }
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Log warning if unsafe mode is enabled
        if self.unsafe_mode:
            self.logger.warning("⚠️ INTERACTIVE UNSAFE MODE ENABLED - ALL SECURITY MECHANISMS DISABLED")
        
        # Ensure base directory exists
        self.base_directory.mkdir(parents=True, exist_ok=True)
        
        # Session cleanup will be handled manually
        
        # Create the FunctionTool
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=InteractiveBashArgs.model_json_schema(),
            on_invoke_tool=self._run_interactive_bash
        )
        
        # Register this instance in the global registry
        _interactive_bash_tools_registry.append(self)
    
    def _validate_dangerous_patterns(self, command: str) -> None:
        """Validate command against dangerous patterns (unless in unsafe mode)."""
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
                full_path = Path(working_dir).resolve()
            else:
                full_path = (self.base_directory / working_dir).resolve()
            
            full_path.mkdir(parents=True, exist_ok=True)
            return full_path
        
        # Safe mode - restrict to base directory
        full_path = (self.base_directory / working_dir).resolve()
        
        try:
            full_path.relative_to(self.base_directory)
        except ValueError:
            raise ValueError(f"Working directory '{working_dir}' is outside the allowed base directory")
        
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        self.session_counter += 1
        return f"interactive_session_{self.session_counter}_{int(time.time())}"
    
    async def _detect_prompts(self, output: str) -> Optional[str]:
        """Detect common interactive prompts in output."""
        prompt_patterns = [
            # General prompts
            "Press any key to continue",
            "Do you want to continue? [Y/n]",
            "Are you sure? [y/N]",
            "Enter your choice:",
            "Select an option:",
            "Please enter",
            "Password:",
            "Username:",
            "[Y/n]",
            "[y/N]",
            "(y/n)",
            "Continue? ",
            "Proceed? ",
            
            # Package manager specific
            "Which package manager would you like to use?",
            "Choose a package manager:",
            "Select package manager:",
            "? ",  # Common CLI question prefix
            "❯ ",  # CLI selection arrow
            "✔ ",  # CLI checkmark
            "◯ ",  # CLI radio button
            "◉ ",  # CLI selected radio
            "▸ ",  # CLI arrow
            
            # Nuxt/Vue specific
            "Initialize git repository?",
            "Install dependencies?",
            "Which UI framework would you like to use?",
            "Would you like to install dependencies?",
            "Project name:",
            "Package name:",
            
            # Shell prompts
            "> ",
            "$ ",
            "# ",
            
            # Generic patterns that might indicate waiting
            "...",
            "waiting",
            "loading",
        ]
        
        output_lower = output.lower()
        output_lines = output.split('\n')
        
        # Check each line for prompts (more precise than checking entire output)
        for line in output_lines[-5:]:  # Check last 5 lines
            line_lower = line.strip().lower()
            if not line_lower:
                continue
                
            for pattern in prompt_patterns:
                if pattern.lower() in line_lower:
                    self.logger.info(f"🔍 PROMPT DETECTED in line: '{line.strip()}' -> pattern: '{pattern}'")
                    return pattern
        
        # Also check if output ends with certain characters that suggest waiting for input
        if output.strip():
            last_char = output.strip()[-1]
            if last_char in ['?', ':', '>', '$', '#']:
                self.logger.info(f"🔍 PROMPT DETECTED by ending character: '{last_char}'")
                return f"Prompt ending with '{last_char}'"
        
        return None
    
    def _convert_special_keys_to_sequence(self, special_keys: List[str]) -> str:
        """Convert list of special key names to escape sequences."""
        sequence = ""
        for key in special_keys:
            key_lower = key.lower()
            if key_lower in self.key_mappings:
                sequence += self.key_mappings[key_lower]
            else:
                raise ValueError(f"Unknown special key: {key}. Available keys: {list(self.key_mappings.keys())}")
        return sequence
    
    async def _send_input_to_process(self, process: asyncio.subprocess.Process, 
                                   input_text: Optional[str] = None,
                                   special_keys: Optional[List[str]] = None,
                                   key_sequence: Optional[str] = None) -> None:
        """Send input to the interactive process."""
        try:
            if not (process.stdin and not process.stdin.is_closing()):
                raise ValueError("Process stdin is not available")
            
            # Determine what to send
            if key_sequence:
                # Raw escape sequence (advanced usage)
                input_bytes = key_sequence.encode('utf-8')
                self.logger.info(f"🔑 SENT RAW SEQUENCE: {repr(key_sequence)}")
                
            elif special_keys:
                # Convert special keys to escape sequences
                sequence = self._convert_special_keys_to_sequence(special_keys)
                input_bytes = sequence.encode('utf-8')
                self.logger.info(f"🔑 SENT SPECIAL KEYS: {special_keys} -> {repr(sequence)}")
                
            elif input_text is not None:
                # Regular text input (add newline unless it's just whitespace/control chars)
                if input_text.strip() and not all(ord(c) < 32 for c in input_text):
                    input_bytes = (input_text + '\n').encode('utf-8')
                else:
                    input_bytes = input_text.encode('utf-8')
                self.logger.info(f"📝 SENT TEXT: {input_text}")
                
            else:
                raise ValueError("Must provide input_text, special_keys, or key_sequence")
            
            # Send the input
            process.stdin.write(input_bytes)
            await process.stdin.drain()
            
        except Exception as e:
            self.logger.error(f"Error sending input to process: {e}")
            raise
    
    async def _cleanup_sessions(self):
        """Background task to cleanup expired sessions."""
        while True:
            try:
                current_time = time.time()
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    if (current_time - session.last_activity > self.session_timeout or 
                        not session.is_alive()):
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    session = self.sessions.pop(session_id, None)
                    if session and session.is_alive():
                        try:
                            session.process.terminate()
                            await asyncio.wait_for(session.process.wait(), timeout=5)
                        except:
                            session.process.kill()
                    
                    self.logger.info(f"🧹 CLEANED UP SESSION: {session_id}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(60)
    
    async def _run_interactive_bash(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Execute interactive bash operations based on action.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing InteractiveBashArgs
            
        Returns:
            Action result as string
        """
        try:
            # Parse arguments
            parsed_args = InteractiveBashArgs.model_validate_json(args)
            
            # Route to appropriate action handler
            if parsed_args.action == 'start_session':
                return await self._action_start_session(parsed_args)
            elif parsed_args.action == 'check_session':
                return await self._action_check_session(parsed_args)
            elif parsed_args.action == 'send_input':
                return await self._action_send_input(parsed_args)
            elif parsed_args.action == 'terminate_session':
                return await self._action_terminate_session(parsed_args)
            else:
                raise ValueError(f"Unknown action: {parsed_args.action}")
                
        except ValueError as e:
            self.logger.error(f"❌ INTERACTIVE BASH FAILED with validation error: {str(e)}")
            return f"Validation error: {str(e)}"
        except Exception as e:
            self.logger.error(f"❌ INTERACTIVE BASH FAILED with unexpected error: {str(e)}")
            return f"Unexpected error: {str(e)}"
    
    async def _action_start_session(self, parsed_args: InteractiveBashArgs) -> str:
        """Start a new interactive session."""
        # Validate command safety
        self._validate_dangerous_patterns(parsed_args.command)
        self._validate_command_permissions(parsed_args.command)
        working_dir = self._validate_working_directory(parsed_args.working_directory)
        
        self.logger.info(f"🚀 STARTING SESSION - Command: {parsed_args.command}")
        self.logger.info(f"📁 Working directory: {working_dir}")
        
        try:
            # Create process with PTY for better streaming compatibility
            # and unbuffered output
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['TERM'] = 'xterm-256color'
            env['FORCE_COLOR'] = '1'  # Force color output for better tool compatibility
            
            # Wrap command with stdbuf to force line buffering for better streaming
            wrapped_command = f"stdbuf -o0 -e0 {parsed_args.command}"
            
            process = await asyncio.create_subprocess_shell(
                wrapped_command,
                cwd=working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,  # Merge stderr with stdout
                stdin=asyncio.subprocess.PIPE,
                env=env,
                start_new_session=True  # Create new process group
            )
            
            # Create session
            session_id = self._generate_session_id()
            session = InteractiveSession(session_id, process, working_dir, parsed_args.command)
            self.sessions[session_id] = session
            
            # Read any immediately available output
            await asyncio.sleep(1.0)  # Give process more time to start
            
            # Get any initial output with longer wait
            initial_output = await self._read_available_output(session, timeout=2.0)
            
            # Clear the "new output" buffer since we're returning initial output
            await session.get_new_output_since_check()
            
            result_parts = [
                f"🚀 SESSION STARTED",
                f"Session ID: {session_id}",
                f"Command: {parsed_args.command}",
                f"Working Directory: {str(working_dir.relative_to(self.base_directory))}",
                f"Process Alive: {session.is_alive()}",
                f"Exit Code: {process.returncode}",
                f"Status: {session.status}"
            ]
            
            if initial_output.strip():
                result_parts.append(f"\nINITIAL OUTPUT:\n{initial_output}")
            
            return "\n".join(result_parts)
            
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            return f"❌ FAILED TO START SESSION: {str(e)}"
    
    async def _action_check_session(self, parsed_args: InteractiveBashArgs) -> str:
        """Check session status and get new output."""
        session = self.sessions.get(parsed_args.session_id)
        if not session:
            return f"❌ SESSION NOT FOUND: {parsed_args.session_id}"
        
        session.update_activity()
        
        # Read any available output and update session state with longer timeout
        await self._read_available_output(session, timeout=1.0)
        
        # Get new output since last check
        new_output = await session.get_new_output_since_check()
        
        # Update status based on current state
        if not session.is_alive():
            session.status = "completed"
        elif session.is_waiting_for_input:
            session.status = "waiting"
        else:
            session.status = "running"
        
        result_parts = [
            f"📊 SESSION CHECK - {parsed_args.session_id}",
            f"Process Alive: {session.is_alive()}",
            f"Exit Code: {session.process.returncode}",
            f"Status: {session.status}",
            f"Waiting for Input: {session.is_waiting_for_input}"
        ]
        
        if session.prompt_detected:
            result_parts.append(f"Detected Prompt: {session.prompt_detected}")
        
        result_parts.extend([
            f"Session Age: {int(time.time() - session.created_at)}s",
            f"Last Activity: {int(time.time() - session.last_activity)}s ago",
            f"Total Output: {session.total_output_length} chars"
        ])
        
        if new_output.strip():
            result_parts.append(f"\nNEW OUTPUT:\n{new_output}")
        else:
            result_parts.append("No new output since last check")
        
        return "\n".join(result_parts)
    
    async def _action_send_input(self, parsed_args: InteractiveBashArgs) -> str:
        """Send input to an existing session."""
        session = self.sessions.get(parsed_args.session_id)
        if not session:
            return f"❌ SESSION NOT FOUND: {parsed_args.session_id}"
        
        if not session.is_alive():
            return f"❌ SESSION PROCESS NOT ALIVE: {parsed_args.session_id} (exit code: {session.process.returncode})"
        
        try:
            # Send the input
            await self._send_input_to_process(
                session.process,
                input_text=parsed_args.input_text,
                special_keys=parsed_args.special_keys,
                key_sequence=parsed_args.key_sequence
            )
            
            # Reset waiting state
            session.is_waiting_for_input = False
            session.prompt_detected = None
            session.status = "running"
            session.update_activity()
            
            # Wait a moment for response then read output
            await asyncio.sleep(3.0)
            
            # Try to force output by sending a newline if no input was provided
            if parsed_args.input_text is None and parsed_args.special_keys is None and parsed_args.key_sequence is None:
                # For commands that might be waiting, send an empty line to trigger output
                try:
                    session.process.stdin.write(b'\n')
                    await session.process.stdin.drain()
                    await asyncio.sleep(0.5)
                except:
                    pass
            
            # Read any available output with longer timeout and multiple attempts
            for attempt in range(3):
                await self._read_available_output(session, timeout=2.0)
                if session.new_output_since_check:
                    break
                await asyncio.sleep(1.0)
            
            # Get response output
            response_output = await session.get_new_output_since_check()
            
            input_sent = parsed_args.input_text or str(parsed_args.special_keys) or parsed_args.key_sequence
            
            result_parts = [
                f"📝 INPUT SENT - {parsed_args.session_id}",
                f"Input: {input_sent}",
                f"Process Alive: {session.is_alive()}",
                f"Exit Code: {session.process.returncode}",
                f"Status: {session.status}",
                f"Waiting for Input: {session.is_waiting_for_input}"
            ]
            
            if response_output.strip():
                result_parts.append(f"\nRESPONSE OUTPUT:\n{response_output}")
            else:
                result_parts.append("No response output received")
            
            return "\n".join(result_parts)
            
        except Exception as e:
            self.logger.error(f"Error sending input: {e}")
            return f"❌ FAILED TO SEND INPUT: {str(e)}"
    
    async def _action_terminate_session(self, parsed_args: InteractiveBashArgs) -> str:
        """Terminate an existing session."""
        session = self.sessions.pop(parsed_args.session_id, None)
        if not session:
            return f"❌ SESSION NOT FOUND: {parsed_args.session_id}"
        
        exit_code = session.process.returncode
        final_output = ''.join(session.output_buffer)
        
        # Properly clean up the session (this will terminate process and cancel tasks)
        await session.cleanup()
        
        result_parts = [
            f"🛑 SESSION TERMINATED - {parsed_args.session_id}",
            f"Exit Code: {session.process.returncode}",
            f"Session Duration: {int(time.time() - session.created_at)}s",
            f"Total Output: {session.total_output_length} chars"
        ]
        
        if final_output.strip():
            # Show last 1000 chars of output
            display_output = final_output[-1000:] if len(final_output) > 1000 else final_output
            result_parts.append(f"\nFINAL OUTPUT:\n{display_output}")
        
        return "\n".join(result_parts)
    
    async def _read_available_output(self, session: InteractiveSession, timeout: float = 0.5) -> str:
        """Read any available output from the session without blocking."""
        output_chunks = []
        
        try:
            # Non-blocking read of available data with configurable timeout
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        session.process.stdout.read(4096), 
                        timeout=timeout
                    )
                    
                    if not chunk:
                        break
                        
                    chunk_text = chunk.decode('utf-8', errors='replace')
                    output_chunks.append(chunk_text)
                    await session.add_output(chunk_text)
                    
                except asyncio.TimeoutError:
                    # No more data available
                    break
                except Exception as e:
                    self.logger.debug(f"Error reading output: {e}")
                    break
            
            full_output = ''.join(output_chunks)
            
            # Check for prompts if we got output
            if full_output:
                recent_output = session.get_recent_output(500)
                prompt = await self._detect_prompts(recent_output)
                if prompt:
                    session.prompt_detected = prompt
                    session.is_waiting_for_input = True
                    session.status = "waiting"
                    self.logger.info(f"🔍 PROMPT DETECTED in session {session.session_id}: {prompt}")
            
            # Update session status
            if not session.is_alive():
                session.status = "completed"
                
            return full_output
            
        except Exception as e:
            self.logger.error(f"Error reading available output: {e}")
            return ""
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool instance
        """
        return self.tool
    
    def get_active_sessions(self) -> Dict[str, Dict]:
        """Get information about active sessions.
        
        Returns:
            Dictionary with session information
        """
        return {
            session_id: {
                "command": session.command,
                "working_dir": str(session.working_dir),
                "is_alive": session.is_alive(),
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "waiting_for_input": session.is_waiting_for_input,
                "detected_prompt": session.prompt_detected
            }
            for session_id, session in self.sessions.items()
        }
    
    async def cleanup_all_sessions(self):
        """Clean up all active sessions."""
        self.logger.info(f"🧹 CLEANING UP {len(self.sessions)} interactive bash sessions")
        
        for session_id, session in list(self.sessions.items()):
            try:
                self.logger.info(f"🧹 Cleaning up session: {session_id}")
                await session.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up session {session_id}: {e}")
        
        self.sessions.clear()
        self.logger.info("✅ All interactive bash sessions cleaned up")


def get_default_interactive_bash_tool() -> FunctionTool:
    """Get a default interactive bash operations tool instance.
    
    Returns:
        FunctionTool instance
    """
    return InteractiveBashOperationsTool().get_tool()


async def cleanup_all_global_interactive_bash_sessions():
    """Clean up all sessions from all registered interactive bash tools."""
    logger = logging.getLogger(__name__)
    
    if not _interactive_bash_tools_registry:
        logger.debug("No interactive bash tools registered for cleanup")
        return
    
    logger.info(f"🧹 GLOBAL CLEANUP: Found {len(_interactive_bash_tools_registry)} interactive bash tools")
    
    for tool in _interactive_bash_tools_registry:
        try:
            await tool.cleanup_all_sessions()
        except Exception as e:
            logger.error(f"Error during global cleanup of interactive bash tool: {e}")
    
    logger.info("✅ Global interactive bash sessions cleanup completed")


def clear_interactive_bash_tools_registry():
    """Clear the global registry (useful for testing or complete reset)."""
    global _interactive_bash_tools_registry
    _interactive_bash_tools_registry.clear()