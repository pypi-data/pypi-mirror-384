"""Team structure visualization command for Gnosari Teams CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule

from ....engine.config.configuration_manager import ConfigurationManager


class StructureCommand:
    """Display comprehensive team structure including agents, tools, knowledge, and relationships."""
    
    def __init__(self, console: Console):
        """Initialize the command with a console."""
        self.console = console
    
    async def run(self, args) -> object:
        """Execute the structure command."""
        try:
            # Get team path from args
            team_path = Path(args.team_path)
            if not team_path.exists():
                return type('Result', (), {'success': False, 'message': f"Team path not found: {team_path}"})()
            
            # Load team configuration
            if team_path.is_dir():
                team_data = await self._load_modular_config(team_path)
            else:
                team_data = await self._load_monolithic_config(team_path)
            
            # Display based on format
            format_type = getattr(args, 'format', 'tree')
            detailed = getattr(args, 'detailed', False)
            
            if format_type == 'json':
                self._display_json(team_data, detailed)
            elif format_type == 'table':
                self._display_table(team_data, detailed)
            else:  # tree format (default)
                self._display_tree(team_data, detailed)
                
            return type('Result', (), {'success': True, 'message': "Team structure displayed successfully"})()
            
        except Exception as e:
            return type('Result', (), {'success': False, 'message': f"Failed to display team structure: {e}"})()
    
    async def _load_modular_config(self, team_path: Path) -> Dict[str, Any]:
        """Load modular team configuration."""
        config_manager = ConfigurationManager()
        modular_config = await config_manager.load_team_from_directory(team_path)
        
        # Convert to structured data
        team_data = {
            'name': modular_config.main.name,
            'description': modular_config.main.description,
            'version': getattr(modular_config.main, 'version', 'N/A'),
            'type': 'modular',
            'path': str(team_path),
            'learning': getattr(modular_config.main, 'learning', {}),
            'agents': {},
            'tools': {},
            'knowledge': {},
            'traits': {}
        }
        
        # Process agents
        for agent_id, agent_comp in modular_config.agents.items():
            agent_data = {
                'name': agent_comp.name or agent_id,
                'instructions': agent_comp.instructions or '',
                'orchestrator': agent_comp.orchestrator,
                'model': agent_comp.model,
                'temperature': agent_comp.temperature,
                'tools': agent_comp.tools or [],
                'knowledge': agent_comp.knowledge or [],
                'traits': getattr(agent_comp, 'traits', []),
                'learning': getattr(agent_comp, 'learning', []),
                'delegation': getattr(agent_comp, 'delegation', []),
                'trigger': getattr(agent_comp, 'trigger', [])
            }
            team_data['agents'][agent_id] = agent_data
        
        # Process tools
        for tool_id, tool_comp in modular_config.tools.items():
            tool_data = {
                'name': tool_comp.name or tool_id,
                'url': getattr(tool_comp, 'url', None),
                'connection_type': getattr(tool_comp, 'connection_type', None),
                'headers': getattr(tool_comp, 'headers', {}),
                'config': getattr(tool_comp, 'config', {})
            }
            team_data['tools'][tool_id] = tool_data
        
        # Process knowledge
        for knowledge_id, knowledge_comp in modular_config.knowledge.items():
            knowledge_data = {
                'name': knowledge_comp.name or knowledge_id,
                'type': knowledge_comp.type,
                'data': knowledge_comp.data or [],
                'config': getattr(knowledge_comp, 'config', {})
            }
            team_data['knowledge'][knowledge_id] = knowledge_data
        
        # Process traits
        for trait_id, trait_comp in modular_config.traits.items():
            trait_data = {
                'name': trait_comp.name or trait_id,
                'description': getattr(trait_comp, 'description', ''),
                'keywords': getattr(trait_comp, 'keywords', []),
                'behaviors': getattr(trait_comp, 'behaviors', [])
            }
            team_data['traits'][trait_id] = trait_data
        
        return team_data
    
    async def _load_monolithic_config(self, team_path: Path) -> Dict[str, Any]:
        """Load monolithic YAML team configuration."""
        import yaml
        
        with open(team_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        team_data = {
            'name': config.get('name', 'Unknown Team'),
            'description': config.get('description', ''),
            'version': config.get('version', 'N/A'),
            'type': 'monolithic',
            'path': str(team_path),
            'learning': config.get('learning', {}),
            'agents': {},
            'tools': {},
            'knowledge': {},
            'traits': {}
        }
        
        # Process agents
        for agent_config in config.get('agents', []):
            agent_id = agent_config.get('name', 'Unknown')
            team_data['agents'][agent_id] = {
                'name': agent_config.get('name', 'Unknown'),
                'instructions': agent_config.get('instructions', ''),
                'orchestrator': agent_config.get('orchestrator', False),
                'model': agent_config.get('model', 'default'),
                'temperature': agent_config.get('temperature', 1.0),
                'tools': agent_config.get('tools', []),
                'knowledge': agent_config.get('knowledge', []),
                'traits': agent_config.get('traits', []),
                'learning': agent_config.get('learning', []),
                'delegation': agent_config.get('delegation', []),
                'trigger': agent_config.get('trigger', [])
            }
        
        # Process tools (simplified for monolithic)
        for tool_name in set().union(*[agent.get('tools', []) for agent in config.get('agents', [])]):
            team_data['tools'][tool_name] = {
                'name': tool_name,
                'type': 'builtin',
                'description': f"Built-in tool: {tool_name}"
            }
        
        # Process knowledge
        for kb_config in config.get('knowledge', []):
            kb_name = kb_config.get('name', 'Unknown')
            team_data['knowledge'][kb_name] = {
                'name': kb_name,
                'type': kb_config.get('type', 'unknown'),
                'data': kb_config.get('data', []),
                'config': kb_config.get('config', {})
            }
        
        return team_data
    
    def _display_tree(self, team_data: Dict[str, Any], detailed: bool):
        """Display team structure as a visual tree."""
        # Main team info
        team_name = team_data['name']
        team_desc = team_data.get('description', '')
        team_type = team_data.get('type', 'unknown')
        
        self.console.print(Panel(
            f"[bold cyan]{team_name}[/bold cyan]\n"
            f"[dim]{team_desc}[/dim]\n"
            f"Type: [yellow]{team_type.title()}[/yellow] | "
            f"Version: [green]{team_data.get('version', 'N/A')}[/green] | "
            f"Agents: [blue]{len(team_data['agents'])}[/blue]",
            title="🏗️  Team Overview",
            border_style="cyan"
        ))
        
        # Create main tree
        tree = Tree(f"[bold]{team_name}[/bold]", guide_style="bright_blue")
        
        # Add learning configuration
        if team_data.get('learning'):
            learning_node = tree.add("🧠 [bold yellow]Learning Configuration[/bold yellow]")
            learning_config = team_data['learning']
            if isinstance(learning_config, dict):
                learning_node.add(f"Enabled: [green]{learning_config.get('enabled', 'false')}[/green]")
                if learning_config.get('learning_agent'):
                    learning_node.add(f"Learning Agent: [cyan]{learning_config['learning_agent']}[/cyan]")
                if learning_config.get('execution_mode'):
                    learning_node.add(f"Mode: [yellow]{learning_config['execution_mode']}[/yellow]")
                if learning_config.get('session_limit'):
                    learning_node.add(f"Session Limit: [blue]{learning_config['session_limit']}[/blue]")
        
        # Add agents
        if team_data['agents']:
            agents_node = tree.add("👥 [bold green]Agents[/bold green]")
            
            # Sort agents: orchestrator first
            sorted_agents = sorted(
                team_data['agents'].items(),
                key=lambda x: (not x[1]['orchestrator'], x[0])
            )
            
            for agent_id, agent in sorted_agents:
                role_emoji = "🎯" if agent['orchestrator'] else "🤖"
                role_text = "Orchestrator" if agent['orchestrator'] else "Worker"
                
                agent_node = agents_node.add(
                    f"{role_emoji} [bold]{agent['name']}[/bold] [dim]({role_text})[/dim]"
                )
                
                # Basic info
                if agent.get('model') and agent['model'] != 'default':
                    agent_node.add(f"🧠 Model: [cyan]{agent['model']}[/cyan]")
                if agent.get('temperature') is not None:
                    agent_node.add(f"🌡️  Temperature: [yellow]{agent['temperature']}[/yellow]")
                
                # Instructions preview
                if agent.get('instructions'):
                    instructions = agent['instructions'][:80] + "..." if len(agent['instructions']) > 80 else agent['instructions']
                    agent_node.add(f"📝 Instructions: [dim]{instructions}[/dim]")
                
                # Tools
                if agent.get('tools'):
                    tools_node = agent_node.add("🔧 [yellow]Tools[/yellow]")
                    for tool in agent['tools']:
                        tools_node.add(f"• {tool}")
                
                # Knowledge
                if agent.get('knowledge'):
                    knowledge_node = agent_node.add("📚 [blue]Knowledge[/blue]")
                    for kb in agent['knowledge']:
                        knowledge_node.add(f"• {kb}")
                
                # Traits
                if agent.get('traits'):
                    traits_node = agent_node.add("✨ [magenta]Traits[/magenta]")
                    for trait in agent['traits']:
                        traits_node.add(f"• {trait}")
                
                # Detailed information
                if detailed:
                    # Learning data
                    if agent.get('learning'):
                        learning_node = agent_node.add("🧠 [green]Learning Data[/green]")
                        for learning_item in agent['learning'][:3]:  # Show first 3
                            if isinstance(learning_item, dict):
                                priority = learning_item.get('priority', 'unknown')
                                content = learning_item.get('content', '')[:50] + "..."
                                learning_node.add(f"[{priority}] {content}")
                        if len(agent['learning']) > 3:
                            learning_node.add(f"... and {len(agent['learning']) - 3} more")
                    
                    # Delegation
                    if agent.get('delegation'):
                        delegation_node = agent_node.add("🔄 [orange1]Delegation[/orange1]")
                        for delegation in agent['delegation']:
                            if isinstance(delegation, dict):
                                target = delegation.get('agent', 'unknown')
                                mode = delegation.get('mode', 'sync')
                                delegation_node.add(f"➤ {target} ({mode})")
                    
                    # Triggers
                    if agent.get('trigger'):
                        trigger_node = agent_node.add("⚡ [red]Triggers[/red]")
                        for trigger in agent['trigger']:
                            if isinstance(trigger, dict):
                                event_type = trigger.get('event_type', 'unknown')
                                trigger_node.add(f"• {event_type}")
        
        # Add tools
        if team_data['tools']:
            tools_node = tree.add("🔧 [bold yellow]Tools[/bold yellow]")
            for tool_id, tool in team_data['tools'].items():
                tool_node = tools_node.add(f"🛠️  [bold]{tool['name']}[/bold]")
                
                if tool.get('url'):
                    tool_node.add(f"🌐 URL: [blue]{tool['url']}[/blue]")
                if tool.get('connection_type'):
                    tool_node.add(f"🔗 Type: [cyan]{tool['connection_type']}[/cyan]")
                
                if detailed and tool.get('config'):
                    config_node = tool_node.add("⚙️  [dim]Configuration[/dim]")
                    for key, value in list(tool['config'].items())[:3]:  # Show first 3 config items
                        config_node.add(f"{key}: {str(value)[:30]}...")
        
        # Add knowledge bases
        if team_data['knowledge']:
            knowledge_node = tree.add("📚 [bold blue]Knowledge Bases[/bold blue]")
            for kb_id, kb in team_data['knowledge'].items():
                kb_node = knowledge_node.add(f"📖 [bold]{kb['name']}[/bold]")
                kb_node.add(f"📊 Type: [cyan]{kb['type']}[/cyan]")
                
                if kb.get('data'):
                    data_node = kb_node.add("🗂️  [green]Data Sources[/green]")
                    for source in kb['data'][:3]:  # Show first 3 sources
                        data_node.add(f"• {source}")
                    if len(kb['data']) > 3:
                        data_node.add(f"... and {len(kb['data']) - 3} more")
                
                if detailed and kb.get('config'):
                    config_node = kb_node.add("⚙️  [dim]Configuration[/dim]")
                    if isinstance(kb['config'], dict):
                        for key, value in list(kb['config'].items())[:3]:
                            config_node.add(f"{key}: {str(value)[:30]}...")
        
        # Add traits
        if team_data['traits']:
            traits_node = tree.add("✨ [bold magenta]Traits[/bold magenta]")
            for trait_id, trait in team_data['traits'].items():
                trait_node = traits_node.add(f"⭐ [bold]{trait['name']}[/bold]")
                if trait.get('description'):
                    desc = trait['description'][:60] + "..." if len(trait['description']) > 60 else trait['description']
                    trait_node.add(f"📄 {desc}")
                
                if detailed:
                    if trait.get('keywords'):
                        keywords_node = trait_node.add("🏷️  [yellow]Keywords[/yellow]")
                        for keyword in trait['keywords'][:5]:  # Show first 5
                            keywords_node.add(f"• {keyword}")
                    
                    if trait.get('behaviors'):
                        behaviors_node = trait_node.add("🎭 [green]Behaviors[/green]")
                        for behavior in trait['behaviors'][:3]:  # Show first 3
                            behaviors_node.add(f"• {behavior}")
        
        self.console.print()
        self.console.print(tree)
        
        # Summary statistics
        self.console.print()
        self._display_summary_stats(team_data)
    
    def _display_table(self, team_data: Dict[str, Any], detailed: bool):
        """Display team structure as tables."""
        self.console.print(Panel(
            f"[bold cyan]{team_data['name']}[/bold cyan] - Team Structure",
            title="📊 Table View"
        ))
        
        # Agents table
        if team_data['agents']:
            agents_table = Table(
                title="👥 Agents",
                show_header=True,
                header_style="bold magenta"
            )
            agents_table.add_column("Name", style="cyan")
            agents_table.add_column("Role", style="yellow")
            agents_table.add_column("Model", style="green")
            agents_table.add_column("Tools", style="blue")
            agents_table.add_column("Knowledge", style="purple")
            
            if detailed:
                agents_table.add_column("Traits", style="magenta")
                agents_table.add_column("Learning Items", style="orange1")
            
            for agent_id, agent in team_data['agents'].items():
                role = "🎯 Orchestrator" if agent['orchestrator'] else "🤖 Worker"
                tools = ", ".join(agent.get('tools', [])[:3])
                if len(agent.get('tools', [])) > 3:
                    tools += f" (+{len(agent['tools']) - 3})"
                
                knowledge = ", ".join(agent.get('knowledge', [])[:2])
                if len(agent.get('knowledge', [])) > 2:
                    knowledge += f" (+{len(agent['knowledge']) - 2})"
                
                row = [
                    agent['name'],
                    role,
                    agent.get('model', 'default'),
                    tools or "None",
                    knowledge or "None"
                ]
                
                if detailed:
                    traits = ", ".join(agent.get('traits', [])[:2])
                    if len(agent.get('traits', [])) > 2:
                        traits += f" (+{len(agent['traits']) - 2})"
                    
                    learning_count = len(agent.get('learning', []))
                    learning_text = f"{learning_count} items" if learning_count > 0 else "None"
                    
                    row.extend([traits or "None", learning_text])
                
                agents_table.add_row(*row)
            
            self.console.print(agents_table)
        
        # Tools table
        if team_data['tools']:
            tools_table = Table(
                title="🔧 Tools",
                show_header=True,
                header_style="bold yellow"
            )
            tools_table.add_column("Name", style="cyan")
            tools_table.add_column("Type", style="yellow")
            tools_table.add_column("URL/Description", style="blue")
            
            for tool_id, tool in team_data['tools'].items():
                tool_type = tool.get('connection_type', tool.get('type', 'builtin'))
                url_or_desc = tool.get('url', tool.get('description', 'N/A'))
                
                tools_table.add_row(
                    tool['name'],
                    tool_type,
                    url_or_desc[:50] + "..." if len(str(url_or_desc)) > 50 else str(url_or_desc)
                )
            
            self.console.print(tools_table)
        
        # Knowledge table
        if team_data['knowledge']:
            kb_table = Table(
                title="📚 Knowledge Bases",
                show_header=True,
                header_style="bold blue"
            )
            kb_table.add_column("Name", style="cyan")
            kb_table.add_column("Type", style="yellow")
            kb_table.add_column("Sources", style="green")
            
            for kb_id, kb in team_data['knowledge'].items():
                sources = ", ".join(kb.get('data', [])[:2])
                if len(kb.get('data', [])) > 2:
                    sources += f" (+{len(kb['data']) - 2})"
                
                kb_table.add_row(
                    kb['name'],
                    kb['type'],
                    sources or "None"
                )
            
            self.console.print(kb_table)
    
    def _display_json(self, team_data: Dict[str, Any], detailed: bool):
        """Display team structure as JSON."""
        if not detailed:
            # Remove detailed fields for non-detailed view
            simplified_data = {
                'name': team_data['name'],
                'description': team_data.get('description', ''),
                'type': team_data.get('type'),
                'agents': {
                    agent_id: {
                        'name': agent['name'],
                        'orchestrator': agent['orchestrator'],
                        'tools': agent.get('tools', []),
                        'knowledge': agent.get('knowledge', [])
                    }
                    for agent_id, agent in team_data['agents'].items()
                },
                'tools': {tool_id: tool['name'] for tool_id, tool in team_data['tools'].items()},
                'knowledge': {kb_id: kb['name'] for kb_id, kb in team_data['knowledge'].items()}
            }
            team_data = simplified_data
        
        self.console.print_json(json.dumps(team_data, indent=2))
    
    def _display_summary_stats(self, team_data: Dict[str, Any]):
        """Display summary statistics."""
        orchestrators = sum(1 for agent in team_data['agents'].values() if agent['orchestrator'])
        workers = len(team_data['agents']) - orchestrators
        
        total_tools = len(team_data['tools'])
        total_knowledge = len(team_data['knowledge'])
        total_traits = len(team_data['traits'])
        
        # Learning stats
        agents_with_learning = sum(
            1 for agent in team_data['agents'].values() 
            if agent.get('learning') and len(agent['learning']) > 0
        )
        
        # Tool usage stats
        tool_usage = {}
        for agent in team_data['agents'].values():
            for tool in agent.get('tools', []):
                tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        most_used_tool = max(tool_usage.items(), key=lambda x: x[1]) if tool_usage else None
        
        stats_table = Table(
            title="📈 Team Statistics",
            show_header=False,
            box=None,
            padding=(0, 2)
        )
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("👥 Total Agents", str(len(team_data['agents'])))
        stats_table.add_row("🎯 Orchestrators", str(orchestrators))
        stats_table.add_row("🤖 Workers", str(workers))
        stats_table.add_row("🔧 Tools", str(total_tools))
        stats_table.add_row("📚 Knowledge Bases", str(total_knowledge))
        stats_table.add_row("✨ Traits", str(total_traits))
        stats_table.add_row("🧠 Agents with Learning", str(agents_with_learning))
        
        if most_used_tool:
            stats_table.add_row("🏆 Most Used Tool", f"{most_used_tool[0]} ({most_used_tool[1]} agents)")
        
        self.console.print(Panel(stats_table, border_style="green"))