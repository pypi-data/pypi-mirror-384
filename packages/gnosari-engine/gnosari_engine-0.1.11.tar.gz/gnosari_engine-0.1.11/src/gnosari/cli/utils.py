"""CLI utilities."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.logging import RichHandler


def setup_cli_logging(level: str = 'INFO', debug: bool = False) -> None:
    """Setup logging for the CLI application."""
    log_level = getattr(logging, level.upper())
    
    # Configure rich handler
    handler = RichHandler(
        rich_tracebacks=debug,
        show_time=debug,
        show_path=debug
    )
    
    # Configure logger
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("embedchain").setLevel(logging.WARNING)


def load_environment_variables() -> None:
    """Load environment variables from .env files."""
    # Load from project root .env file
    project_root = Path(__file__).parent.parent.parent.parent
    env_file = project_root / '.env'
    
    if env_file.exists():
        load_dotenv(env_file)
    
    # Also load from current directory
    current_env = Path.cwd() / '.env'
    if current_env.exists():
        load_dotenv(current_env)