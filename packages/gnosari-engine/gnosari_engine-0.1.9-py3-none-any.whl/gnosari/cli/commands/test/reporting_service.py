"""
Test Reporting Service

SOLID-based service for generating comprehensive test reports and analytics.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics


class ReportFormat(Enum):
    """Available report formats."""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    MARKDOWN = "md"


@dataclass
class TestExecutionMetrics:
    """Metrics from test execution."""
    total_tests: int
    successful_tests: int
    failed_tests: int
    total_execution_time: float
    average_execution_time: float
    confidence_scores: List[float]
    average_confidence: float
    test_types: Dict[str, int]
    commands_tested: List[str]
    timestamp: datetime


@dataclass
class ReportData:
    """Comprehensive report data."""
    metrics: TestExecutionMetrics
    test_results: List[Dict[str, Any]]
    historical_data: Optional[List[TestExecutionMetrics]] = None
    environment_info: Optional[Dict[str, Any]] = None


class MetricsCollector:
    """Collects and calculates test execution metrics (Single Responsibility)."""
    
    def collect_metrics(self, test_results: List[Any]) -> TestExecutionMetrics:
        """Collect comprehensive metrics from test results."""
        if not test_results:
            return TestExecutionMetrics(
                total_tests=0,
                successful_tests=0,
                failed_tests=0,
                total_execution_time=0.0,
                average_execution_time=0.0,
                confidence_scores=[],
                average_confidence=0.0,
                test_types={},
                commands_tested=[],
                timestamp=datetime.now()
            )
        
        # Basic counts
        total_tests = len(test_results)
        successful_tests = sum(1 for r in test_results if getattr(r, 'success', False))
        failed_tests = total_tests - successful_tests
        
        # Time metrics
        execution_times = [getattr(r, 'execution_time', 0.0) for r in test_results]
        total_execution_time = sum(execution_times)
        average_execution_time = statistics.mean(execution_times) if execution_times else 0.0
        
        # Confidence scores
        confidence_scores = []
        for result in test_results:
            validation_result = getattr(result, 'validation_result', None)
            if validation_result and hasattr(validation_result, 'confidence'):
                confidence_scores.append(validation_result.confidence)
        
        average_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
        
        # Test type distribution
        test_types = {}
        commands_tested = set()
        
        for result in test_results:
            # Extract test type (from result or infer from command)
            test_type = getattr(result, 'test_type', 'agentic')
            test_types[test_type] = test_types.get(test_type, 0) + 1
            
            # Extract command
            command = getattr(result, 'command_name', None)
            if command:
                commands_tested.add(command)
        
        return TestExecutionMetrics(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            total_execution_time=total_execution_time,
            average_execution_time=average_execution_time,
            confidence_scores=confidence_scores,
            average_confidence=average_confidence,
            test_types=test_types,
            commands_tested=list(commands_tested),
            timestamp=datetime.now()
        )


class HistoricalDataManager:
    """Manages historical test data (Single Responsibility)."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def save_metrics(self, metrics: TestExecutionMetrics) -> None:
        """Save metrics to historical data."""
        filename = f"metrics_{metrics.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename
        
        # Convert to serializable format
        data = asdict(metrics)
        data['timestamp'] = metrics.timestamp.isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_historical_metrics(self, days_back: int = 30) -> List[TestExecutionMetrics]:
        """Load historical metrics from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        historical_metrics = []
        
        for file_path in self.data_dir.glob("metrics_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                timestamp = datetime.fromisoformat(data['timestamp'])
                if timestamp >= cutoff_date:
                    data['timestamp'] = timestamp
                    metrics = TestExecutionMetrics(**data)
                    historical_metrics.append(metrics)
                    
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
        
        return sorted(historical_metrics, key=lambda m: m.timestamp)


class ReportGenerator:
    """Generates reports in different formats (Single Responsibility)."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_console_report(self, report_data: ReportData, console: Console) -> None:
        """Generate a rich console report."""
        metrics = report_data.metrics
        
        # Summary panel
        success_rate = (metrics.successful_tests / metrics.total_tests * 100) if metrics.total_tests > 0 else 0
        summary_color = "green" if success_rate >= 80 else "yellow" if success_rate >= 60 else "red"
        
        summary_content = f"[bold {summary_color}]Test Execution Summary[/bold {summary_color}]\\n\\n"
        summary_content += f"📊 Total Tests: {metrics.total_tests}\\n"
        summary_content += f"✅ Successful: {metrics.successful_tests} ({success_rate:.1f}%)\\n"
        summary_content += f"❌ Failed: {metrics.failed_tests}\\n"
        summary_content += f"⏱️  Total Time: {metrics.total_execution_time:.2f}s\\n"
        summary_content += f"📈 Avg Time: {metrics.average_execution_time:.2f}s\\n"
        summary_content += f"🤖 Avg Confidence: {metrics.average_confidence:.1f}%\\n"
        
        summary_panel = Panel(
            summary_content,
            title="📋 Test Report Summary",
            border_style=summary_color
        )
        console.print(summary_panel)
        
        # Test type distribution
        if metrics.test_types:
            type_table = Table(title="📁 Test Type Distribution")
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", justify="right")
            type_table.add_column("Percentage", justify="right")
            
            for test_type, count in metrics.test_types.items():
                percentage = (count / metrics.total_tests * 100) if metrics.total_tests > 0 else 0
                type_table.add_row(
                    test_type.title(),
                    str(count),
                    f"{percentage:.1f}%"
                )
            
            console.print(type_table)
        
        # Commands tested
        if metrics.commands_tested:
            commands_panel = Panel(
                ", ".join(sorted(metrics.commands_tested)),
                title="⚙️  Commands Tested",
                border_style="blue"
            )
            console.print(commands_panel)
        
        # Historical comparison if available
        if report_data.historical_data:
            self._generate_historical_comparison(report_data.historical_data, metrics, console)
    
    def generate_json_report(self, report_data: ReportData) -> Path:
        """Generate JSON format report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Convert to serializable format
        report_dict = {
            "metrics": asdict(report_data.metrics),
            "test_results": report_data.test_results,
            "generated_at": datetime.now().isoformat(),
            "environment_info": report_data.environment_info
        }
        
        # Handle datetime serialization
        report_dict["metrics"]["timestamp"] = report_data.metrics.timestamp.isoformat()
        
        if report_data.historical_data:
            report_dict["historical_data"] = [
                {**asdict(h), "timestamp": h.timestamp.isoformat()}
                for h in report_data.historical_data
            ]
        
        with open(filepath, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        return filepath
    
    def generate_markdown_report(self, report_data: ReportData) -> Path:
        """Generate Markdown format report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_{timestamp}.md"
        filepath = self.output_dir / filename
        
        metrics = report_data.metrics
        success_rate = (metrics.successful_tests / metrics.total_tests * 100) if metrics.total_tests > 0 else 0
        
        content = f"""# Test Execution Report
        
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {metrics.total_tests} |
| Successful | {metrics.successful_tests} ({success_rate:.1f}%) |
| Failed | {metrics.failed_tests} |
| Total Time | {metrics.total_execution_time:.2f}s |
| Average Time | {metrics.average_execution_time:.2f}s |
| Average Confidence | {metrics.average_confidence:.1f}% |

## Test Type Distribution

| Type | Count | Percentage |
|------|-------|------------|
"""
        
        for test_type, count in metrics.test_types.items():
            percentage = (count / metrics.total_tests * 100) if metrics.total_tests > 0 else 0
            content += f"| {test_type.title()} | {count} | {percentage:.1f}% |\\n"
        
        content += f"""
## Commands Tested

{', '.join(sorted(metrics.commands_tested)) if metrics.commands_tested else 'None'}

## Environment Information

"""
        if report_data.environment_info:
            for key, value in report_data.environment_info.items():
                content += f"- **{key}**: {value}\\n"
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filepath
    
    def _generate_historical_comparison(
        self, 
        historical_data: List[TestExecutionMetrics], 
        current_metrics: TestExecutionMetrics,
        console: Console
    ) -> None:
        """Generate historical comparison section."""
        if len(historical_data) < 2:
            return
        
        # Calculate trends
        recent_metrics = historical_data[-5:]  # Last 5 runs
        avg_success_rate = statistics.mean([
            (m.successful_tests / m.total_tests * 100) if m.total_tests > 0 else 0
            for m in recent_metrics
        ])
        avg_confidence = statistics.mean([m.average_confidence for m in recent_metrics])
        
        current_success_rate = (current_metrics.successful_tests / current_metrics.total_tests * 100) if current_metrics.total_tests > 0 else 0
        
        # Trend indicators
        success_trend = "📈" if current_success_rate > avg_success_rate else "📉" if current_success_rate < avg_success_rate else "➡️"
        confidence_trend = "📈" if current_metrics.average_confidence > avg_confidence else "📉" if current_metrics.average_confidence < avg_confidence else "➡️"
        
        trend_content = f"Success Rate Trend: {success_trend} {current_success_rate:.1f}% (avg: {avg_success_rate:.1f}%)\\n"
        trend_content += f"Confidence Trend: {confidence_trend} {current_metrics.average_confidence:.1f}% (avg: {avg_confidence:.1f}%)"
        
        trend_panel = Panel(
            trend_content,
            title="📊 Historical Trends",
            border_style="blue"
        )
        console.print(trend_panel)


