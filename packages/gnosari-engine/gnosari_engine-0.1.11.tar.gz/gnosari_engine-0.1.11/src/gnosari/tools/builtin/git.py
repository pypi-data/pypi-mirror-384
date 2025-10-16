"""
Git Operations Tool - Using OpenAI Agents SDK FunctionTool
"""

import logging
import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional, Literal, List, Dict
from pydantic import BaseModel, Field, field_validator
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import SyncTool


class GitArgs(BaseModel):
    """Arguments for the git operations tool."""
    operation: Literal[
        "status", "add", "commit", "push", "pull", "clone", "branch", "checkout", 
        "merge", "log", "diff", "remote", "tag", "stash", "reset", "revert", "fetch"
    ] = Field(..., description="Git operation to perform")
    
    # Common arguments
    repository_path: Optional[str] = Field(default=None, description="Path to git repository (relative to base directory)")
    
    # Add operation
    files: Optional[List[str]] = Field(default=None, description="Files to add (for add operation)")
    all_files: Optional[bool] = Field(default=False, description="Add all changes (git add -A)")
    
    # Commit operation
    message: Optional[str] = Field(default=None, description="Commit message (required for commit operation)")
    amend: Optional[bool] = Field(default=False, description="Amend the last commit")
    
    # Branch operations
    branch_name: Optional[str] = Field(default=None, description="Branch name (for branch, checkout operations)")
    create_branch: Optional[bool] = Field(default=False, description="Create new branch (for checkout -b)")
    delete_branch: Optional[bool] = Field(default=False, description="Delete branch")
    
    # Remote operations
    remote_name: Optional[str] = Field(default="origin", description="Remote name (default: origin)")
    remote_url: Optional[str] = Field(default=None, description="Remote URL (for adding remotes)")
    
    # Push/Pull options
    force: Optional[bool] = Field(default=False, description="Force push/pull")
    set_upstream: Optional[bool] = Field(default=False, description="Set upstream tracking")
    
    # Clone operation
    clone_url: Optional[str] = Field(default=None, description="Repository URL to clone")
    clone_destination: Optional[str] = Field(default=None, description="Destination directory for clone")
    
    # Log operation
    max_count: Optional[int] = Field(default=10, description="Maximum number of commits to show in log")
    oneline: Optional[bool] = Field(default=False, description="Show log in oneline format")
    
    # Diff operation
    staged: Optional[bool] = Field(default=False, description="Show staged changes (git diff --cached)")
    file_path: Optional[str] = Field(default=None, description="Specific file to diff")
    
    # Reset operation
    reset_mode: Optional[Literal["soft", "mixed", "hard"]] = Field(default="mixed", description="Reset mode")
    commit_hash: Optional[str] = Field(default=None, description="Commit hash for reset/revert operations")
    
    # Tag operation
    tag_name: Optional[str] = Field(default=None, description="Tag name")
    tag_message: Optional[str] = Field(default=None, description="Tag message (for annotated tags)")
    
    # Stash operation
    stash_message: Optional[str] = Field(default=None, description="Stash message")
    stash_operation: Optional[Literal["save", "pop", "apply", "list", "drop", "clear"]] = Field(default="save", description="Stash sub-operation")
    
    @field_validator('message')
    @classmethod
    def validate_commit_message(cls, v, info):
        """Validate commit message is provided for commit operations."""
        values = info.data
        if values.get('operation') == 'commit' and not v and not values.get('amend'):
            raise ValueError("Commit message is required for commit operation")
        return v
    
    @field_validator('clone_url')
    @classmethod
    def validate_clone_url(cls, v, info):
        """Validate clone URL is provided for clone operations."""
        values = info.data
        if values.get('operation') == 'clone' and not v:
            raise ValueError("Clone URL is required for clone operation")
        return v
    
    class Config:
        extra = "forbid"


