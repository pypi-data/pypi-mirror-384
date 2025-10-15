"""Team pull command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Set

import aiohttp
import yaml

from ...base import AsyncCommand
from ...exceptions import ValidationError, NetworkError, ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse
from ...utils import ensure_directory_exists, sanitize_filename


def detect_env_variables(config: dict) -> Set[str]:
    """Detect required environment variables from configuration."""
    env_vars = set()
    
    def _recursive_search(obj, path: str = "") -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                _recursive_search(value, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                _recursive_search(item, new_path)
        elif isinstance(obj, str):
            # Look for environment variable patterns
            env_pattern = r'\$\{([^}]+)\}'
            matches = re.findall(env_pattern, obj)
            env_vars.update(matches)
    
    _recursive_search(config)
    return env_vars


def generate_env_example(env_vars: Set[str]) -> str:
    """Generate example .env file content."""
    if not env_vars:
        return ""
    
    lines = ["# Environment variables for Gnosari Teams", ""]
    
    for var in sorted(env_vars):
        if var.endswith('_API_KEY'):
            lines.append(f"{var}=your-api-key-here")
        elif var.endswith('_URL'):
            lines.append(f"{var}=https://api.example.com")
        elif var.endswith('_MODEL'):
            lines.append(f"{var}=gpt-4o")
        elif var.endswith('_TEMPERATURE'):
            lines.append(f"{var}=1.0")
        else:
            lines.append(f"{var}=your-value-here")
    
    return "\n".join(lines)


def transform_json_to_yaml(team_data: dict) -> dict:
    """Transform JSON team data to YAML format for better readability."""
    # Create a copy to avoid modifying original
    transformed = team_data.copy()
    
    # Ensure proper ordering of main fields
    ordered_config = {}
    
    # Main identification fields first
    if 'id' in transformed:
        ordered_config['id'] = transformed['id']
    if 'name' in transformed:
        ordered_config['name'] = transformed['name']
    if 'description' in transformed:
        ordered_config['description'] = transformed['description']
    
    # Configuration sections
    for key in ['knowledge', 'tools', 'agents']:
        if key in transformed:
            ordered_config[key] = transformed[key]
    
    # Any remaining fields
    for key, value in transformed.items():
        if key not in ordered_config:
            ordered_config[key] = value
    
    return ordered_config


@register_command("team")
class PullCommand(AsyncCommand):
    """Pull team configuration from Gnosari API."""
    
    name = "pull"
    description = "Pull team configuration from Gnosari API"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'team_identifier',
            help='Team identifier to pull from the API'
        )
        parser.add_argument(
            'output_directory',
            nargs='?',
            default='./teams',
            help='Output directory for the team (default: ./teams)'
        )
        parser.add_argument(
            '--api-url',
            help='Gnosari API URL (default: https://api.gnosari.com or GNOSARI_API_URL env var)'
        )
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command arguments."""
        # Basic validation - team_identifier is required (handled by argparse)
        return True
    
    async def execute(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the pull command."""
        try:
            # Default API URL if not provided
            api_url = args.api_url or os.getenv("GNOSARI_API_URL", "https://api.gnosari.com")
            
            # Build API endpoint URL
            if not api_url.endswith("/api/v1/teams/pull"):
                # Only add endpoint if it's a base URL
                from urllib.parse import urlparse
                parsed = urlparse(api_url)
                if parsed.path in ['', '/']:
                    api_url = api_url.rstrip("/") + "/api/v1/teams/pull"
            
            self.console.print(f"[blue]Pulling team configuration...[/blue]")
            self.console.print(f"[blue]Team identifier:[/blue] {args.team_identifier}")
            self.console.print(f"[blue]API URL:[/blue] {api_url}")
            
            # Make HTTP request
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Accept': 'application/json'
                }
                
                # Add authentication header if API key is available
                api_key = os.getenv("GNOSARI_API_KEY")
                if api_key:
                    headers['X-Auth-Token'] = api_key
                else:
                    self.console.print("[yellow]Warning: GNOSARI_API_KEY not found in environment variables[/yellow]")
                
                # Build request URL with team identifier
                request_url = f"{api_url}?team_id={args.team_identifier}"
                
                self.logger.debug(f"Making HTTP GET request to: {request_url}")
                self.logger.debug(f"Request headers: {dict(headers)}")
                
                try:
                    async with session.get(request_url, headers=headers) as response:
                        response_text = await response.text()
                        
                        self.logger.debug(f"Response status: {response.status}")
                        self.logger.debug(f"Response headers: {dict(response.headers)}")
                        self.logger.debug(f"Response body: {response_text}")
                        
                        if response.status == 200:
                            try:
                                team_data = await response.json()
                                
                                # Extract team information
                                team_name = team_data.get('name', args.team_identifier)
                                team_id = team_data.get('id', args.team_identifier)
                                
                                self.console.print(f"[green]✅ Successfully retrieved team configuration![/green]")
                                self.console.print(f"[green]Team name:[/green] {team_name}")
                                self.console.print(f"[green]Team ID:[/green] {team_id}")
                                
                                # Create output directory
                                output_dir = Path(args.output_directory)
                                ensure_directory_exists(output_dir)
                                
                                # Sanitize team name for filename
                                safe_team_name = sanitize_filename(team_name)
                                
                                # Generate YAML filename
                                yaml_filename = f"{safe_team_name}.yaml"
                                yaml_path = output_dir / yaml_filename
                                
                                # Transform data for better YAML output
                                transformed_data = transform_json_to_yaml(team_data)
                                
                                # Write YAML file
                                with open(yaml_path, 'w', encoding='utf-8') as f:
                                    yaml.dump(
                                        transformed_data,
                                        f,
                                        default_flow_style=False,
                                        sort_keys=False,
                                        indent=2,
                                        allow_unicode=True
                                    )
                                
                                self.console.print(f"[green]Team configuration saved to:[/green] {yaml_path}")
                                
                                # Detect environment variables and create .env.example if needed
                                env_vars = detect_env_variables(transformed_data)
                                if env_vars:
                                    env_example_path = output_dir / f"{safe_team_name}.env.example"
                                    env_content = generate_env_example(env_vars)
                                    
                                    with open(env_example_path, 'w', encoding='utf-8') as f:
                                        f.write(env_content)
                                    
                                    self.console.print(f"[green]Environment variables example saved to:[/green] {env_example_path}")
                                    self.console.print(f"[yellow]Found {len(env_vars)} environment variables in configuration[/yellow]")
                                    
                                    for var in sorted(env_vars):
                                        self.console.print(f"  - {var}")
                                
                                return CommandResponse(
                                    success=True,
                                    message="Team configuration pulled successfully",
                                    data={
                                        "team_name": team_name,
                                        "team_id": team_id,
                                        "yaml_path": str(yaml_path),
                                        "env_vars": list(env_vars)
                                    }
                                )
                            
                            except json.JSONDecodeError as e:
                                raise ConfigurationError(f"Invalid JSON response from API: {e}")
                        
                        elif response.status == 401:
                            raise NetworkError(
                                "Authentication failed. Please check your GNOSARI_API_KEY environment variable.",
                                exit_code=1
                            )
                        
                        elif response.status == 404:
                            raise ValidationError(f"Team not found: {args.team_identifier}")
                        
                        else:
                            try:
                                error_data = await response.json()
                                error_message = error_data.get('message', f'HTTP {response.status}')
                            except json.JSONDecodeError:
                                error_message = f"HTTP {response.status}: {response_text}"
                            
                            raise NetworkError(f"Failed to pull team configuration: {error_message}")
                
                except aiohttp.ClientError as e:
                    raise NetworkError(f"Network error while pulling team configuration: {e}")
        
        except ValidationError:
            raise
        except NetworkError:
            raise
        except Exception as e:
            self.logger.error(f"Pull command failed: {e}")
            raise ConfigurationError(f"Failed to pull team configuration: {e}")