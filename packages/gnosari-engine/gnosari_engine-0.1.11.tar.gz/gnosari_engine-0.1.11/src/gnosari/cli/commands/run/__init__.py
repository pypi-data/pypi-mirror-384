"""Run command module."""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ...context import CLIContext


@click.group()
def cli():
    """Run team configurations."""
    pass


@cli.command()
@click.argument('team_path', type=click.Path(exists=True, path_type=Path))
@click.option('--message', '-m', required=True, help='Message to send to the team')
@click.option('--agent', '-a', help='Run only a specific agent from the team')
@click.option('--session-id', '-s', help='Session ID for conversation persistence')
@click.option('--api-key', help='OpenAI API key')
@click.option('--model', help='Model to use')
@click.option('--temperature', type=float, help='Model temperature')
@click.option('--stream', is_flag=True, help='Stream the response in real-time')
@click.option('--show-prompts', is_flag=True, help='Display the generated system prompts')
@click.pass_obj
def team(ctx: CLIContext, team_path: Path, message: str, agent: Optional[str] = None,
         session_id: Optional[str] = None, api_key: Optional[str] = None,
         model: Optional[str] = None, temperature: Optional[float] = None,
         stream: bool = False, show_prompts: bool = False):
    """Run team from YAML file or modular directory (auto-detects configuration type)."""
    
    try:
        result = asyncio.run(_execute_team(
            ctx=ctx,
            team_path=team_path,
            message=message,
            agent=agent,
            session_id=session_id,
            api_key=api_key,
            model=model,
            temperature=temperature,
            stream=stream,
            show_prompts=show_prompts
        ))
        
        if result.get('success', False):
            ctx.print_success("Team execution completed successfully")
        else:
            ctx.print_error(f"Team execution failed: {result.get('message', 'Unknown error')}")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to execute team: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


async def _execute_team(ctx: CLIContext, team_path: Path, message: str,
                       agent: Optional[str], session_id: Optional[str],
                       api_key: Optional[str], model: Optional[str],
                       temperature: Optional[float], stream: bool,
                       show_prompts: bool) -> dict:
    """Execute team with given parameters using clean service layer."""
    
    try:
        ctx.print_debug(f"Starting team execution for: {team_path}")
        
        # Use the service layer following SOLID principles
        from .team_service import create_team_execution_service
        
        team_service = create_team_execution_service()
        
        result = await team_service.execute_team(
            team_path=team_path,
            message=message,
            agent=agent,
            session_id=session_id,
            api_key=api_key,
            model=model,
            temperature=temperature,
            stream=stream,
            show_prompts=show_prompts,
            console=ctx.console,
            ctx=ctx
        )
        
        return result
        
    except Exception as e:
        ctx.print_error(f"Unexpected error during team execution: {e}")
        return {
            'success': False,
            'message': f'Team execution failed: {e}'
        }