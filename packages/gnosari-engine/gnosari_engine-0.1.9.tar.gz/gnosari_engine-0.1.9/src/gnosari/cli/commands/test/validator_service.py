"""
Validator Testing Service

SOLID-based service for testing individual AI validators with sample data.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import json
import time
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
class ValidatorTestResult:
    """Result of validator testing."""
    validator_name: str
    success: bool
    validation_result: Optional[ValidationResult] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    sample_data_used: Optional[str] = None


class ValidatorRegistry:
    """Registry for available validators (Single Responsibility)."""
    
    def __init__(self):
        self._validators: Dict[str, IValidator] = {}
    
    def register_validator(self, name: str, validator: IValidator) -> None:
        """Register a validator."""
        self._validators[name] = validator
    
    def get_validator(self, name: str) -> Optional[IValidator]:
        """Get validator by name."""
        return self._validators.get(name)
    
    def list_validators(self) -> Dict[str, str]:
        """List available validators with descriptions."""
        return {
            name: getattr(validator, 'description', 'No description available')
            for name, validator in self._validators.items()
        }


class SampleDataProvider:
    """Provides sample data for validator testing (Single Responsibility)."""
    
    def __init__(self, test_root: Path):
        self.test_root = test_root
    
    def get_sample_output(self, validator_name: str, sample_file: Optional[str] = None) -> Optional[str]:
        """Get sample output data for validator testing."""
        if sample_file:
            # Use provided sample file
            sample_path = Path(sample_file)
            if sample_path.exists():
                return sample_path.read_text()
            return None
        
        # Look for default sample files
        samples_dir = self.test_root / "agentic" / "samples"
        if not samples_dir.exists():
            return None
        
        # Try to find matching sample file
        for pattern in [f"{validator_name.lower()}.txt", f"{validator_name.lower()}_output.txt"]:
            sample_path = samples_dir / pattern
            if sample_path.exists():
                return sample_path.read_text()
        
        return None
    
    def get_expected_config(self, validator_name: str, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Get expected configuration for validator testing."""
        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path) as f:
                    return json.load(f)
        
        # Default configurations for known validators
        default_configs = {
            "StructureValidator": {
                "command": "team structure",
                "expected_sections": ["Team Overview", "Agents", "Team Statistics"],
                "required_icons": ["🏗️", "👥", "📈"],
                "team_type": "modular"
            },
            "ShowPromptsValidator": {
                "command": "team show-prompts",
                "expected_sections": ["System Prompts", "Agent"],
                "required_icons": ["🚀", "🎯", "🤖"],
                "prompt_format": "structured"
            }
        }
        
        return default_configs.get(validator_name, {})


class ValidatorTester:
    """Tests individual validators (Single Responsibility)."""
    
    def __init__(self, registry: ValidatorRegistry, data_provider: SampleDataProvider):
        self.registry = registry
        self.data_provider = data_provider
    
    async def test_validator(
        self, 
        validator_name: str, 
        sample_output: Optional[str] = None,
        config_file: Optional[str] = None
    ) -> ValidatorTestResult:
        """Test a specific validator with sample data."""
        start_time = time.time()
        
        try:
            # Get validator
            validator = self.registry.get_validator(validator_name)
            if not validator:
                return ValidatorTestResult(
                    validator_name=validator_name,
                    success=False,
                    execution_time=time.time() - start_time,
                    error_message=f"Validator '{validator_name}' not found"
                )
            
            # Get sample data
            sample_data = self.data_provider.get_sample_output(validator_name, sample_output)
            if not sample_data:
                return ValidatorTestResult(
                    validator_name=validator_name,
                    success=False,
                    execution_time=time.time() - start_time,
                    error_message="No sample data available for testing"
                )
            
            # Get expected config
            expected_config = self.data_provider.get_expected_config(validator_name, config_file)
            
            # Run validation
            validation_result = await validator.validate(
                command=f"gnosari test-command",
                output=sample_data,
                expected_config=expected_config
            )
            
            return ValidatorTestResult(
                validator_name=validator_name,
                success=True,
                validation_result=validation_result,
                execution_time=time.time() - start_time,
                sample_data_used=sample_data[:200] + "..." if len(sample_data) > 200 else sample_data
            )
            
        except Exception as e:
            return ValidatorTestResult(
                validator_name=validator_name,
                success=False,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )


