"""
Kubectl Tool - Comprehensive Kubernetes Cluster Management using kubectl and Helm
"""

import logging
import asyncio
import json
import os
import subprocess
import shlex
import yaml
from pathlib import Path
from typing import Any, Optional, Literal, List, Dict, Union
from pydantic import BaseModel, Field, field_validator
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import SyncTool


class KubectlArgs(BaseModel):
    """Arguments for the kubectl tool."""
    operation: Literal[
        "deployment", "pod", "service", "configmap", "secret", 
        "helm", "namespace", "info", "generic"
    ] = Field(..., description="Type of Kubernetes operation to perform")
    
    action: str = Field(..., description="Specific action to perform within the operation")
    
    # Resource identification
    name: Optional[str] = Field(default=None, description="Name of the resource (deployment, pod, service, etc.)")
    namespace: Optional[str] = Field(default=None, description="Kubernetes namespace to operate in")
    
    # Generic parameters
    params: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters specific to the action")
    
    # File and YAML operations
    yaml_content: Optional[str] = Field(default=None, description="YAML content for create/apply operations")
    file_path: Optional[str] = Field(default=None, description="Path to YAML file for apply operations")
    
    # Helm-specific parameters
    chart: Optional[str] = Field(default=None, description="Helm chart name or path")
    release_name: Optional[str] = Field(default=None, description="Helm release name")
    chart_version: Optional[str] = Field(default=None, description="Helm chart version")
    values: Optional[Dict[str, Any]] = Field(default=None, description="Helm values override")
    values_file: Optional[str] = Field(default=None, description="Path to Helm values file")
    repo_name: Optional[str] = Field(default=None, description="Helm repository name")
    repo_url: Optional[str] = Field(default=None, description="Helm repository URL")
    
    # Pod-specific parameters
    container: Optional[str] = Field(default=None, description="Container name for pod operations")
    command: Optional[List[str]] = Field(default=None, description="Command to execute in pod")
    follow_logs: Optional[bool] = Field(default=False, description="Follow logs output")
    tail_lines: Optional[int] = Field(default=None, description="Number of lines to tail from logs")
    
    # Deployment-specific parameters
    replicas: Optional[int] = Field(default=None, description="Number of replicas for scaling")
    image: Optional[str] = Field(default=None, description="Container image for deployment")
    
    # Service-specific parameters
    port: Optional[int] = Field(default=None, description="Port number for service operations")
    target_port: Optional[int] = Field(default=None, description="Target port for service")
    service_type: Optional[Literal["ClusterIP", "NodePort", "LoadBalancer", "ExternalName"]] = Field(
        default="ClusterIP", description="Kubernetes service type"
    )
    
    # Generic kubectl parameters
    output_format: Optional[Literal["json", "yaml", "wide", "name", "custom-columns"]] = Field(
        default=None, description="Output format for kubectl commands"
    )
    labels: Optional[Dict[str, str]] = Field(default=None, description="Label selectors")
    all_namespaces: Optional[bool] = Field(default=False, description="Operate across all namespaces")
    dry_run: Optional[bool] = Field(default=False, description="Perform dry run without making changes")
    
    # Execution parameters
    timeout: Optional[int] = Field(default=60, description="Command timeout in seconds")
    kubeconfig: Optional[str] = Field(default=None, description="Path to kubeconfig file")
    context: Optional[str] = Field(default=None, description="Kubernetes context to use")
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v):
        """Validate operation type."""
        valid_operations = [
            "deployment", "pod", "service", "configmap", "secret", 
            "helm", "namespace", "info", "generic"
        ]
        if v not in valid_operations:
            raise ValueError(f"Operation must be one of: {valid_operations}")
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout is within reasonable bounds."""
        if v is not None and (v <= 0 or v > 3600):
            raise ValueError("Timeout must be between 1 and 3600 seconds")
        return v
    
    class Config:
        extra = "forbid"


class KubectlTool(SyncTool):
    """Comprehensive Kubernetes management tool using kubectl and Helm."""
    
    def __init__(self, 
                 kubeconfig: Optional[str] = None,
                 default_namespace: str = "default",
                 default_context: Optional[str] = None,
                 kubectl_binary: str = "kubectl",
                 helm_binary: str = "helm",
                 working_directory: str = "./",
                 max_output_size: int = 1024 * 1024 * 5,  # 5MB default
                 verify_tools: bool = True):
        """Initialize the kubectl tool.
        
        Args:
            kubeconfig: Path to kubeconfig file
            default_namespace: Default Kubernetes namespace
            default_context: Default Kubernetes context
            kubectl_binary: Path to kubectl binary
            helm_binary: Path to helm binary
            working_directory: Working directory for file operations
            max_output_size: Maximum output size in bytes
            verify_tools: Whether to verify kubectl and helm are available
        """
        super().__init__(
            name="kubectl_operations",
            description="Comprehensive Kubernetes cluster management with kubectl and Helm",
            input_schema=KubectlArgs
        )
        
        self.kubeconfig = kubeconfig
        self.default_namespace = default_namespace
        self.default_context = default_context
        self.kubectl_binary = kubectl_binary
        self.helm_binary = helm_binary
        self.working_directory = Path(working_directory).resolve()
        self.max_output_size = max_output_size
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Verify tools are available
        if verify_tools:
            self._verify_tools()
        
        # Ensure working directory exists
        self.working_directory.mkdir(parents=True, exist_ok=True)
        
        # Create the FunctionTool
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=KubectlArgs.model_json_schema(),
            on_invoke_tool=self._run_kubectl_operation
        )
    
    def _verify_tools(self) -> None:
        """Verify kubectl and helm binaries are available."""
        try:
            # Check kubectl
            result = subprocess.run([self.kubectl_binary, "version", "--client"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.logger.warning(f"kubectl not found or not working: {result.stderr}")
            
            # Check helm
            result = subprocess.run([self.helm_binary, "version", "--short"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.logger.warning(f"helm not found or not working: {result.stderr}")
                
        except Exception as e:
            self.logger.warning(f"Could not verify tools: {str(e)}")
    
    def _build_base_command(self, args: KubectlArgs, use_helm: bool = False) -> List[str]:
        """Build base command with common parameters."""
        if use_helm:
            cmd = [self.helm_binary]
        else:
            cmd = [self.kubectl_binary]
            
            # Add kubeconfig if specified
            kubeconfig = args.kubeconfig or self.kubeconfig
            if kubeconfig:
                cmd.extend(["--kubeconfig", kubeconfig])
            
            # Add context if specified
            context = args.context or self.default_context
            if context:
                cmd.extend(["--context", context])
            
            # Add namespace if specified and not using all namespaces
            if not args.all_namespaces:
                namespace = args.namespace or self.default_namespace
                if namespace and namespace != "default":
                    cmd.extend(["-n", namespace])
        
        return cmd
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for kubectl selector."""
        return ",".join([f"{k}={v}" for k, v in labels.items()])
    
    async def _run_kubectl_operation(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Execute the kubectl operation.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing KubectlArgs
            
        Returns:
            Command execution result as string
        """
        try:
            # Parse arguments
            parsed_args = KubectlArgs.model_validate_json(args)
            
            self.logger.info(f"🔧 KUBECTL OPERATION - {parsed_args.operation}:{parsed_args.action}")
            
            # Route to appropriate handler
            if parsed_args.operation == "deployment":
                return await self._handle_deployment(parsed_args)
            elif parsed_args.operation == "pod":
                return await self._handle_pod(parsed_args)
            elif parsed_args.operation == "service":
                return await self._handle_service(parsed_args)
            elif parsed_args.operation == "configmap":
                return await self._handle_configmap(parsed_args)
            elif parsed_args.operation == "secret":
                return await self._handle_secret(parsed_args)
            elif parsed_args.operation == "helm":
                return await self._handle_helm(parsed_args)
            elif parsed_args.operation == "namespace":
                return await self._handle_namespace(parsed_args)
            elif parsed_args.operation == "info":
                return await self._handle_info(parsed_args)
            elif parsed_args.operation == "generic":
                return await self._handle_generic(parsed_args)
            else:
                return f"Unsupported operation: {parsed_args.operation}"
                
        except ValueError as e:
            self.logger.error(f"❌ KUBECTL OPERATION FAILED with validation error: {str(e)}")
            return f"Validation error: {str(e)}"
        except Exception as e:
            self.logger.error(f"❌ KUBECTL OPERATION FAILED with unexpected error: {str(e)}")
            return f"Unexpected error: {str(e)}"
    
    async def _handle_deployment(self, args: KubectlArgs) -> str:
        """Handle deployment operations."""
        cmd = self._build_base_command(args)
        
        if args.action == "create":
            if args.yaml_content:
                return await self._apply_yaml_content(args, args.yaml_content)
            elif args.file_path:
                cmd.extend(["apply", "-f", args.file_path])
            elif args.name and args.image:
                cmd.extend(["create", "deployment", args.name, f"--image={args.image}"])
                if args.replicas:
                    cmd.extend([f"--replicas={args.replicas}"])
            else:
                return "Error: create action requires yaml_content, file_path, or name+image"
        
        elif args.action == "get":
            cmd.extend(["get", "deployments"])
            if args.name:
                cmd.append(args.name)
            if args.output_format:
                cmd.extend(["-o", args.output_format])
                
        elif args.action == "update":
            if args.yaml_content:
                return await self._apply_yaml_content(args, args.yaml_content)
            elif args.file_path:
                cmd.extend(["apply", "-f", args.file_path])
            else:
                return "Error: update action requires yaml_content or file_path"
                
        elif args.action == "delete":
            if not args.name:
                return "Error: delete action requires name parameter"
            cmd.extend(["delete", "deployment", args.name])
            
        elif args.action == "scale":
            if not args.name or args.replicas is None:
                return "Error: scale action requires name and replicas parameters"
            cmd.extend(["scale", "deployment", args.name, f"--replicas={args.replicas}"])
            
        elif args.action == "rollout":
            if not args.name:
                return "Error: rollout action requires name parameter"
            rollout_action = args.params.get("rollout_action", "status") if args.params else "status"
            cmd.extend(["rollout", rollout_action, f"deployment/{args.name}"])
            
        else:
            return f"Unsupported deployment action: {args.action}"
        
        return await self._execute_command(cmd, args.timeout)
    
    async def _handle_pod(self, args: KubectlArgs) -> str:
        """Handle pod operations."""
        cmd = self._build_base_command(args)
        
        if args.action == "get":
            cmd.extend(["get", "pods"])
            if args.name:
                cmd.append(args.name)
            if args.labels:
                cmd.extend(["-l", self._format_labels(args.labels)])
            if args.output_format:
                cmd.extend(["-o", args.output_format])
                
        elif args.action == "logs":
            if not args.name:
                return "Error: logs action requires name parameter"
            cmd.extend(["logs", args.name])
            if args.container:
                cmd.extend(["-c", args.container])
            if args.follow_logs:
                cmd.append("-f")
            if args.tail_lines:
                cmd.extend([f"--tail={args.tail_lines}"])
                
        elif args.action == "exec":
            if not args.name or not args.command:
                return "Error: exec action requires name and command parameters"
            cmd.extend(["exec", "-it", args.name])
            if args.container:
                cmd.extend(["-c", args.container])
            cmd.append("--")
            cmd.extend(args.command)
            
        elif args.action == "delete":
            if not args.name:
                return "Error: delete action requires name parameter"
            cmd.extend(["delete", "pod", args.name])
            
        elif args.action == "port-forward":
            if not args.name or not args.port:
                return "Error: port-forward action requires name and port parameters"
            local_port = args.params.get("local_port", args.port) if args.params else args.port
            cmd.extend(["port-forward", args.name, f"{local_port}:{args.port}"])
            
        else:
            return f"Unsupported pod action: {args.action}"
        
        return await self._execute_command(cmd, args.timeout)
    
    async def _handle_service(self, args: KubectlArgs) -> str:
        """Handle service operations."""
        cmd = self._build_base_command(args)
        
        if args.action == "create":
            if args.yaml_content:
                return await self._apply_yaml_content(args, args.yaml_content)
            elif args.file_path:
                cmd.extend(["apply", "-f", args.file_path])
            else:
                return "Error: create action requires yaml_content or file_path"
                
        elif args.action == "get":
            cmd.extend(["get", "services"])
            if args.name:
                cmd.append(args.name)
            if args.output_format:
                cmd.extend(["-o", args.output_format])
                
        elif args.action == "delete":
            if not args.name:
                return "Error: delete action requires name parameter"
            cmd.extend(["delete", "service", args.name])
            
        elif args.action == "expose":
            if not args.name or not args.port:
                return "Error: expose action requires name and port parameters"
            target_port = args.target_port or args.port
            cmd.extend([
                "expose", "deployment", args.name,
                f"--port={args.port}",
                f"--target-port={target_port}",
                f"--type={args.service_type}"
            ])
            
        else:
            return f"Unsupported service action: {args.action}"
        
        return await self._execute_command(cmd, args.timeout)
    
    async def _handle_configmap(self, args: KubectlArgs) -> str:
        """Handle configmap operations."""
        cmd = self._build_base_command(args)
        
        if args.action == "create":
            if not args.name:
                return "Error: create action requires name parameter"
            cmd.extend(["create", "configmap", args.name])
            
            if args.file_path:
                cmd.extend([f"--from-file={args.file_path}"])
            elif args.params and "from_literal" in args.params:
                for key, value in args.params["from_literal"].items():
                    cmd.extend([f"--from-literal={key}={value}"])
            else:
                return "Error: create action requires file_path or from_literal in params"
                
        elif args.action == "get":
            cmd.extend(["get", "configmaps"])
            if args.name:
                cmd.append(args.name)
            if args.output_format:
                cmd.extend(["-o", args.output_format])
                
        elif args.action == "delete":
            if not args.name:
                return "Error: delete action requires name parameter"
            cmd.extend(["delete", "configmap", args.name])
            
        else:
            return f"Unsupported configmap action: {args.action}"
        
        return await self._execute_command(cmd, args.timeout)
    
    async def _handle_secret(self, args: KubectlArgs) -> str:
        """Handle secret operations."""
        cmd = self._build_base_command(args)
        
        if args.action == "create":
            if not args.name:
                return "Error: create action requires name parameter"
            
            secret_type = args.params.get("type", "generic") if args.params else "generic"
            cmd.extend(["create", "secret", secret_type, args.name])
            
            if args.file_path:
                cmd.extend([f"--from-file={args.file_path}"])
            elif args.params and "from_literal" in args.params:
                for key, value in args.params["from_literal"].items():
                    cmd.extend([f"--from-literal={key}={value}"])
            else:
                return "Error: create action requires file_path or from_literal in params"
                
        elif args.action == "get":
            cmd.extend(["get", "secrets"])
            if args.name:
                cmd.append(args.name)
            if args.output_format:
                cmd.extend(["-o", args.output_format])
                
        elif args.action == "delete":
            if not args.name:
                return "Error: delete action requires name parameter"
            cmd.extend(["delete", "secret", args.name])
            
        else:
            return f"Unsupported secret action: {args.action}"
        
        return await self._execute_command(cmd, args.timeout)
    
    async def _handle_helm(self, args: KubectlArgs) -> str:
        """Handle Helm operations."""
        cmd = [self.helm_binary]
        
        if args.action == "install":
            if not args.release_name or not args.chart:
                return "Error: install action requires release_name and chart parameters"
            cmd.extend(["install", args.release_name, args.chart])
            
            if args.namespace:
                cmd.extend(["-n", args.namespace])
            if args.chart_version:
                cmd.extend(["--version", args.chart_version])
            if args.values_file:
                cmd.extend(["-f", args.values_file])
            if args.values:
                for key, value in args.values.items():
                    cmd.extend(["--set", f"{key}={value}"])
                    
        elif args.action == "upgrade":
            if not args.release_name or not args.chart:
                return "Error: upgrade action requires release_name and chart parameters"
            cmd.extend(["upgrade", args.release_name, args.chart])
            
            if args.namespace:
                cmd.extend(["-n", args.namespace])
            if args.chart_version:
                cmd.extend(["--version", args.chart_version])
            if args.values_file:
                cmd.extend(["-f", args.values_file])
            if args.values:
                for key, value in args.values.items():
                    cmd.extend(["--set", f"{key}={value}"])
                    
        elif args.action == "uninstall":
            if not args.release_name:
                return "Error: uninstall action requires release_name parameter"
            cmd.extend(["uninstall", args.release_name])
            if args.namespace:
                cmd.extend(["-n", args.namespace])
                
        elif args.action == "list":
            cmd.append("list")
            if args.namespace:
                cmd.extend(["-n", args.namespace])
            elif args.all_namespaces:
                cmd.append("-A")
                
        elif args.action == "status":
            if not args.release_name:
                return "Error: status action requires release_name parameter"
            cmd.extend(["status", args.release_name])
            if args.namespace:
                cmd.extend(["-n", args.namespace])
                
        elif args.action == "repo":
            repo_action = args.params.get("repo_action") if args.params else None
            if not repo_action:
                return "Error: repo action requires repo_action in params"
            
            if repo_action == "add":
                if not args.repo_name or not args.repo_url:
                    return "Error: repo add requires repo_name and repo_url parameters"
                cmd.extend(["repo", "add", args.repo_name, args.repo_url])
            elif repo_action == "update":
                cmd.extend(["repo", "update"])
            elif repo_action == "list":
                cmd.extend(["repo", "list"])
            else:
                return f"Unsupported repo action: {repo_action}"
                
        else:
            return f"Unsupported helm action: {args.action}"
        
        # Add kubeconfig for helm operations that interact with cluster
        if args.action in ["install", "upgrade", "uninstall", "list", "status"] and args.kubeconfig:
            cmd.extend(["--kubeconfig", args.kubeconfig])
        
        return await self._execute_command(cmd, args.timeout)
    
    async def _handle_namespace(self, args: KubectlArgs) -> str:
        """Handle namespace operations."""
        cmd = self._build_base_command(args)
        
        if args.action == "create":
            if not args.name:
                return "Error: create action requires name parameter"
            cmd.extend(["create", "namespace", args.name])
            
        elif args.action == "get":
            cmd.extend(["get", "namespaces"])
            if args.name:
                cmd.append(args.name)
            if args.output_format:
                cmd.extend(["-o", args.output_format])
                
        elif args.action == "delete":
            if not args.name:
                return "Error: delete action requires name parameter"
            cmd.extend(["delete", "namespace", args.name])
            
        elif args.action == "switch":
            if not args.name:
                return "Error: switch action requires name parameter"
            cmd.extend(["config", "set-context", "--current", f"--namespace={args.name}"])
            
        else:
            return f"Unsupported namespace action: {args.action}"
        
        return await self._execute_command(cmd, args.timeout)
    
    async def _handle_info(self, args: KubectlArgs) -> str:
        """Handle cluster info operations."""
        cmd = self._build_base_command(args)
        
        if args.action == "version":
            cmd.extend(["version"])
            
        elif args.action == "cluster-info":
            cmd.extend(["cluster-info"])
            
        elif args.action == "get-nodes":
            cmd.extend(["get", "nodes"])
            if args.output_format:
                cmd.extend(["-o", args.output_format])
                
        elif args.action == "get-namespaces":
            cmd.extend(["get", "namespaces"])
            if args.output_format:
                cmd.extend(["-o", args.output_format])
                
        elif args.action == "get-contexts":
            cmd.extend(["config", "get-contexts"])
            
        elif args.action == "current-context":
            cmd.extend(["config", "current-context"])
            
        else:
            return f"Unsupported info action: {args.action}"
        
        return await self._execute_command(cmd, args.timeout)
    
    async def _handle_generic(self, args: KubectlArgs) -> str:
        """Handle generic kubectl operations."""
        cmd = self._build_base_command(args)
        
        if args.action == "apply":
            if args.yaml_content:
                return await self._apply_yaml_content(args, args.yaml_content)
            elif args.file_path:
                cmd.extend(["apply", "-f", args.file_path])
            else:
                return "Error: apply action requires yaml_content or file_path"
                
        elif args.action == "get":
            resource_type = args.params.get("resource_type") if args.params else None
            if not resource_type:
                return "Error: get action requires resource_type in params"
            cmd.extend(["get", resource_type])
            if args.name:
                cmd.append(args.name)
            if args.labels:
                cmd.extend(["-l", self._format_labels(args.labels)])
            if args.output_format:
                cmd.extend(["-o", args.output_format])
                
        elif args.action == "describe":
            resource_type = args.params.get("resource_type") if args.params else None
            if not resource_type or not args.name:
                return "Error: describe action requires resource_type in params and name"
            cmd.extend(["describe", resource_type, args.name])
            
        elif args.action == "delete":
            resource_type = args.params.get("resource_type") if args.params else None
            if not resource_type or not args.name:
                return "Error: delete action requires resource_type in params and name"
            cmd.extend(["delete", resource_type, args.name])
            
        elif args.action == "custom":
            custom_args = args.params.get("custom_args") if args.params else None
            if not custom_args:
                return "Error: custom action requires custom_args in params"
            cmd.extend(custom_args)
            
        else:
            return f"Unsupported generic action: {args.action}"
        
        return await self._execute_command(cmd, args.timeout)
    
    async def _apply_yaml_content(self, args: KubectlArgs, yaml_content: str) -> str:
        """Apply YAML content using temporary file."""
        try:
            # Create temporary YAML file
            temp_file = self.working_directory / f"temp_kubectl_{os.getpid()}.yaml"
            
            # Write YAML content to file
            with open(temp_file, 'w') as f:
                f.write(yaml_content)
            
            # Build command
            cmd = self._build_base_command(args)
            cmd.extend(["apply", "-f", str(temp_file)])
            
            if args.dry_run:
                cmd.append("--dry-run=client")
            
            # Execute command
            result = await self._execute_command(cmd, args.timeout)
            
            # Clean up temporary file
            try:
                temp_file.unlink()
            except Exception:
                pass
            
            return result
            
        except Exception as e:
            return f"Error applying YAML content: {str(e)}"
    
    async def _execute_command(self, cmd: List[str], timeout: int) -> str:
        """Execute kubectl/helm command asynchronously."""
        try:
            self.logger.info(f"🔧 EXECUTING: {' '.join(cmd)}")
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
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
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # Check output size
            total_output_size = len(stdout_text.encode('utf-8')) + len(stderr_text.encode('utf-8'))
            if total_output_size > self.max_output_size:
                self.logger.error(f"❌ OUTPUT TOO LARGE: {total_output_size} bytes")
                return f"Error: Command output too large ({total_output_size} bytes). Maximum allowed: {self.max_output_size} bytes"
            
            # Format result
            result_parts = []
            result_parts.append(f"Command: {' '.join(cmd)}")
            result_parts.append(f"Exit code: {process.returncode}")
            
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
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool instance
        """
        return self.tool


def get_default_kubectl_tool() -> FunctionTool:
    """Get a default kubectl tool instance.
    
    Returns:
        FunctionTool instance
    """
    return KubectlTool().get_tool()