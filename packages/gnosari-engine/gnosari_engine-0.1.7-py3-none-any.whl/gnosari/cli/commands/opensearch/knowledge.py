"""Knowledge preload Click command."""

import asyncio
import logging
from typing import Optional
from pathlib import Path

import click
from rich.table import Table
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from ...context import CLIContext
from ....core.exceptions import KnowledgeError


@click.command()
@click.argument('team_path', type=click.Path(exists=True, path_type=Path))
@click.option('--knowledge-base', '--kb', help='Specific knowledge base name to preload')
@click.option('--recursive', '-r', is_flag=True, help='Recursively preload all teams in directory')
@click.option('--force', '-f', is_flag=True, help='Force cleanup and reload of existing data')
@click.option('--batch-size', type=int, default=100, help='Batch size for processing')
@click.option('--list', 'list_only', is_flag=True, help='List available knowledge bases without preloading')
@click.pass_obj
def preload(ctx: CLIContext, team_path: Path, knowledge_base: Optional[str], 
           recursive: bool, force: bool, batch_size: int, list_only: bool):
    """Preload knowledge bases into OpenSearch for improved runtime performance.
    
    This command processes team configurations and loads knowledge bases
    that use the OpenSearch provider, indexing their data for faster queries.
    
    Examples:
      gnosari opensearch preload teams/my-team         # Preload team knowledge
      gnosari opensearch preload teams/my-team --kb docs  # Preload specific KB
      gnosari opensearch preload teams/ --recursive   # Preload all teams
      gnosari opensearch preload --list               # List available knowledge bases
      gnosari opensearch preload teams/my-team --force # Force cleanup and reload
    """
    
    try:
        result = asyncio.run(_execute_preload(
            ctx=ctx,
            team_path=team_path,
            knowledge_base=knowledge_base,
            recursive=recursive,
            force=force,
            batch_size=batch_size,
            list_only=list_only
        ))
        
        if result['success']:
            ctx.print_success(result.get('message', 'Knowledge preload completed'))
        else:
            ctx.print_error(result.get('message', 'Knowledge preload failed'))
            import sys
            sys.exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to preload knowledge: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        import sys
        sys.exit(1)


