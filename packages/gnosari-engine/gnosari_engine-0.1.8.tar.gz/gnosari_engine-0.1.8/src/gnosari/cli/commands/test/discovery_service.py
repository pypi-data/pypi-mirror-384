"""
Test Discovery Service

SOLID-based service for discovering and cataloging available tests across the project.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
import json
import fnmatch
from dataclasses import dataclass
from enum import Enum


class TestType(Enum):
    """Types of tests that can be discovered."""
    AGENTIC = "agentic"
    INTEGRATION = "integration" 
    UNIT = "unit"
    PERFORMANCE = "performance"


@dataclass
class TestInfo:
    """Information about a discovered test."""
    name: str
    path: Path
    type: TestType
    command: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    estimated_duration: Optional[float] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class TestScanner:
    """Scans directories for test files (Single Responsibility)."""
    
    def __init__(self, test_root: Path):
        self.test_root = test_root
        self.patterns = {
            TestType.AGENTIC: ["**/agentic/**/test_*.py", "**/agentic/**/*_test.py"],
            TestType.INTEGRATION: ["**/integration/**/test_*.py", "**/integration/**/*_test.py"],
            TestType.UNIT: ["**/unit/**/test_*.py", "**/unit/**/*_test.py", "**/test_*.py"],
            TestType.PERFORMANCE: ["**/performance/**/test_*.py", "**/perf_*.py"]
        }
    
    def scan_tests(self, test_types: Set[TestType] = None) -> List[TestInfo]:
        """Scan for test files of specified types."""
        if test_types is None:
            test_types = set(TestType)
        
        discovered_tests = []
        
        for test_type in test_types:
            patterns = self.patterns.get(test_type, [])
            for pattern in patterns:
                for test_file in self.test_root.glob(pattern):
                    if test_file.is_file() and test_file.suffix == '.py':
                        test_info = self._extract_test_info(test_file, test_type)
                        if test_info:
                            discovered_tests.append(test_info)
        
        return discovered_tests
    
    def _extract_test_info(self, test_file: Path, test_type: TestType) -> Optional[TestInfo]:
        """Extract test information from file."""
        try:
            # Basic info from file path
            relative_path = test_file.relative_to(self.test_root)
            name = test_file.stem
            
            # Try to extract command from path structure
            command = self._extract_command_from_path(relative_path)
            
            # Try to extract metadata from file content
            metadata = self._extract_file_metadata(test_file)
            
            return TestInfo(
                name=name,
                path=test_file,
                type=test_type,
                command=command,
                description=metadata.get('description'),
                tags=metadata.get('tags', []),
                estimated_duration=metadata.get('duration')
            )
            
        except Exception:
            return None
    
    def _extract_command_from_path(self, relative_path: Path) -> Optional[str]:
        """Extract command name from test file path."""
        parts = relative_path.parts
        
        # Look for command indicators in path
        for i, part in enumerate(parts):
            if part in ['scenarios', 'commands']:
                if i + 1 < len(parts):
                    return parts[i + 1]
        
        # Look for common command patterns
        for part in parts:
            if part in ['structure', 'show-prompts', 'run', 'team']:
                return part
        
        return None
    
    def _extract_file_metadata(self, test_file: Path) -> Dict[str, Any]:
        """Extract metadata from test file content."""
        try:
            content = test_file.read_text(encoding='utf-8')
            metadata = {}
            
            # Look for docstring with metadata
            lines = content.split('\\n')
            in_docstring = False
            docstring_lines = []
            
            for line in lines[:20]:  # Only check first 20 lines
                stripped = line.strip()
                
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if in_docstring:
                        break
                    in_docstring = True
                    docstring_lines.append(stripped[3:])
                elif in_docstring:
                    if stripped.endswith('"""') or stripped.endswith("'''"):
                        docstring_lines.append(stripped[:-3])
                        break
                    docstring_lines.append(stripped)
            
            docstring = '\\n'.join(docstring_lines).strip()
            if docstring:
                metadata['description'] = docstring.split('\\n')[0]  # First line as description
            
            # Look for special comments
            for line in lines[:50]:  # Check more lines for metadata
                if '# Tags:' in line:
                    tags = line.split('# Tags:')[1].strip()
                    metadata['tags'] = [tag.strip() for tag in tags.split(',')]
                elif '# Duration:' in line:
                    try:
                        duration = float(line.split('# Duration:')[1].strip().rstrip('s'))
                        metadata['duration'] = duration
                    except (ValueError, IndexError):
                        pass
            
            return metadata
            
        except Exception:
            return {}


class TestFilter:
    """Filters discovered tests based on criteria (Single Responsibility)."""
    
    def filter_tests(
        self,
        tests: List[TestInfo],
        command_filter: Optional[str] = None,
        test_type_filter: Optional[TestType] = None,
        tag_filter: Optional[List[str]] = None,
        name_pattern: Optional[str] = None
    ) -> List[TestInfo]:
        """Filter tests based on various criteria."""
        filtered = tests
        
        # Filter by command
        if command_filter:
            filtered = [t for t in filtered if t.command == command_filter]
        
        # Filter by test type
        if test_type_filter:
            filtered = [t for t in filtered if t.type == test_type_filter]
        
        # Filter by tags
        if tag_filter:
            filtered = [
                t for t in filtered 
                if any(tag in t.tags for tag in tag_filter)
            ]
        
        # Filter by name pattern
        if name_pattern:
            filtered = [
                t for t in filtered
                if fnmatch.fnmatch(t.name.lower(), name_pattern.lower())
            ]
        
        return filtered


