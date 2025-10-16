"""Worker command module."""

import click
from ...context import CLIContext


@click.group()
def cli():
    """Worker management commands."""
    pass


@cli.command()
@click.option('--concurrency', '-c', type=int, default=1, help='Number of worker processes')
@click.option('--queue', '-Q', help='Comma-separated list of queues to consume from')
@click.option('--loglevel', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              default='INFO', help='Logging level')
@click.pass_obj
def start(ctx: CLIContext, concurrency: int, queue: str, loglevel: str):
    """Start Celery worker for async job processing."""
    try:
        from .start import WorkerStartCommand
        cmd = WorkerStartCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.concurrency = concurrency
                self.queue = queue
                self.loglevel = loglevel
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if not result.success:
            ctx.print_error(result.message or "Failed to start worker")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to start worker: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.option('--port', type=int, default=5555, help='Port for Flower UI')
@click.option('--auth', help='Basic auth in format user:password')
@click.pass_obj  
def flower(ctx: CLIContext, port: int, auth: str):
    """Run Flower UI for monitoring Celery tasks."""
    try:
        from .flower import FlowerCommand
        cmd = FlowerCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.port = port
                self.auth = auth
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if not result.success:
            ctx.print_error(result.message or "Failed to start Flower")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to start Flower: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)