async def _execute_preload(ctx: CLIContext, team_path: Path, knowledge_base: Optional[str],
                          recursive: bool, force: bool, batch_size: int, list_only: bool) -> dict:
    """Execute the knowledge preload operation."""
    
    try:
        ctx.print_debug(f"Starting knowledge preload for: {team_path}")
        
        # Import required modules
        from ....engine.config.configuration_manager import ConfigurationManager
        from ....knowledge.manager import KnowledgeManager
        
        config_manager = ConfigurationManager()
        knowledge_manager = KnowledgeManager()
        
        # Discover team configurations
        team_configs = []
        if recursive and team_path.is_dir():
            # Find all team configurations recursively
            for config_file in team_path.rglob("*.yaml"):
                if config_file.name in ["team.yaml", "main.yaml"] or (
                    config_file.is_file() and 
                    not config_file.parent.name.startswith(".") and
                    config_file.name.endswith("team.yaml")
                ):
                    team_configs.append(config_file)
        else:
            # Single team configuration
            if team_path.is_file():
                # Single YAML file
                team_configs.append(team_path)
            elif team_path.is_dir():
                # Check for modular team configuration (team.yaml or main.yaml)
                team_yaml = team_path / "team.yaml"
                main_yaml = team_path / "main.yaml"
                if team_yaml.exists():
                    team_configs.append(team_yaml)
                elif main_yaml.exists():
                    team_configs.append(main_yaml)
                else:
                    ctx.print_error(f"No team.yaml or main.yaml found in directory: {team_path}")
                    return {'success': False, 'message': 'No valid team configuration found'}
        
        if not team_configs:
            ctx.print_error("No team configurations found")
            return {'success': False, 'message': 'No team configurations found'}
        
        ctx.print_debug(f"Found {len(team_configs)} team configuration(s)")
        
        # Process each team configuration
        total_processed = 0
        total_errors = 0
        
        for team_config_path in team_configs:
            try:
                ctx.print_debug(f"Processing team configuration: {team_config_path}")
                
                # Load team configuration
                if team_config_path.name in ["team.yaml", "main.yaml"] and (
                    (team_config_path.parent / "agents").exists() or
                    (team_config_path.parent / "tools").exists() or
                    (team_config_path.parent / "knowledge").exists()
                ):
                    # Modular configuration - load from directory
                    modular_config = await config_manager.load_team_from_directory(team_config_path.parent)
                    team_config = await config_manager.convert_to_legacy_format(modular_config)
                else:
                    # Monolithic configuration - load single file
                    import yaml
                    with open(team_config_path, 'r') as f:
                        team_config = yaml.safe_load(f)
                
                # Extract knowledge bases
                knowledge_configs = team_config.get('knowledge', [])
                if not knowledge_configs:
                    ctx.print_debug(f"No knowledge bases found in {team_config_path}")
                    continue
                
                # Filter by specific knowledge base if requested
                if knowledge_base:
                    knowledge_configs = [kb for kb in knowledge_configs if kb.get('name') == knowledge_base]
                    if not knowledge_configs:
                        ctx.print_warning(f"Knowledge base '{knowledge_base}' not found in {team_config_path}")
                        continue
                
                # List mode - just show available knowledge bases
                if list_only:
                    table = Table(title=f"Knowledge Bases in {team_config_path.name}")
                    table.add_column("Name", style="cyan")
                    table.add_column("Type", style="green")
                    table.add_column("Provider", style="yellow")
                    table.add_column("Data Sources", style="blue")
                    
                    for kb in knowledge_configs:
                        # Provider can be in 'provider' field or 'config.provider'
                        provider_info = kb.get('provider', {})
                        if isinstance(provider_info, dict) and 'type' in provider_info:
                            provider_type = provider_info.get('type')
                        else:
                            # Check config.provider for modular configs
                            config = kb.get('config', {})
                            provider_type = config.get('provider', 'embedchain')
                        
                        data_sources = ', '.join([str(source) for source in kb.get('data', [])])
                        
                        table.add_row(
                            kb.get('name', 'Unknown'),
                            kb.get('type', 'Unknown'),
                            provider_type,
                            data_sources[:50] + "..." if len(data_sources) > 50 else data_sources
                        )
                    
                    ctx.console.print(table)
                    continue
                
                # Process OpenSearch knowledge bases
                opensearch_kbs = []
                for kb in knowledge_configs:
                    ctx.print_debug(f"Checking KB: {kb.get('name')} - Provider: {kb.get('provider')} - Config: {kb.get('config', {}).get('provider')}")
                    
                    # Check provider in different possible locations
                    provider_info = kb.get('provider', {})
                    if isinstance(provider_info, dict) and provider_info.get('type') == 'opensearch':
                        ctx.print_debug(f"Found OpenSearch KB via provider.type: {kb.get('name')}")
                        opensearch_kbs.append(kb)
                    else:
                        # Check config.provider for modular configs
                        config = kb.get('config', {})
                        if config.get('provider') == 'opensearch':
                            ctx.print_debug(f"Found OpenSearch KB via config.provider: {kb.get('name')}")
                            opensearch_kbs.append(kb)
                
                if not opensearch_kbs:
                    ctx.print_debug(f"No OpenSearch knowledge bases found in {team_config_path}")
                    continue
                
                ctx.console.print(f"[bold]Processing {len(opensearch_kbs)} OpenSearch knowledge base(s) from {team_config_path.name}[/bold]")
                
                for kb_config in opensearch_kbs:
                    kb_name = kb_config.get('name', 'unknown')
                    
                    try:
                        ctx.console.print(f"  Processing knowledge base: [cyan]{kb_name}[/cyan]")
                        
                        # Determine KB ID following original logic:
                        # - For single file teams: use 'id' field from YAML
                        # - For modular teams: use filename
                        if team_config_path.name in ["team.yaml", "main.yaml"] and (
                            (team_config_path.parent / "agents").exists() or
                            (team_config_path.parent / "tools").exists() or
                            (team_config_path.parent / "knowledge").exists()
                        ):
                            # Modular configuration - use filename (directory name)
                            kb_id = kb_config.get('id', team_config_path.parent.name)
                        else:
                            # Single file - use id field from YAML
                            kb_id = kb_config.get('id', kb_name.lower().replace(' ', '_'))
                        
                        kb_type = kb_config.get('type', 'unknown')
                        
                        ctx.print_debug(f"Using KB ID: {kb_id} for knowledge base: {kb_name}")
                        
                        # Handle force option - invalidate cache if requested
                        if force:
                            ctx.console.print(f"  [yellow]Force option enabled - clearing cache for {kb_name}[/yellow]")
                            knowledge_manager.invalidate_knowledge_cache(kb_id)
                        
                        # Extract provider from config and put it at top level for KnowledgeManager
                        config_for_manager = kb_config.copy()
                        nested_config = config_for_manager.get('config', {})
                        if 'provider' in nested_config:
                            config_for_manager['provider'] = nested_config['provider']
                        
                        ctx.print_debug(f"Creating KB with config provider: {config_for_manager.get('provider')}")
                        
                        # Check if knowledge base already exists
                        if knowledge_manager.knowledge_base_exists(kb_name) and not force:
                            ctx.print_debug(f"Knowledge base {kb_name} already exists, skipping creation")
                            kb = knowledge_manager.get_knowledge_base(kb_name)
                            
                            # Initialize if needed
                            if not kb.is_initialized():
                                await kb.initialize()
                            
                            result = {'success': True, 'documents_processed': 0}
                        else:
                            # Create or recreate the knowledge base
                            try:
                                kb = knowledge_manager.create_knowledge_base(
                                    name=kb_name,
                                    kb_type=kb_type,
                                    config=config_for_manager,
                                    knowledge_id=kb_id
                                )
                                
                                # Initialize if needed
                                if not kb.is_initialized():
                                    await kb.initialize()
                                
                                # Load data sources into the knowledge base
                                data_sources = kb_config.get('data', [])
                                total_docs_processed = 0
                                
                                # Create progress bar for data source loading
                                with Progress(
                                    SpinnerColumn(),
                                    TextColumn("[bold blue]{task.description}"),
                                    BarColumn(),
                                    TextColumn("({task.completed}/{task.total} sources)"),
                                    TextColumn("[green]{task.fields[docs_processed]} docs"),
                                    TimeElapsedColumn(),
                                    console=ctx.console,
                                    transient=True
                                ) as progress:
                                    # Add task for this knowledge base
                                    task_id = progress.add_task(
                                        f"Loading {kb_name}",
                                        total=len(data_sources),
                                        docs_processed=0
                                    )
                                    
                                    for idx, source in enumerate(data_sources):
                                        # Update progress with current source
                                        source_display = str(source)
                                        if len(source_display) > 50:
                                            source_display = source_display[:47] + "..."
                                        progress.update(task_id, description=f"Loading {kb_name}: {source_display}")
                                        
                                        # Load data and get document count directly from the manager
                                        docs_added = await knowledge_manager.add_data_to_knowledge_base(
                                            kb_name=kb_name,
                                            data=str(source),
                                            source=str(source)
                                        )
                                        
                                        total_docs_processed += docs_added
                                        
                                        # Update progress with completion and document count
                                        progress.update(
                                            task_id, 
                                            advance=1, 
                                            docs_processed=total_docs_processed,
                                            description=f"Loading {kb_name}: {source_display} ✓"
                                        )
                                
                                result = {
                                    'success': True,
                                    'documents_processed': total_docs_processed
                                }
                                
                            except Exception as e:
                                raise KnowledgeError(f"Failed to create knowledge base '{kb_name}': {e}")
                        
                        if result.get('success', False):
                            docs_count = result.get('documents_processed', 0)
                            ctx.print_success(f"  ✓ Loaded {docs_count} documents for {kb_name}")
                            total_processed += docs_count
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            ctx.print_error(f"  ✗ Failed to load {kb_name}: {error_msg}")
                            total_errors += 1
                            
                    except Exception as e:
                        ctx.print_error(f"  ✗ Error processing {kb_name}: {e}")
                        total_errors += 1
                        
            except Exception as e:
                ctx.print_error(f"Error processing team configuration {team_config_path}: {e}")
                total_errors += 1
        
        # Return results
        if list_only:
            return {'success': True, 'message': 'Knowledge base listing completed'}
        
        if total_errors > 0:
            message = f"Completed with errors. Processed {total_processed} documents, {total_errors} errors"
        else:
            message = f"Successfully processed {total_processed} documents"
        
        return {
            'success': total_errors == 0,
            'message': message,
            'documents_processed': total_processed,
            'errors': total_errors
        }
        
    except Exception as e:
        ctx.print_error(f"Unexpected error during preload: {e}")
        return {
            'success': False,
            'message': f"Preload failed: {e}"
        }