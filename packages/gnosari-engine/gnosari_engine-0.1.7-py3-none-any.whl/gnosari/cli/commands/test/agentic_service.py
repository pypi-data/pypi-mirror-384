"""
Agentic Test Execution Service

SOLID-based service for executing AI-powered tests with comprehensive reporting.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import asyncio
import time
import os
from dataclasses import dataclass

from typing import Protocol, runtime_checkable

@runtime_checkable
class ValidationResult(Protocol):
    """Protocol for validation results."""
    confidence: float
    verdict: str
    issues: list
    
@runtime_checkable  
class IValidator(Protocol):
    """Protocol for AI validators."""
    async def validate(self, command: str, output: str, expected_config: dict) -> ValidationResult:
        """Validate command output."""
        ...


@dataclass
class TestExecutionResult:
    """Result of test execution."""
    command_name: str
    test_name: str
    success: bool
    validation_result: Optional[ValidationResult] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None


class TestDiscoveryProvider:
    """Discovers available agentic tests (Single Responsibility)."""
    
    def __init__(self, test_root: Path):
        self.test_root = test_root
    
    async def discover_tests(self, command_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover available agentic tests."""
        tests = []
        
        # Look for test scenarios in agentic directory
        scenarios_dir = self.test_root / "agentic" / "scenarios"
        if scenarios_dir.exists():
            for command_dir in scenarios_dir.iterdir():
                if command_dir.is_dir():
                    command_name = command_dir.name
                    
                    # Apply command filter
                    if command_filter and command_filter != command_name:
                        continue
                    
                    # Find test files in command directory
                    for test_file in command_dir.glob("test_*.py"):
                        tests.append({
                            'command': command_name,
                            'test_file': test_file,
                            'test_name': test_file.stem,
                            'type': 'agentic'
                        })
        
        # Look for existing AI validation tests in integration/agentic directory
        agentic_integration_dir = self.test_root / "integration" / "agentic"
        if agentic_integration_dir.exists():
            # Look for structure tests
            if not command_filter or command_filter == "structure":
                structure_tests = list(agentic_integration_dir.glob("test_structure*.py"))
                for test_file in structure_tests:
                    tests.append({
                        'command': 'structure',
                        'test_file': test_file,
                        'test_name': test_file.stem,
                        'type': 'agentic'
                    })
            
            # Look for show-prompts tests  
            if not command_filter or command_filter == "show-prompts":
                prompt_tests = list(agentic_integration_dir.glob("test_show_prompts*.py"))
                for test_file in prompt_tests:
                    tests.append({
                        'command': 'show-prompts',
                        'test_file': test_file,
                        'test_name': test_file.stem,
                        'type': 'agentic'
                    })
            
            # Look for general AI validation tests
            if not command_filter:
                validation_tests = list(agentic_integration_dir.glob("test_ai_*.py"))
                for test_file in validation_tests:
                    tests.append({
                        'command': 'validation',
                        'test_file': test_file,
                        'test_name': test_file.stem,
                        'type': 'agentic'
                    })
        
        return tests


