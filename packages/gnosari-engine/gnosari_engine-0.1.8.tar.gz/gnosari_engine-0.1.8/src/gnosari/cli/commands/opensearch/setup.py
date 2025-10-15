"""OpenSearch setup Click command."""

import asyncio
import os
from typing import Optional

import click

from ...context import CLIContext


@click.command()
@click.option('--host', default='localhost', help='OpenSearch host')
@click.option('--port', type=int, default=9200, help='OpenSearch port')
@click.option('--username', help='OpenSearch username')
@click.option('--password', help='OpenSearch password')
@click.option('--use-ssl', is_flag=True, help='Use SSL connection')
@click.option('--verify-certs', is_flag=True, help='Verify SSL certificates')
@click.option('--force', '-f', is_flag=True, help='Force recreate existing resources')
@click.option('--no-sample-data', is_flag=True, help='Skip sample data ingestion')
@click.option('--no-hybrid', is_flag=True, help='Disable hybrid search setup')
@click.pass_obj
def setup(ctx: CLIContext, host: str, port: int, username: Optional[str], 
          password: Optional[str], use_ssl: bool, verify_certs: bool,
          force: bool, no_sample_data: bool, no_hybrid: bool):
    """Set up OpenSearch for semantic search with OpenAI embeddings.

    This command creates a complete OpenSearch semantic search setup including:
    - OpenAI embedding model connector
    - Model group and deployment
    - Ingest pipeline for automatic text embedding
    - Search pipeline for hybrid search (optional)
    - Vector index optimized for semantic search
    - Sample data ingestion for testing

    Examples:
      gnosari opensearch setup                    # Basic setup with defaults
      gnosari opensearch setup --host localhost  # Custom host
      gnosari opensearch setup --force           # Force recreate existing resources
      gnosari opensearch setup --no-sample-data  # Skip sample data ingestion
      gnosari opensearch setup --no-hybrid       # Disable hybrid search setup
    """
    
    try:
        result = asyncio.run(_execute_setup(
            ctx=ctx,
            host=host,
            port=port,
            username=username,
            password=password,
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            force=force,
            no_sample_data=no_sample_data,
            no_hybrid=no_hybrid
        ))
        
        if result['success']:
            ctx.print_success(result.get('message', 'OpenSearch setup completed'))
        else:
            ctx.print_error(result.get('message', 'OpenSearch setup failed'))
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to setup OpenSearch: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


async def _execute_setup(ctx: CLIContext, host: str, port: int, username: Optional[str],
                        password: Optional[str], use_ssl: bool, verify_certs: bool,
                        force: bool, no_sample_data: bool, no_hybrid: bool) -> dict:
    """Execute the OpenSearch setup operation."""
    
    try:
        ctx.print_debug(f"Starting OpenSearch setup on {host}:{port}")
        
        # Validate environment
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return {
                'success': False,
                'message': 'OPENAI_API_KEY environment variable is required'
            }
        
        # Import OpenSearch adapter
        from ....knowledge.opensearch_adapter import OpenSearchAdapter
        
        # Create connection config
        connection_config = {
            'host': host,
            'port': port,
            'use_ssl': use_ssl,
            'verify_certs': verify_certs
        }
        
        if username and password:
            connection_config['http_auth'] = (username, password)
        
        # Initialize adapter
        adapter = OpenSearchAdapter(connection_config)
        
        # Test connection
        ctx.console.print("Testing OpenSearch connection...")
        if not await adapter.test_connection():
            return {
                'success': False,
                'message': f'Failed to connect to OpenSearch at {host}:{port}'
            }
        
        ctx.print_success("✓ Connected to OpenSearch")
        
        # Setup semantic search infrastructure
        setup_steps = [
            ("Creating OpenAI connector", adapter.create_openai_connector),
            ("Setting up model group", adapter.create_model_group),
            ("Deploying embedding model", adapter.deploy_embedding_model),
            ("Creating ingest pipeline", adapter.create_ingest_pipeline),
        ]
        
        if not no_hybrid:
            setup_steps.append(("Creating search pipeline", adapter.create_search_pipeline))
        
        setup_steps.extend([
            ("Creating vector index", adapter.create_vector_index),
        ])
        
        if not no_sample_data:
            setup_steps.append(("Ingesting sample data", adapter.ingest_sample_data))
        
        # Execute setup steps
        for step_name, step_func in setup_steps:
            try:
                with ctx.console.status(f"{step_name}..."):
                    if force:
                        # For force mode, try to cleanup existing resources first
                        cleanup_func_name = step_func.__name__.replace('create_', 'delete_').replace('deploy_', 'undeploy_').replace('ingest_', 'clear_')
                        ctx.print_debug(f"Looking for cleanup method: {cleanup_func_name}")
                        if hasattr(adapter, cleanup_func_name):
                            cleanup_func = getattr(adapter, cleanup_func_name)
                            try:
                                ctx.print_debug(f"Calling cleanup method: {cleanup_func_name}")
                                await cleanup_func()
                                ctx.print_debug(f"Cleaned up existing resources for {step_name}")
                            except Exception as cleanup_error:
                                ctx.print_debug(f"Cleanup failed (expected): {cleanup_error}")
                        else:
                            ctx.print_debug(f"No cleanup method found: {cleanup_func_name}")
                    
                    result = await step_func()
                    
                if result.get('success', True):
                    ctx.print_success(f"✓ {step_name}")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    if force and 'already exists' in str(error_msg).lower():
                        ctx.print_warning(f"⚠ {step_name} - resource already exists")
                    else:
                        ctx.print_error(f"✗ {step_name}: {error_msg}")
                        return {
                            'success': False,
                            'message': f'Setup failed at step: {step_name}'
                        }
                        
            except Exception as e:
                ctx.print_error(f"✗ {step_name}: {e}")
                return {
                    'success': False,
                    'message': f'Setup failed at step: {step_name}'
                }
        
        # Verify setup
        ctx.console.print("Verifying setup...")
        verification_result = await adapter.verify_setup()
        
        if verification_result.get('success', False):
            ctx.print_success("✓ OpenSearch semantic search setup verified")
            
            # Show setup summary
            ctx.console.print("\n[bold]Setup Summary:[/bold]")
            ctx.console.print(f"  • Host: {host}:{port}")
            ctx.console.print(f"  • SSL: {'Enabled' if use_ssl else 'Disabled'}")
            ctx.console.print(f"  • Hybrid search: {'Enabled' if not no_hybrid else 'Disabled'}")
            ctx.console.print(f"  • Sample data: {'Loaded' if not no_sample_data else 'Skipped'}")
            
            return {
                'success': True,
                'message': 'OpenSearch semantic search setup completed successfully'
            }
        else:
            error_msg = verification_result.get('error', 'Verification failed')
            return {
                'success': False,
                'message': f'Setup completed but verification failed: {error_msg}'
            }
        
    except Exception as e:
        ctx.print_error(f"Unexpected error during setup: {e}")
        return {
            'success': False,
            'message': f'Setup failed: {e}'
        }