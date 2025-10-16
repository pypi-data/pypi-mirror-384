"""Flower UI command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
import os
import subprocess

from ...base import SyncCommand
from ...exceptions import ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse


@register_command("worker")
class FlowerCommand(SyncCommand):
    """Run Flower UI for monitoring Celery tasks."""
    
    name = "flower"
    description = "Run Flower UI for monitoring Celery tasks"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            '--port', '-p',
            type=int,
            default=5555,
            help='Port to run Flower on (default: 5555)'
        )
        parser.add_argument(
            '--auth',
            help='Basic auth in format user:password (default: admin:admin)'
        )
        parser.add_argument(
            '--broker',
            help='Broker URL (default: redis://localhost:6379/0)'
        )
        parser.add_argument(
            '--url-prefix',
            help='URL prefix for Flower (useful when running behind a proxy)'
        )
        parser.add_argument(
            '--max-tasks',
            type=int,
            default=10000,
            help='Maximum number of tasks to keep in memory (default: 10000)'
        )
    
    def execute_sync(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the flower command."""
        try:
            # Set environment variables for Flower
            env = os.environ.copy()
            if args.broker:
                env['CELERY_BROKER_URL'] = args.broker
            
            # Build flower command
            flower_cmd = [
                "celery", "-A", "gnosari.queue.app.celery_app", "flower",
                f"--port={args.port}",
                f"--max-tasks={args.max_tasks}"
            ]
            
            # Add basic auth if specified
            auth = args.auth or "admin:admin"
            flower_cmd.append(f"--basic-auth={auth}")
            
            # Add URL prefix if specified
            if args.url_prefix:
                flower_cmd.append(f"--url-prefix={args.url_prefix}")
            
            self.console.print(f"🌸 [bold green]Starting Flower UI[/bold green]")
            self.console.print(f"[blue]Port:[/blue] {args.port}")
            self.console.print(f"[blue]URL:[/blue] http://localhost:{args.port}")
            self.console.print(f"[blue]Authentication:[/blue] {auth}")
            if args.url_prefix:
                self.console.print(f"[blue]URL Prefix:[/blue] {args.url_prefix}")
            if args.broker:
                self.console.print(f"[blue]Broker:[/blue] {args.broker}")
            
            self.console.print("\n[dim]Press Ctrl+C to stop Flower[/dim]")
            
            try:
                subprocess.run(flower_cmd, env=env, check=True)
                return CommandResponse(
                    success=True,
                    message="Flower UI started successfully"
                )
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Flower stopped by user[/yellow]")
                return CommandResponse(
                    success=True,
                    message="Flower stopped by user",
                    exit_code=130
                )
            except subprocess.CalledProcessError as e:
                raise ConfigurationError(f"Error running Flower: {e}")
                
        except Exception as e:
            self.logger.error(f"Flower command failed: {e}")
            raise ConfigurationError(f"Failed to start Flower UI: {e}")