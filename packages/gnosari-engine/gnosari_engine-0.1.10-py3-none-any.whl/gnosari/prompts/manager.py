"""Prompt template management utilities for Gnosari CLI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from rich.console import Console
from rich.syntax import Syntax
from rich.markdown import Markdown


class PromptManager:
    """Manages prompt templates in the prompts directory."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        """Initialize prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt templates
        """
        self.prompts_dir = Path(prompts_dir)
        self.console = Console()
    
    def list_prompts(self) -> List[str]:
        """List all available prompt templates.
        
        Returns:
            List of prompt template names (without .md extension)
        """
        if not self.prompts_dir.exists():
            return []
        
        return [
            file.stem for file in self.prompts_dir.glob("*.md")
            if file.is_file()
        ]
    
    def get_prompt_path(self, name: str) -> Path:
        """Get the full path to a prompt template.
        
        Args:
            name: Prompt template name (without .md extension)
            
        Returns:
            Path to the prompt template file
        """
        return self.prompts_dir / f"{name}.md"
    
    def prompt_exists(self, name: str) -> bool:
        """Check if a prompt template exists.
        
        Args:
            name: Prompt template name (without .md extension)
            
        Returns:
            True if the prompt template exists
        """
        return self.get_prompt_path(name).exists()
    
    def extract_variables(self, content: str) -> Set[str]:
        """Extract variable placeholders from prompt content.
        
        Args:
            content: Prompt template content
            
        Returns:
            Set of variable names found in the template
        """
        # Find all {variable_name} patterns
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, content)
        
        # Filter out common markdown/formatting patterns that aren't variables
        variables = set()
        for match in matches:
            # Skip if it looks like a language identifier for code blocks
            if match.lower() in ['python', 'yaml', 'bash', 'json', 'toml', 'md']:
                continue
            # Skip if it contains spaces (likely not a variable)
            if ' ' in match:
                continue
            variables.add(match)
        
        return variables
    
    def get_prompt_variables(self, name: str) -> Set[str]:
        """Get all variables required by a prompt template.
        
        Args:
            name: Prompt template name (without .md extension)
            
        Returns:
            Set of variable names required by the template
            
        Raises:
            FileNotFoundError: If the prompt template doesn't exist
        """
        prompt_path = self.get_prompt_path(name)
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template '{name}' not found")
        
        content = prompt_path.read_text(encoding='utf-8')
        return self.extract_variables(content)
    
    def substitute_variables(self, content: str, variables: Dict[str, str]) -> str:
        """Substitute variables in prompt content.
        
        Args:
            content: Prompt template content
            variables: Dictionary mapping variable names to values
            
        Returns:
            Content with variables substituted
        """
        result = content
        for var_name, var_value in variables.items():
            pattern = f"{{{var_name}}}"
            result = result.replace(pattern, var_value)
        return result
    
    def substitute_variables_partial(self, content: str, variables: Dict[str, str]) -> str:
        """Substitute only provided variables in prompt content, leaving others as placeholders.
        
        Args:
            content: Prompt template content
            variables: Dictionary mapping variable names to values (partial substitution)
            
        Returns:
            Content with provided variables substituted, others left as {variable}
        """
        result = content
        for var_name, var_value in variables.items():
            pattern = f"{{{var_name}}}"
            result = result.replace(pattern, var_value)
        return result
    
    def use_prompt(self, name: str, variables: Dict[str, str]) -> str:
        """Use a prompt template with partial variable substitution.
        
        Args:
            name: Prompt template name (without .md extension)
            variables: Dictionary mapping variable names to values (partial substitution allowed)
            
        Returns:
            Processed prompt content with provided variables substituted, others left as placeholders
            
        Raises:
            FileNotFoundError: If the prompt template doesn't exist
        """
        prompt_path = self.get_prompt_path(name)
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template '{name}' not found")
        
        content = prompt_path.read_text(encoding='utf-8')
        
        # Use partial substitution - no variables are required
        return self.substitute_variables_partial(content, variables)
    
    def display_processed_prompt(self, name: str, message: str, variables: Dict[str, str], format_type: str = "rich"):
        """Display a processed prompt with message and variable substitution.
        
        Args:
            name: Prompt template name (without .md extension)
            message: Message for the prompt processing
            variables: Dictionary of variables to substitute
            format_type: Output format - "rich" for formatted display or "markdown" for plain markdown
        """
        try:
            # Process the prompt with variables
            processed_content = self.use_prompt(name, variables)
            
            if format_type == "markdown":
                # Plain markdown output - just print the content
                print(processed_content)
            else:
                # Rich formatted output (default)
                self.console.print(f"[bold green]Processed Prompt Template:[/bold green] {name}")
                self.console.print(f"[bold green]Message:[/bold green] {message}")
                self.console.print("=" * 60)
                
                # Display processed content as markdown
                from rich.markdown import Markdown
                markdown = Markdown(processed_content)
                self.console.print(markdown)
                
                self.console.print("\n" + "=" * 60)
                self.console.print(f"[bold cyan]Prompt ready to use with message:[/bold cyan] {message}")
                
        except FileNotFoundError as e:
            if format_type == "rich":
                self.console.print(f"[red]Error: {e}[/red]")
                self.console.print(f"[yellow]Available prompts:[/yellow]")
                available = self.list_prompts()
                for prompt in sorted(available):
                    self.console.print(f"  • {prompt}")
            else:
                print(f"Error: {e}")
        except Exception as e:
            if format_type == "rich":
                self.console.print(f"[red]Unexpected error: {e}[/red]")
            else:
                print(f"Error: {e}")
    
    def display_prompt_list(self):
        """Display list of available prompt templates."""
        prompts = self.list_prompts()
        
        if not prompts:
            self.console.print("[yellow]No prompt templates found in prompts/ directory[/yellow]")
            return
        
        self.console.print("[bold cyan]Available Prompt Templates:[/bold cyan]\n")
        
        for prompt_name in sorted(prompts):
            try:
                variables = self.get_prompt_variables(prompt_name)
                var_count = len(variables)
                var_info = f"({var_count} variables)" if var_count > 0 else "(no variables)"
                
                self.console.print(f"  [green]•[/green] [bold]{prompt_name}[/bold] [dim]{var_info}[/dim]")
            except Exception as e:
                self.console.print(f"  [green]•[/green] [bold]{prompt_name}[/bold] [red](error reading: {e})[/red]")
    
    def display_prompt_content(self, name: str, variables: Dict[str, str] = None, format_type: str = "rich"):
        """Display the content of a prompt template with optional variable substitution.
        
        Args:
            name: Prompt template name (without .md extension)
            variables: Optional dictionary of variables to substitute for preview
            format_type: Output format - "rich" for formatted display or "markdown" for plain markdown
        """
        if not self.prompt_exists(name):
            self.console.print(f"[red]Error: Prompt template '{name}' not found[/red]")
            return
        
        prompt_path = self.get_prompt_path(name)
        content = prompt_path.read_text(encoding='utf-8')
        
        # Get all variables from template
        all_variables = self.extract_variables(content)
        
        # Substitute provided variables if any
        if variables:
            content = self.substitute_variables_partial(content, variables)
        
        if format_type == "markdown":
            # Plain markdown output - just print the content
            print(content)
        else:
            # Rich formatted output (default)
            # Determine what to show in header
            if variables:
                substituted_vars = set(variables.keys()) & all_variables
                remaining_vars = all_variables - substituted_vars
                
                self.console.print(f"[bold blue]Prompt Template:[/bold blue] {name} [dim](preview with variables)[/dim]")
                self.console.print(f"[bold blue]File:[/bold blue] {prompt_path}")
                
                if substituted_vars:
                    self.console.print(f"[bold green]Substituted variables:[/bold green] {', '.join(sorted(substituted_vars))}")
                if remaining_vars:
                    self.console.print(f"[bold yellow]Remaining variables:[/bold yellow] {', '.join(sorted(remaining_vars))}")
            else:
                self.console.print(f"[bold blue]Prompt Template:[/bold blue] {name}")
                self.console.print(f"[bold blue]File:[/bold blue] {prompt_path}")
                
                # Show variables if any
                if all_variables:
                    self.console.print(f"[bold blue]Variables:[/bold blue] {', '.join(sorted(all_variables))}")
                else:
                    self.console.print("[bold blue]Variables:[/bold blue] none")
            
            self.console.print("\n" + "="*60)
            
            # Display content as markdown
            markdown = Markdown(content)
            self.console.print(markdown)
    
    def display_prompt_variables(self, name: str):
        """Display only the variables required by a prompt template.
        
        Args:
            name: Prompt template name (without .md extension)
        """
        if not self.prompt_exists(name):
            self.console.print(f"[red]Error: Prompt template '{name}' not found[/red]")
            return
        
        try:
            variables = self.get_prompt_variables(name)
            
            self.console.print(f"[bold blue]Variables for prompt '[/bold blue][bold green]{name}[/bold green][bold blue]':[/bold blue]\n")
            
            if not variables:
                self.console.print("[yellow]No variables required for this template[/yellow]")
                return
            
            for var in sorted(variables):
                self.console.print(f"  [green]•[/green] [bold]{var}[/bold]")
            
            self.console.print(f"\n[dim]Total: {len(variables)} variable(s)[/dim]")
            
            # Show usage example
            self.console.print(f"\n[bold cyan]Usage example:[/bold cyan]")
            var_args = ' '.join([f'--{var} "value"' for var in sorted(variables)])
            self.console.print(f"[dim]gnosari prompts use {name} \"Your message\" {var_args}[/dim]")
            
        except Exception as e:
            self.console.print(f"[red]Error reading prompt template: {e}[/red]")
    
    def create_prompt_from_template(self, template_name: str, output_path: str, variables: Dict[str, str]) -> bool:
        """Create a new prompt file from a template with variable substitution.
        
        Args:
            template_name: Name of the template to use (without .md extension)
            output_path: Path where the new prompt should be saved
            variables: Dictionary of variables to substitute
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if template exists
            if not self.prompt_exists(template_name):
                self.console.print(f"[red]Error: Template '{template_name}' not found[/red]")
                return False
            
            # Process the template
            processed_content = self.use_prompt(template_name, variables)
            
            # Create output directory if it doesn't exist
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the processed content to the output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            self.console.print(f"[green]✅ Created prompt file:[/green] {output_file}")
            
            # Show summary
            all_variables = self.get_prompt_variables(template_name)
            substituted_vars = set(variables.keys()) & all_variables
            remaining_vars = all_variables - substituted_vars
            
            self.console.print(f"[blue]Template used:[/blue] {template_name}")
            if substituted_vars:
                self.console.print(f"[green]Variables substituted:[/green] {len(substituted_vars)} ({', '.join(sorted(substituted_vars))})")
            if remaining_vars:
                self.console.print(f"[yellow]Variables remaining as placeholders:[/yellow] {len(remaining_vars)} ({', '.join(sorted(remaining_vars))})")
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error creating prompt file: {e}[/red]")
            return False