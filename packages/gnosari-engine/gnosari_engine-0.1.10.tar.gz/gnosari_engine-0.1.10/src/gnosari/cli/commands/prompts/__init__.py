"""Prompts command module."""

import click
from ...context import CLIContext


@click.group()
def cli():
    """Prompt management commands."""
    pass


@cli.command()
@click.pass_obj
def list(ctx: CLIContext):
    """List available prompt templates."""
    try:
        from .list import PromptsListCommand
        cmd = PromptsListCommand(ctx.console)
        
        import asyncio
        result = asyncio.run(cmd.run(None))
        
        if not result.success:
            ctx.print_error(result.message or "Failed to list prompts")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to list prompts: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.argument('prompt_name')
@click.pass_obj
def view(ctx: CLIContext, prompt_name: str):
    """View a specific prompt template."""
    try:
        from .view import PromptsViewCommand
        cmd = PromptsViewCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.prompt_name = prompt_name
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if not result.success:
            ctx.print_error(result.message or "Failed to view prompt")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to view prompt: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.argument('prompt_name')
@click.argument('variables', nargs=-1)
@click.pass_obj
def use(ctx: CLIContext, prompt_name: str, variables):
    """Use a prompt template with variable substitution."""
    try:
        from .use import PromptsUseCommand
        cmd = PromptsUseCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.prompt_name = prompt_name
                self.variables = dict(var.split('=', 1) for var in variables if '=' in var)
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if not result.success:
            ctx.print_error(result.message or "Failed to use prompt")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to use prompt: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.argument('prompt_name')
@click.option('--template', help='Template content for the prompt')
@click.option('--description', help='Description of the prompt')
@click.pass_obj
def create(ctx: CLIContext, prompt_name: str, template: str, description: str):
    """Create a new prompt template."""
    try:
        from .create import PromptsCreateCommand
        cmd = PromptsCreateCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.prompt_name = prompt_name
                self.template = template
                self.description = description
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if result.success:
            ctx.print_success(result.message or "Prompt created successfully")
        else:
            ctx.print_error(result.message or "Failed to create prompt")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to create prompt: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)