class ValidatorTestReporter:
    """Generates validator test reports (Single Responsibility)."""
    
    def generate_test_report(self, result: ValidatorTestResult, console: Console) -> None:
        """Generate validator test report."""
        # Status panel
        status_color = "green" if result.success else "red"
        status_text = "✅ SUCCESS" if result.success else "❌ FAILED"
        
        panel_content = f"[bold {status_color}]{status_text}[/bold {status_color}]\\n\\n"
        panel_content += f"🤖 Validator: {result.validator_name}\\n"
        panel_content += f"⏱️  Execution Time: {result.execution_time:.3f}s\\n"
        
        if result.success and result.validation_result:
            panel_content += f"🎯 Confidence: {result.validation_result.confidence:.1f}%\\n"
            panel_content += f"📊 Verdict: {result.validation_result.verdict}\\n"
            panel_content += f"🔍 Issues Found: {len(result.validation_result.issues)}\\n"
        
        if result.error_message:
            panel_content += f"❌ Error: {result.error_message}\\n"
        
        status_panel = Panel(
            panel_content,
            title=f"🧪 Validator Test: {result.validator_name}",
            border_style=status_color
        )
        console.print(status_panel)
        
        # Validation details if successful
        if result.success and result.validation_result:
            self._print_validation_details(result.validation_result, console)
        
        # Sample data used
        if result.sample_data_used:
            sample_panel = Panel(
                result.sample_data_used,
                title="📋 Sample Data Used",
                border_style="dim"
            )
            console.print(sample_panel)
    
    def _print_validation_details(self, validation_result: ValidationResult, console: Console) -> None:
        """Print detailed validation results."""
        if validation_result.issues:
            table = Table(title="🔍 Validation Issues")
            table.add_column("Type", style="cyan")
            table.add_column("Description", style="yellow")
            table.add_column("Severity", justify="center")
            
            for issue in validation_result.issues:
                table.add_row(
                    issue.get('type', 'Unknown'),
                    issue.get('description', 'No description'),
                    issue.get('severity', 'Unknown')
                )
            
            console.print(table)
        
        # AI reasoning
        if hasattr(validation_result, 'reasoning') and validation_result.reasoning:
            reasoning_panel = Panel(
                validation_result.reasoning,
                title="🧠 AI Reasoning",
                border_style="blue"
            )
            console.print(reasoning_panel)


class ValidatorTestService:
    """Main service for validator testing (Orchestration)."""
    
    def __init__(
        self,
        registry: ValidatorRegistry,
        tester: ValidatorTester,
        reporter: ValidatorTestReporter
    ):
        self.registry = registry
        self.tester = tester
        self.reporter = reporter
    
    async def test_validator(
        self,
        console: Console,
        validator_name: str,
        sample_output: Optional[str] = None,
        config_file: Optional[str] = None,
        verbose: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Test a specific validator."""
        try:
            console.print(f"🧪 Testing validator: {validator_name}")
            
            # List available validators if requested validator not found
            if not self.registry.get_validator(validator_name):
                available = list(self.registry.list_validators().keys())
                return {
                    'success': False,
                    'message': f"Validator '{validator_name}' not found. Available: {', '.join(available)}"
                }
            
            # Run validator test
            result = await self.tester.test_validator(
                validator_name=validator_name,
                sample_output=sample_output,
                config_file=config_file
            )
            
            # Generate report
            self.reporter.generate_test_report(result, console)
            
            return {
                'success': result.success,
                'summary': f"Validator test {'passed' if result.success else 'failed'}",
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Validator test execution failed: {e}'
            }
    
    async def list_validators(self, console: Console) -> Dict[str, Any]:
        """List available validators."""
        try:
            validators = self.registry.list_validators()
            
            if not validators:
                console.print("[yellow]No validators registered[/yellow]")
                return {'success': True, 'validators': {}}
            
            # Display validators table
            table = Table(title="🤖 Available Validators")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="white")
            
            for name, description in validators.items():
                table.add_row(name, description)
            
            console.print(table)
            
            return {
                'success': True,
                'validators': validators,
                'summary': f"Found {len(validators)} validator(s)"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to list validators: {e}'
            }


def create_validator_test_service() -> ValidatorTestService:
    """Factory function for creating validator test service."""
    # Create test root path
    test_root = Path(__file__).parent.parent.parent.parent.parent.parent / "tests"
    
    # Create dependencies
    registry = ValidatorRegistry()
    data_provider = SampleDataProvider(test_root)
    tester = ValidatorTester(registry, data_provider)
    reporter = ValidatorTestReporter()
    
    # Register mock validators (in real implementation, load from config)
    # registry.register_validator("StructureValidator", StructureValidatorImpl())
    # registry.register_validator("ShowPromptsValidator", ShowPromptsValidatorImpl())
    
    return ValidatorTestService(registry, tester, reporter)