class TestDisplayFormatter:
    """Formats test discovery results for display (Single Responsibility)."""
    
    def format_as_table(self, tests: List[TestInfo], console: Console) -> None:
        """Display tests as a table."""
        if not tests:
            console.print("[yellow]No tests found matching criteria[/yellow]")
            return
        
        table = Table(title="🔍 Discovered Tests")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Command", style="green")
        table.add_column("Duration", justify="right")
        table.add_column("Tags", style="dim")
        table.add_column("Path", style="dim")
        
        for test in sorted(tests, key=lambda t: (t.type.value, t.command or "", t.name)):
            duration = f"{test.estimated_duration:.1f}s" if test.estimated_duration else "N/A"
            tags = ", ".join(test.tags) if test.tags else "None"
            relative_path = str(test.path).split('tests/')[-1] if 'tests/' in str(test.path) else str(test.path)
            
            table.add_row(
                test.name,
                test.type.value.title(),
                test.command or "N/A",
                duration,
                tags,
                relative_path
            )
        
        console.print(table)
    
    def format_as_tree(self, tests: List[TestInfo], console: Console) -> None:
        """Display tests as a hierarchical tree."""
        if not tests:
            console.print("[yellow]No tests found matching criteria[/yellow]")
            return
        
        # Group tests by type and command
        grouped = {}
        for test in tests:
            test_type = test.type.value
            command = test.command or "general"
            
            if test_type not in grouped:
                grouped[test_type] = {}
            if command not in grouped[test_type]:
                grouped[test_type][command] = []
            
            grouped[test_type][command].append(test)
        
        # Create tree
        tree = Tree("🧪 Test Inventory")
        
        for test_type in sorted(grouped.keys()):
            type_node = tree.add(f"📁 {test_type.title()} Tests")
            
            for command in sorted(grouped[test_type].keys()):
                command_tests = grouped[test_type][command]
                command_node = type_node.add(f"⚙️  {command} ({len(command_tests)} tests)")
                
                for test in sorted(command_tests, key=lambda t: t.name):
                    duration = f"({test.estimated_duration:.1f}s)" if test.estimated_duration else ""
                    tags = f"[{', '.join(test.tags)}]" if test.tags else ""
                    test_node = command_node.add(f"🧪 {test.name} {duration} {tags}")
        
        console.print(tree)
    
    def format_as_json(self, tests: List[TestInfo], console: Console) -> None:
        """Display tests as JSON."""
        test_data = []
        for test in tests:
            test_data.append({
                "name": test.name,
                "type": test.type.value,
                "command": test.command,
                "description": test.description,
                "tags": test.tags,
                "estimated_duration": test.estimated_duration,
                "path": str(test.path)
            })
        
        json_output = json.dumps(test_data, indent=2)
        console.print(f"```json\\n{json_output}\\n```")


class TestDiscoveryService:
    """Main service for test discovery (Orchestration)."""
    
    def __init__(
        self,
        scanner: TestScanner,
        filter: TestFilter,
        formatter: TestDisplayFormatter
    ):
        self.scanner = scanner
        self.filter = filter
        self.formatter = formatter
    
    async def discover_tests(
        self,
        console: Console,
        test_type: str = 'all',
        command_filter: Optional[str] = None,
        output_format: str = 'table',
        name_pattern: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Discover and display available tests."""
        try:
            console.print("🔍 Scanning for tests...")
            
            # Determine test types to scan
            if test_type == 'all':
                scan_types = set(TestType)
            else:
                try:
                    scan_types = {TestType(test_type)}
                except ValueError:
                    return {
                        'success': False,
                        'message': f"Invalid test type '{test_type}'. Valid types: {[t.value for t in TestType]}"
                    }
            
            # Scan for tests
            tests = self.scanner.scan_tests(scan_types)
            
            # Apply filters
            test_type_filter = None if test_type == 'all' else TestType(test_type)
            filtered_tests = self.filter.filter_tests(
                tests=tests,
                command_filter=command_filter,
                test_type_filter=test_type_filter,
                tag_filter=tags,
                name_pattern=name_pattern
            )
            
            # Display results
            if output_format == 'table':
                self.formatter.format_as_table(filtered_tests, console)
            elif output_format == 'tree':
                self.formatter.format_as_tree(filtered_tests, console)
            elif output_format == 'json':
                self.formatter.format_as_json(filtered_tests, console)
            else:
                return {
                    'success': False,
                    'message': f"Invalid format '{output_format}'. Valid formats: table, tree, json"
                }
            
            # Summary
            total_tests = len(tests)
            shown_tests = len(filtered_tests)
            summary = f"Found {total_tests} total tests, showing {shown_tests}"
            if command_filter:
                summary += f" for command '{command_filter}'"
            
            console.print(f"\\n📊 {summary}")
            
            return {
                'success': True,
                'summary': summary,
                'total_tests': total_tests,
                'filtered_tests': shown_tests,
                'tests': filtered_tests
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Test discovery failed: {e}'
            }


def create_test_discovery_service() -> TestDiscoveryService:
    """Factory function for creating test discovery service."""
    # Create test root path
    test_root = Path(__file__).parent.parent.parent.parent.parent.parent / "tests"
    
    # Create dependencies
    scanner = TestScanner(test_root)
    filter_engine = TestFilter()
    formatter = TestDisplayFormatter()
    
    return TestDiscoveryService(scanner, filter_engine, formatter)