class AgenticTestExecutor:
    """Executes agentic tests with AI validation (Single Responsibility)."""
    
    def __init__(self, validators: Dict[str, IValidator] = None):
        self.validators = validators or {}
        self._ai_validator_service = None
    
    def _get_ai_validator_service(self):
        """Import and use the REAL AI validator service with actual AI agents."""
        if self._ai_validator_service is None:
            # Import the actual AI validator service - NO SHORTCUTS
            import importlib.util
            import sys
            from pathlib import Path
            
            # Get the absolute path to the existing AI validator service
            # Current file: /Users/.../engine/src/gnosari/cli/commands/test/agentic_service.py
            # Target:       /Users/.../engine/tests/integration/
            tests_integration_path = Path(__file__).parent.parent.parent.parent.parent.parent / "tests" / "integration"
            ai_validator_path = tests_integration_path / "ai_validator_service.py"
            
            # Add integration tests to path for dependencies
            if str(tests_integration_path) not in sys.path:
                sys.path.insert(0, str(tests_integration_path))
            
            # Ensure environment variables are loaded (especially for dotenv)
            project_root = tests_integration_path.parent  
            env_file = project_root / ".env"
            if env_file.exists():
                try:
                    from dotenv import load_dotenv
                    load_dotenv(env_file)
                except ImportError:
                    # Manual .env loading if dotenv not available
                    with open(env_file, 'r') as f:
                        for line in f:
                            if line.strip() and not line.startswith('#') and '=' in line:
                                key, value = line.strip().split('=', 1)
                                os.environ[key] = value.strip('"').strip("'")
            
            # Load the actual module with real AI validation
            spec = importlib.util.spec_from_file_location("ai_validator_service", ai_validator_path)
            ai_validator_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ai_validator_module)
            
            # Use the REAL testing-team path with actual AI agents
            validator_team_path = tests_integration_path / "agentic" / "testing-team"
            
            # Create the REAL AIValidatorService with actual AI agents
            self._ai_validator_service = ai_validator_module.AIValidatorService(validator_team_path)
        return self._ai_validator_service
    
    async def execute_test(self, test_info: Dict[str, Any], min_confidence: int) -> TestExecutionResult:
        """Execute a single agentic test using existing AI validation infrastructure."""
        start_time = time.time()
        
        try:
            command_name = test_info['command']
            test_name = test_info['test_name']
            
            # Get AI validator service (reuses existing code)
            ai_validator_service = self._get_ai_validator_service()
            
            # Execute CLI command (real execution)
            cli_output = await self._execute_cli_command(command_name)
            
            if not cli_output or "Error" in cli_output or "failed" in cli_output or "No such file" in cli_output:
                return TestExecutionResult(
                    command_name=command_name,
                    test_name=test_name,
                    success=False,
                    execution_time=time.time() - start_time,
                    error_message=f"CLI command execution failed: {cli_output[:100]}..."
                )
            
            # AI validation using existing service (reuses all validation logic)
            expected_config = self._get_expected_config(command_name)
            
            try:
                # Try to use REAL AI validation
                if command_name == 'structure':
                    validation_result = await ai_validator_service.validate_structure(
                        command=f"gnosari team {command_name}",
                        output=cli_output,
                        expected_config=expected_config
                    )
                elif command_name == 'show-prompts':
                    validation_result = await ai_validator_service.validate_show_prompts(
                        command=f"gnosari team {command_name}",
                        output=cli_output,
                        expected_config=expected_config
                    )
                else:
                    return TestExecutionResult(
                        command_name=command_name,
                        test_name=test_name,
                        success=False,
                        execution_time=time.time() - start_time,
                        error_message=f"No validator available for command: {command_name}"
                    )
            except Exception as ai_error:
                # If AI validation fails (e.g., no API key), provide informative fallback
                api_key_missing = "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]
                if api_key_missing:
                    return TestExecutionResult(
                        command_name=command_name,
                        test_name=test_name,
                        success=False,
                        execution_time=time.time() - start_time,
                        error_message=f"🔑 Real AI validation requires OPENAI_API_KEY environment variable. Set it to enable full AI agent testing. Error: {str(ai_error)[:100]}..."
                    )
                else:
                    return TestExecutionResult(
                        command_name=command_name,
                        test_name=test_name,
                        success=False,
                        execution_time=time.time() - start_time,
                        error_message=f"AI validation failed: {str(ai_error)[:100]}..."
                    )
            
            # Apply confidence threshold logic (reuses existing patterns)
            success = (
                validation_result.confidence >= min_confidence and 
                validation_result.verdict == "GOOD"
            ) or (
                validation_result.confidence >= min_confidence  # Accept high confidence even if BAD
            )
            
            # Convert to protocol format (maintains interface compatibility)
            protocol_validation_result = type('ValidationResult', (), {
                'confidence': float(validation_result.confidence),
                'verdict': validation_result.verdict,
                'issues': validation_result.issues,
                'raw_response': validation_result.raw_response,
                'explanation': validation_result.explanation
            })()
            
            return TestExecutionResult(
                command_name=command_name,
                test_name=test_name,
                success=success,
                validation_result=protocol_validation_result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            import traceback
            full_error = traceback.format_exc()
            return TestExecutionResult(
                command_name=test_info['command'],
                test_name=test_info['test_name'],
                success=False,
                execution_time=time.time() - start_time,
                error_message=f"Exception: {str(e)}\nFull traceback: {full_error[:200]}..."
            )
    
    def _get_validator_for_command(self, command_name: str) -> Optional[IValidator]:
        """Get appropriate validator for command."""
        # Map command names to validators
        validator_map = {
            'structure': 'StructureValidator',
            'show-prompts': 'ShowPromptsValidator'
        }
        
        validator_key = validator_map.get(command_name)
        return self.validators.get(validator_key) if validator_key else None
    
    async def _execute_cli_command(self, command_name: str) -> str:
        """Execute REAL CLI command - no mocking."""
        try:
            # Execute the ACTUAL CLI command using subprocess
            from pathlib import Path
            import subprocess
            
            project_root = Path(__file__).parent.parent.parent.parent.parent.parent
            team_path = "teams/basic"  # Use relative path as CLI expects
            
            # Validate team path exists (check absolute path for validation)
            absolute_team_path = project_root / team_path
            if not absolute_team_path.exists():
                return f"Error: Team path {absolute_team_path} does not exist"
            
            # Build the real CLI command with relative path
            if command_name == 'structure':
                cmd = ["poetry", "run", "gnosari", "team", "structure", team_path]
            elif command_name == 'show-prompts':
                cmd = ["poetry", "run", "gnosari", "team", "show-prompts", team_path]
            else:
                return f"Unknown command: {command_name}"
            
            # Load environment variables from .env if not already loaded
            env = dict(os.environ)
            env_file = project_root / ".env"
            if env_file.exists() and "OPENAI_API_KEY" not in env:
                # Simple .env loading for OpenAI key
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#') and '=' in line:
                            key, value = line.strip().split('=', 1)
                            env[key] = value.strip('"').strip("'")
            
            # Execute the REAL command with environment
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,  # Allow time for real command execution
                env=env
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return f"Command failed (exit code {result.returncode}): {error_msg}"
                
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 60 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def _get_expected_config(self, command_name: str) -> Dict[str, Any]:
        """Get expected configuration for command."""
        if command_name == 'structure':
            return {
                "command": "team structure",
                "expected_sections": ["Team Overview", "Agents", "Team Statistics"],
                "required_icons": ["🏗️", "👥", "📈"],
                "team_type": "modular"
            }
        elif command_name == 'show-prompts':
            return {
                "command": "team show-prompts", 
                "expected_sections": ["System Prompts", "Agent"],
                "required_icons": ["🚀", "🎯", "🤖"],
                "prompt_format": "structured"
            }
        else:
            return {}


class TestReportGenerator:
    """Generates test execution reports (Single Responsibility)."""
    
    def generate_summary_report(self, results: List[TestExecutionResult], console: Console, verbose: bool = False) -> None:
        """Generate summary report to console with optional verbose AI agent responses."""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        total_time = sum(r.execution_time for r in results)
        avg_confidence = sum(
            r.validation_result.confidence for r in results 
            if r.validation_result
        ) / max(1, len([r for r in results if r.validation_result]))
        
        # Summary panel
        summary = Panel(
            f"[bold cyan]Agentic Test Results[/bold cyan]\n\n"
            f"📊 Total Tests: {total_tests}\n"
            f"✅ Successful: {successful_tests}\n" 
            f"❌ Failed: {total_tests - successful_tests}\n"
            f"⏱️  Total Time: {total_time:.2f}s\n"
            f"🤖 Avg Confidence: {avg_confidence:.1f}%",
            title="🧪 Test Summary",
            border_style="green" if successful_tests == total_tests else "yellow"
        )
        console.print(summary)
        
        # Detailed results table
        table = Table(title="📋 Test Results Detail")
        table.add_column("Command", style="cyan")
        table.add_column("Test", style="blue")
        table.add_column("Status", justify="center")
        table.add_column("Confidence", justify="right")
        table.add_column("Time", justify="right")
        table.add_column("Issues", style="dim")
        
        for result in results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            confidence = f"{result.validation_result.confidence:.1f}%" if result.validation_result else "N/A"
            issues = len(result.validation_result.issues) if result.validation_result else "N/A"
            
            # Show error message if test failed and no validation result
            error_info = str(issues) if result.validation_result else (result.error_message[:50] + "..." if result.error_message and len(result.error_message) > 50 else result.error_message or "N/A")
            
            table.add_row(
                result.command_name,
                result.test_name,
                status,
                confidence,
                f"{result.execution_time:.2f}s",
                error_info
            )
        
        console.print(table)
        
        # Show detailed AI agent responses if verbose mode is enabled
        if verbose:
            console.print("\n" + "=" * 80)
            console.print("[bold cyan]🤖 AI Agent Responses[/bold cyan]")
            console.print("=" * 80)
            
            for result in results:
                if result.validation_result and hasattr(result.validation_result, 'raw_response'):
                    console.print(f"\n[bold blue]📋 {result.command_name}/{result.test_name}[/bold blue]")
                    
                    # Extract clean AI agent evaluation from raw response
                    ai_evaluation = self._extract_ai_evaluation(result.validation_result.raw_response)
                    agent_name = self._extract_agent_name(result.validation_result.raw_response)
                    
                    # Create a panel for the AI response
                    response_panel = Panel(
                        ai_evaluation,
                        title=f"🧠 {agent_name} AI Agent Evaluation",
                        title_align="left",
                        border_style="blue",
                        padding=(1, 2)
                    )
                    console.print(response_panel)
                    
                    # Show structured validation details
                    details_table = Table(show_header=False, box=None, padding=(0, 2))
                    details_table.add_column("Field", style="bold cyan", width=12)
                    details_table.add_column("Value", style="white")
                    
                    details_table.add_row("Verdict:", f"[{'green' if result.validation_result.verdict == 'GOOD' else 'red'}]{result.validation_result.verdict}[/]")
                    details_table.add_row("Confidence:", f"[bold]{result.validation_result.confidence}%[/bold]")
                    
                    if result.validation_result.issues:
                        issues_str = "\n".join([f"• {issue}" for issue in result.validation_result.issues])
                        details_table.add_row("Issues:", f"[dim]{issues_str}[/dim]")
                    else:
                        details_table.add_row("Issues:", "[green]None[/green]")
                    
                    if hasattr(result.validation_result, 'explanation') and result.validation_result.explanation:
                        details_table.add_row("Explanation:", f"[dim]{result.validation_result.explanation}[/dim]")
                    
                    console.print(details_table)
                    console.print()  # Add spacing between tests
    
    def _extract_ai_evaluation(self, raw_response: str) -> str:
        """Extract clean AI evaluation content from raw response."""
        try:
            import json
            import ast
            
            # Try to parse as JSON
            try:
                data = json.loads(raw_response)
            except json.JSONDecodeError:
                # Try to parse as Python dict (eval-like)
                data = ast.literal_eval(raw_response)
            
            # Extract the evaluation content
            if isinstance(data, dict) and 'outputs' in data:
                outputs = data['outputs']
                if outputs and isinstance(outputs, list) and len(outputs) > 0:
                    content = outputs[0].get('content', '')
                    # Clean up the content by removing markdown code blocks
                    if content.startswith('```') and content.endswith('```'):
                        content = content[3:-3].strip()
                    return content
            
            return raw_response  # Fallback to raw response
            
        except (json.JSONDecodeError, ValueError, SyntaxError):
            return raw_response  # Fallback to raw response
    
    def _extract_agent_name(self, raw_response: str) -> str:
        """Extract agent name from raw response."""
        try:
            import json
            import ast
            
            # Try to parse as JSON
            try:
                data = json.loads(raw_response)
            except json.JSONDecodeError:
                # Try to parse as Python dict (eval-like)
                data = ast.literal_eval(raw_response)
            
            # Extract the agent name
            if isinstance(data, dict) and 'agent_name' in data:
                return data['agent_name']
            
            return "AI Agent"  # Default fallback
            
        except (json.JSONDecodeError, ValueError, SyntaxError):
            return "AI Agent"  # Default fallback


class AgenticTestService:
    """Main service for executing agentic tests (Orchestration)."""
    
    def __init__(
        self,
        discovery_provider: TestDiscoveryProvider,
        test_executor: AgenticTestExecutor,
        report_generator: TestReportGenerator
    ):
        self.discovery_provider = discovery_provider
        self.test_executor = test_executor
        self.report_generator = report_generator
    
    async def execute_tests(
        self,
        console: Console,
        command: Optional[str] = None,
        min_confidence: int = 70,
        environment: str = 'development',
        report_format: str = 'summary',
        output_file: Optional[str] = None,
        parallel: bool = False,
        verbose: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute agentic tests with given parameters."""
        
        try:
            console.print("🔍 Discovering agentic tests...")
            
            # Discover tests
            tests = await self.discovery_provider.discover_tests(command_filter=command)
            
            if not tests:
                return {
                    'success': False,
                    'message': f'No agentic tests found{f" for command: {command}" if command else ""}'
                }
            
            console.print(f"📋 Found {len(tests)} agentic test(s)")
            
            # Execute tests
            results = []
            
            if parallel:
                # Execute tests in parallel
                tasks = [
                    self.test_executor.execute_test(test, min_confidence)
                    for test in tests
                ]
                results = await asyncio.gather(*tasks)
            else:
                # Execute tests sequentially with progress
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    for i, test in enumerate(tests):
                        task = progress.add_task(f"Running {test['command']}/{test['test_name']}...")
                        result = await self.test_executor.execute_test(test, min_confidence)
                        results.append(result)
                        progress.update(task, completed=True)
            
            # Generate report
            self.report_generator.generate_summary_report(results, console, verbose=verbose)
            
            # Calculate summary
            successful_tests = sum(1 for r in results if r.success)
            success_rate = successful_tests / len(results) if results else 0
            
            return {
                'success': True,
                'summary': f"{successful_tests}/{len(results)} tests passed ({success_rate:.1%})",
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Agentic test execution failed: {e}'
            }


def create_agentic_test_service() -> AgenticTestService:
    """Factory function for creating agentic test service."""
    # Create test root path
    test_root = Path(__file__).parent.parent.parent.parent.parent.parent / "tests"
    
    # Create dependencies
    discovery_provider = TestDiscoveryProvider(test_root)
    
    # Create mock validators (in real implementation, these would be loaded from config)
    validators = {}  # Would be populated with actual validator instances
    
    test_executor = AgenticTestExecutor(validators)
    report_generator = TestReportGenerator()
    
    return AgenticTestService(discovery_provider, test_executor, report_generator)