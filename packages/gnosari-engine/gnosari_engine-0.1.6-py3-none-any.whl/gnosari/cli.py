"""Gnosari Teams CLI - New modular architecture with backward compatibility."""

from __future__ import annotations

# Suppress warnings before any imports
import warnings
import os
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", message=".*deprecated.*")
warnings.filterwarnings("ignore", message=".*Support for class-based.*")
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"

from typing import NoReturn

def main(argv=None) -> NoReturn:
    """Main entry point for the gnosari CLI with new architecture."""
    print("DEBUG: main() function called")
    # Import and register all commands BEFORE creating the CLI router
    try:
        from .cli.registry import registry
        from .cli.commands import team, modular, worker, prompts
        # Auto-discover any additional commands
        registry.auto_discover_commands('gnosari.cli.commands')
        
        # Debug: show registered commands
        print(f"DEBUG: Registered commands: {registry.list_all_commands()}")
        print(f"DEBUG: Command groups: {registry.list_commands()}")
            
    except ImportError as e:
        print(f"Warning: Could not import some command modules: {e}")
    
    # Import CLI router after commands are registered
    from .cli.router import create_cli_app
    
    # Create and run CLI app
    app = create_cli_app()
    app.run(argv)


if __name__ == "__main__":
    main()