class TestReportingService:
    """Main service for test reporting (Orchestration)."""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        historical_manager: HistoricalDataManager,
        report_generator: ReportGenerator
    ):
        self.metrics_collector = metrics_collector
        self.historical_manager = historical_manager
        self.report_generator = report_generator
    
    async def generate_report(
        self,
        console: Console,
        report_directory: Path,
        output_format: str = 'html',
        include_history: bool = False,
        test_results: Optional[List[Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        try:
            console.print("📊 Generating test report...")
            
            # Use provided results or load from latest execution
            if not test_results:
                test_results = []  # In real implementation, load from test execution data
            
            # Collect metrics
            current_metrics = self.metrics_collector.collect_metrics(test_results)
            
            # Save current metrics
            self.historical_manager.save_metrics(current_metrics)
            
            # Load historical data if requested
            historical_data = None
            if include_history:
                with console.status("Loading historical data..."):
                    historical_data = self.historical_manager.load_historical_metrics()
            
            # Prepare report data
            environment_info = {
                "python_version": "3.9+",
                "gnosari_version": "1.0.0",
                "test_environment": kwargs.get('environment', 'development'),
                "generated_by": "Gnosari Test Framework"
            }
            
            report_data = ReportData(
                metrics=current_metrics,
                test_results=[asdict(r) if hasattr(r, '__dict__') else r for r in test_results],
                historical_data=historical_data,
                environment_info=environment_info
            )
            
            # Generate console report first
            self.report_generator.generate_console_report(report_data, console)
            
            # Generate file-based report
            report_path = None
            if output_format in ['json', 'md']:
                if output_format == 'json':
                    report_path = self.report_generator.generate_json_report(report_data)
                elif output_format == 'md':
                    report_path = self.report_generator.generate_markdown_report(report_data)
                
                console.print(f"📁 Report saved: {report_path}")
            elif output_format in ['html', 'pdf']:
                console.print(f"[yellow]Note: {output_format.upper()} format not yet implemented. Generated console report instead.[/yellow]")
            
            return {
                'success': True,
                'report_path': str(report_path) if report_path else None,
                'summary': f"Generated {output_format.upper()} report with {current_metrics.total_tests} tests",
                'metrics': current_metrics
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Report generation failed: {e}'
            }


def create_reporting_service() -> TestReportingService:
    """Factory function for creating reporting service."""
    # Create output directories
    base_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "tests" / "agentic"
    reports_dir = base_dir / "reports"
    data_dir = base_dir / "data"
    
    reports_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dependencies
    metrics_collector = MetricsCollector()
    historical_manager = HistoricalDataManager(data_dir)
    report_generator = ReportGenerator(reports_dir)
    
    return TestReportingService(metrics_collector, historical_manager, report_generator)