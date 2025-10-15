"""Test command module for Gnosari CLI.

Provides comprehensive testing capabilities including:
- Agentic (AI-powered) testing
- Integration testing
- Test discovery and execution
- Test reporting and analytics

Following SOLID principles and Click framework patterns.
"""

import asyncio
from pathlib import Path
from typing import Optional, List

import click
from ...context import CLIContext


@click.group()
def cli():
    """Professional testing framework for Gnosari CLI commands."""
    pass


@cli.command()
@click.option('--command', '-c', help='Test specific command (e.g., structure, show-prompts)')
@click.option('--min-confidence', '-m', type=int, default=70, help='Minimum AI confidence threshold (0-100)')
@click.option('--env', '-e', default='development', help='Test environment (development, staging, production)')
@click.option('--report', '-r', type=click.Choice(['summary', 'detailed', 'json']), default='summary', help='Report format')
@click.option('--output', '-o', type=click.Path(), help='Output file for report')
@click.option('--parallel', '-p', is_flag=True, help='Run tests in parallel')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_obj
def agentic(ctx: CLIContext, command: Optional[str] = None, min_confidence: int = 70, 
           env: str = 'development', report: str = 'summary', output: Optional[str] = None,
           parallel: bool = False, verbose: bool = False):
    """Run AI-powered agentic tests for CLI commands.
    
    Examples:
        gnosari test agentic                           # Run all agentic tests
        gnosari test agentic --command structure       # Test structure command only
        gnosari test agentic --min-confidence 80       # Require 80% confidence
        gnosari test agentic --report detailed         # Detailed reporting
        gnosari test agentic --env staging             # Use staging environment
    """
    try:
        from .agentic_service import create_agentic_test_service
        
        # Create test execution context
        test_context = {
            'command': command,
            'min_confidence': min_confidence,
            'environment': env,
            'report_format': report,
            'output_file': output,
            'parallel': parallel,
            'verbose': verbose
        }
        
        # Execute agentic tests
        result = asyncio.run(_execute_agentic_tests(ctx, test_context))
        
        if result.get('success', False):
            ctx.print_success(f"Agentic tests completed: {result.get('summary', '')}")
        else:
            ctx.print_error(f"Agentic tests failed: {result.get('message', 'Unknown error')}")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to run agentic tests: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.argument('validator_name')
@click.option('--sample-output', '-s', type=click.Path(exists=True), help='Sample output file to validate')
@click.option('--config', '-c', type=click.Path(exists=True), help='Expected configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_obj
def validate_agent(ctx: CLIContext, validator_name: str, sample_output: Optional[str] = None,
                  config: Optional[str] = None, verbose: bool = False):
    """Validate specific AI agent with sample data.
    
    Examples:
        gnosari test validate-agent StructureValidator
        gnosari test validate-agent StructureValidator --sample-output output.txt
    """
    try:
        from .validator_service import create_validator_test_service
        
        # Create validator test context
        validator_context = {
            'validator_name': validator_name,
            'sample_output': sample_output,
            'config_file': config,
            'verbose': verbose
        }
        
        # Execute validator test
        result = asyncio.run(_execute_validator_test(ctx, validator_context))
        
        if result.get('success', False):
            ctx.print_success(f"Validator test completed: {result.get('summary', '')}")
        else:
            ctx.print_error(f"Validator test failed: {result.get('message', 'Unknown error')}")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to validate agent: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.option('--type', '-t', type=click.Choice(['all', 'agentic', 'integration', 'unit']), 
              default='all', help='Type of tests to discover')
@click.option('--command', '-c', help='Filter by command name')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'tree']), 
              default='table', help='Output format')
@click.pass_obj
def discover(ctx: CLIContext, type: str = 'all', command: Optional[str] = None, 
            format: str = 'table'):
    """Discover available tests and display test inventory.
    
    Examples:
        gnosari test discover                     # Discover all tests
        gnosari test discover --type agentic     # Discover agentic tests only
        gnosari test discover --command structure # Tests for structure command
        gnosari test discover --format json     # JSON output
    """
    try:
        from .discovery_service import create_test_discovery_service
        
        # Create discovery context
        discovery_context = {
            'test_type': type,
            'command_filter': command,
            'output_format': format
        }
        
        # Execute test discovery
        result = asyncio.run(_execute_test_discovery(ctx, discovery_context))
        
        if result.get('success', False):
            # Discovery results are displayed by the service
            pass
        else:
            ctx.print_error(f"Test discovery failed: {result.get('message', 'Unknown error')}")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to discover tests: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.option('--report-dir', '-d', type=click.Path(), default='tests/agentic/reports', 
              help='Report directory')
@click.option('--format', '-f', type=click.Choice(['html', 'pdf', 'json']), 
              default='html', help='Report format')
@click.option('--include-history', '-h', is_flag=True, help='Include historical data')
@click.pass_obj
def report(ctx: CLIContext, report_dir: str = 'tests/agentic/reports', 
          format: str = 'html', include_history: bool = False):
    """Generate comprehensive test reports and analytics.
    
    Examples:
        gnosari test report                      # Generate HTML report
        gnosari test report --format pdf        # Generate PDF report
        gnosari test report --include-history   # Include historical trends
    """
    try:
        from .reporting_service import create_reporting_service
        
        # Create reporting context
        reporting_context = {
            'report_directory': Path(report_dir),
            'output_format': format,
            'include_history': include_history
        }
        
        # Execute report generation
        result = asyncio.run(_execute_report_generation(ctx, reporting_context))
        
        if result.get('success', False):
            ctx.print_success(f"Report generated: {result.get('report_path', '')}")
        else:
            ctx.print_error(f"Report generation failed: {result.get('message', 'Unknown error')}")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to generate report: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


# Async execution functions (Service layer delegation)

async def _execute_agentic_tests(ctx: CLIContext, test_context: dict) -> dict:
    """Execute agentic tests using service layer."""
    try:
        from .agentic_service import create_agentic_test_service
        
        service = create_agentic_test_service()
        return await service.execute_tests(
            console=ctx.console,
            **test_context
        )
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Agentic test execution failed: {e}'
        }


async def _execute_validator_test(ctx: CLIContext, validator_context: dict) -> dict:
    """Execute validator test using service layer."""
    try:
        from .validator_service import create_validator_test_service
        
        service = create_validator_test_service()
        return await service.test_validator(
            console=ctx.console,
            **validator_context
        )
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Validator test failed: {e}'
        }


async def _execute_test_discovery(ctx: CLIContext, discovery_context: dict) -> dict:
    """Execute test discovery using service layer."""
    try:
        from .discovery_service import create_test_discovery_service
        
        service = create_test_discovery_service()
        return await service.discover_tests(
            console=ctx.console,
            **discovery_context
        )
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Test discovery failed: {e}'
        }


async def _execute_report_generation(ctx: CLIContext, reporting_context: dict) -> dict:
    """Execute report generation using service layer."""
    try:
        from .reporting_service import create_reporting_service
        
        service = create_reporting_service()
        return await service.generate_report(
            console=ctx.console,
            **reporting_context
        )
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Report generation failed: {e}'
        }