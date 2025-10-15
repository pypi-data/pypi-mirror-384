"""OpenSearch command module."""

import click


@click.group()
def cli():
    """OpenSearch management commands."""
    pass


# Import commands from their respective modules
from .knowledge import preload
from .setup import setup

# Add commands to the CLI group
cli.add_command(preload)
cli.add_command(setup)