class GitTool(SyncTool):
    """Git Operations Tool that provides comprehensive git functionality."""
    
    def __init__(
        self,
        base_directory: str = "./workspace",
        max_output_size: int = 1024 * 1024,  # 1MB default
        timeout: int = 60,  # Default timeout for git operations
        allowed_operations: Optional[List[str]] = None,  # Restrict operations if needed
        safe_mode: bool = True  # Enable safety checks
    ):
        """Initialize the git operations tool.
        
        Args:
            base_directory: Base directory for git operations
            max_output_size: Maximum output size in bytes
            timeout: Default timeout for git operations
            allowed_operations: List of allowed operations. None allows all.
            safe_mode: Enable safety checks to prevent destructive operations
        """
        super().__init__(
            name="git",
            description="Perform git operations including status, add, commit, push, pull, branching, and more",
            input_schema=GitArgs
        )
        
        self.base_directory = Path(base_directory).resolve()
        self.max_output_size = max_output_size
        self.timeout = timeout
        self.allowed_operations = allowed_operations
        self.safe_mode = safe_mode
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Ensure base directory exists
        self.base_directory.mkdir(parents=True, exist_ok=True)
        
        # Create the FunctionTool
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=GitArgs.model_json_schema(),
            on_invoke_tool=self._run_git_operation
        )
    
    def _validate_repository_path(self, repo_path: Optional[str]) -> Path:
        """Validate and resolve repository path."""
        if repo_path is None:
            return self.base_directory
        
        full_path = (self.base_directory / repo_path).resolve()
        
        # Ensure the path is within the base directory
        try:
            full_path.relative_to(self.base_directory)
        except ValueError:
            raise ValueError(f"Repository path '{repo_path}' is outside the allowed base directory")
        
        return full_path
    
    def _validate_operation(self, operation: str) -> None:
        """Validate that the operation is allowed."""
        if self.allowed_operations and operation not in self.allowed_operations:
            raise ValueError(f"Operation '{operation}' is not allowed. Allowed operations: {self.allowed_operations}")
        
        # Safety checks for destructive operations
        if self.safe_mode:
            destructive_ops = ['reset', 'revert']
            if operation in destructive_ops:
                self.logger.warning(f"⚠️ Destructive operation '{operation}' - use with caution")
    
    async def _execute_git_command(self, command_parts: List[str], working_dir: Path) -> tuple[int, str, str]:
        """Execute a git command asynchronously.
        
        Args:
            command_parts: List of command parts (e.g., ['git', 'status'])
            working_dir: Working directory for the command
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Log the command
            command_str = " ".join(command_parts)
            self.logger.info(f"🔧 Executing: {command_str}")
            self.logger.info(f"📁 Working directory: {working_dir}")
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *command_parts,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                self.logger.error(f"❌ Git command timeout after {self.timeout} seconds")
                return -1, "", f"Git command timed out after {self.timeout} seconds"
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            # Check output size
            total_size = len(stdout_text.encode('utf-8')) + len(stderr_text.encode('utf-8'))
            if total_size > self.max_output_size:
                self.logger.error(f"❌ Output too large: {total_size} bytes")
                return -1, "", f"Output too large ({total_size} bytes). Maximum: {self.max_output_size}"
            
            if process.returncode == 0:
                self.logger.info(f"✅ Git command success")
            else:
                self.logger.warning(f"⚠️ Git command completed with exit code: {process.returncode}")
            
            return process.returncode, stdout_text, stderr_text
            
        except Exception as e:
            self.logger.error(f"❌ Git command execution failed: {str(e)}")
            return -1, "", str(e)
    
    def _build_git_command(self, args: GitArgs) -> List[str]:
        """Build git command based on the operation and arguments."""
        cmd = ["git"]
        
        if args.operation == "status":
            cmd.extend(["status", "--porcelain" if args.oneline else ""])
            if not args.oneline:
                cmd.remove("")  # Remove empty string
        
        elif args.operation == "add":
            cmd.append("add")
            if args.all_files:
                cmd.append("-A")
            elif args.files:
                cmd.extend(args.files)
            else:
                cmd.append(".")
        
        elif args.operation == "commit":
            cmd.append("commit")
            if args.amend:
                cmd.append("--amend")
            if args.message:
                cmd.extend(["-m", args.message])
        
        elif args.operation == "push":
            cmd.append("push")
            if args.force:
                cmd.append("--force")
            if args.set_upstream:
                cmd.extend(["-u", args.remote_name or "origin"])
                if args.branch_name:
                    cmd.append(args.branch_name)
            elif args.remote_name:
                cmd.append(args.remote_name)
                if args.branch_name:
                    cmd.append(args.branch_name)
        
        elif args.operation == "pull":
            cmd.append("pull")
            if args.remote_name:
                cmd.append(args.remote_name)
                if args.branch_name:
                    cmd.append(args.branch_name)
        
        elif args.operation == "clone":
            cmd.extend(["clone", args.clone_url])
            if args.clone_destination:
                cmd.append(args.clone_destination)
        
        elif args.operation == "branch":
            cmd.append("branch")
            if args.delete_branch and args.branch_name:
                cmd.extend(["-d", args.branch_name])
            elif args.branch_name:
                cmd.append(args.branch_name)
        
        elif args.operation == "checkout":
            cmd.append("checkout")
            if args.create_branch:
                cmd.append("-b")
            if args.branch_name:
                cmd.append(args.branch_name)
        
        elif args.operation == "merge":
            cmd.append("merge")
            if args.branch_name:
                cmd.append(args.branch_name)
        
        elif args.operation == "log":
            cmd.append("log")
            if args.max_count:
                cmd.extend([f"--max-count={args.max_count}"])
            if args.oneline:
                cmd.append("--oneline")
        
        elif args.operation == "diff":
            cmd.append("diff")
            if args.staged:
                cmd.append("--cached")
            if args.file_path:
                cmd.append(args.file_path)
        
        elif args.operation == "remote":
            cmd.append("remote")
            if args.remote_url and args.remote_name:
                cmd.extend(["add", args.remote_name, args.remote_url])
            else:
                cmd.append("-v")
        
        elif args.operation == "tag":
            cmd.append("tag")
            if args.tag_name:
                if args.tag_message:
                    cmd.extend(["-a", args.tag_name, "-m", args.tag_message])
                else:
                    cmd.append(args.tag_name)
        
        elif args.operation == "stash":
            cmd.append("stash")
            stash_op = args.stash_operation or "save"
            if stash_op != "save":
                cmd.append(stash_op)
            elif args.stash_message:
                cmd.extend(["save", args.stash_message])
        
        elif args.operation == "reset":
            cmd.append("reset")
            if args.reset_mode:
                cmd.append(f"--{args.reset_mode}")
            if args.commit_hash:
                cmd.append(args.commit_hash)
        
        elif args.operation == "revert":
            cmd.append("revert")
            if args.commit_hash:
                cmd.append(args.commit_hash)
            else:
                cmd.append("HEAD")
        
        elif args.operation == "fetch":
            cmd.append("fetch")
            if args.remote_name:
                cmd.append(args.remote_name)
        
        return cmd
    
    async def _run_git_operation(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Execute git operation based on arguments.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing GitArgs
            
        Returns:
            Git operation result as string
        """
        try:
            # Parse arguments
            parsed_args = GitArgs.model_validate_json(args)
            
            # Validate operation
            self._validate_operation(parsed_args.operation)
            
            # Validate and resolve repository path
            repo_path = self._validate_repository_path(parsed_args.repository_path)
            
            # Special handling for clone operation (creates new directory)
            if parsed_args.operation == "clone":
                working_dir = repo_path.parent if parsed_args.clone_destination else repo_path
                working_dir.mkdir(parents=True, exist_ok=True)
            else:
                working_dir = repo_path
                
                # Check if it's a git repository for most operations
                if not (working_dir / ".git").exists() and parsed_args.operation not in ["clone", "init"]:
                    return f"Error: '{working_dir.relative_to(self.base_directory)}' is not a git repository"
            
            self.logger.info(f"🔧 GIT OPERATION - {parsed_args.operation.upper()}")
            
            # Build git command
            git_command = self._build_git_command(parsed_args)
            
            # Execute git command
            exit_code, stdout, stderr = await self._execute_git_command(git_command, working_dir)
            
            # Format output
            output_parts = []
            output_parts.append(f"Git {parsed_args.operation} completed with exit code: {exit_code}")
            output_parts.append(f"Repository: {repo_path.relative_to(self.base_directory)}")
            output_parts.append(f"Command: {' '.join(git_command)}")
            
            if stdout.strip():
                output_parts.append(f"\nOutput:\n{stdout.strip()}")
            
            if stderr.strip():
                output_parts.append(f"\nError output:\n{stderr.strip()}")
            
            # Add operation-specific success messages
            if exit_code == 0:
                if parsed_args.operation == "commit":
                    output_parts.append("\n✅ Changes committed successfully")
                elif parsed_args.operation == "push":
                    output_parts.append("\n✅ Changes pushed to remote repository")
                elif parsed_args.operation == "pull":
                    output_parts.append("\n✅ Changes pulled from remote repository")
                elif parsed_args.operation == "clone":
                    output_parts.append(f"\n✅ Repository cloned successfully")
            
            return "\n".join(output_parts)
            
        except ValueError as e:
            self.logger.error(f"❌ Git operation validation error: {str(e)}")
            return f"Validation error: {str(e)}"
        except Exception as e:
            self.logger.error(f"❌ Git operation unexpected error: {str(e)}")
            return f"Unexpected error: {str(e)}"
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool instance
        """
        return self.tool


def get_default_git_tool() -> FunctionTool:
    """Get a default git tool instance.
    
    Returns:
        FunctionTool instance
    """
    return GitTool().get_tool()