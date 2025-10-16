"""Specialized learning prompt builder with YAML-configured learning strategies."""

from typing import Dict, List, Any, Optional
from pathlib import Path
from .strategy_loader import LearningStrategyLoader
from ...schemas.learning import LearningStrategyConfig, CompetencyConfig, AgentLearningConfig


class SpecializedLearningPromptBuilder:
    """Builds learning prompts with YAML-configured specialization content.
    
    This builder extends the existing learning prompt system to support
    domain-specific learning strategies and competency-focused analysis
    based on YAML component configurations.
    """
    
    def __init__(self, strategy_loader: LearningStrategyLoader):
        """Initialize the specialized prompt builder.
        
        Args:
            strategy_loader: Loaded strategy and competency component loader
        """
        self.strategy_loader = strategy_loader
    
    def build_specialized_prompt(
        self,
        learning_agent_config: Dict[str, Any],
        target_agent_name: str,
        target_agent_memory: Dict[str, Any],
        session_data: List[Dict[str, Any]],
        agent_config: Dict[str, Any],
        learning_context: Dict[str, Any] = None
    ) -> List[str]:
        """Build learning prompt with YAML-configured specialization content.
        
        Args:
            learning_agent_config: Learning agent configuration
            target_agent_name: Name of agent being learned
            target_agent_memory: Current agent memory dictionary
            session_data: Historical session data for analysis
            agent_config: Target agent configuration (may contain learning_strategy, etc.)
            learning_context: Additional context for learning session
            
        Returns:
            List[str]: Complete specialized learning prompt lines
        """
        # Extract learning configuration from agent config
        learning_strategy_id = agent_config.get('learning_strategy')
        competency_focus_ids = agent_config.get('competency_focus', [])
        learning_priorities = agent_config.get('learning_priorities', [])
        
        # Load strategy and competency configurations
        strategy_config, competency_configs = self._load_learning_components(
            learning_strategy_id, competency_focus_ids
        )
        
        # Build base prompt structure
        base_prompt = self._build_base_learning_prompt(
            learning_agent_config, target_agent_name, target_agent_memory, 
            session_data, learning_context
        )
        
        # Build specialization sections
        specialized_sections = self._build_specialization_sections(
            strategy_config, competency_configs, learning_priorities, learning_context
        )
        
        # Integrate specialization content into base prompt
        return self._integrate_specialization_content(base_prompt, specialized_sections)
    
    def _load_learning_components(
        self, 
        learning_strategy_id: Optional[str], 
        competency_focus_ids: List[str]
    ) -> tuple[LearningStrategyConfig, List[CompetencyConfig]]:
        """Load learning strategy and competency configurations.
        
        Args:
            learning_strategy_id: Strategy identifier (optional)
            competency_focus_ids: List of competency identifiers
            
        Returns:
            tuple: (strategy_config, competency_configs)
        """
        # Load strategy configuration (with fallback to default)
        if learning_strategy_id:
            try:
                strategy_config = self.strategy_loader.load_strategy(learning_strategy_id)
            except ValueError:
                # Fall back to default strategy if specified strategy not found
                default_config = self.strategy_loader.get_default_strategy_config()
                strategy_config = LearningStrategyConfig(**default_config)
        else:
            # Use default strategy if none specified
            default_config = self.strategy_loader.get_default_strategy_config()
            strategy_config = LearningStrategyConfig(**default_config)
        
        # Load competency configurations
        competency_configs = []
        for comp_id in competency_focus_ids:
            try:
                competency_config = self.strategy_loader.load_competency(comp_id)
                competency_configs.append(competency_config)
            except ValueError:
                # Skip competencies that cannot be loaded
                continue
        
        return strategy_config, competency_configs
    
    def _build_base_learning_prompt(
        self,
        learning_agent_config: Dict[str, Any],
        target_agent_name: str,
        target_agent_memory: Dict[str, Any],
        session_data: List[Dict[str, Any]],
        learning_context: Dict[str, Any] = None
    ) -> List[str]:
        """Build base learning prompt structure (non-specialized sections).
        
        This maintains compatibility with the existing prompt structure while
        preparing for specialization content injection.
        
        Args:
            learning_agent_config: Learning agent configuration
            target_agent_name: Name of agent being learned
            target_agent_memory: Current agent memory dictionary
            session_data: Historical session data
            learning_context: Additional learning context
            
        Returns:
            List[str]: Base prompt lines
        """
        # Build minimal base prompt - let teacher agent instructions handle the rest
        import json
        formatted_memory = json.dumps(target_agent_memory, indent=2) if target_agent_memory else "{}"
        
        base_prompt = [
            f"## Current Memory for Agent: {target_agent_name}",
            "",
            "```json",
            formatted_memory,
            "```",
            "",
            # Specialization sections will be injected here
            "",
        ]
        
        return base_prompt
    
    def _build_specialization_sections(
        self,
        strategy_config: LearningStrategyConfig,
        competency_configs: List[CompetencyConfig],
        learning_priorities: List[Dict[str, Any]],
        learning_context: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Build specialization-specific prompt sections from YAML configs.
        
        Args:
            strategy_config: Learning strategy configuration
            competency_configs: List of competency configurations
            learning_priorities: Agent-specific learning priorities
            learning_context: Learning session context
            
        Returns:
            Dict[str, List[str]]: Specialized prompt sections
        """
        sections = {}
        
        # Build strategy-specific analysis criteria
        sections['analysis_criteria'] = self._build_analysis_criteria_section(strategy_config)
        
        # Build competency assessment sections
        if competency_configs:
            sections['competency_assessments'] = self._build_competency_assessments_section(competency_configs)
        
        # Build learning objectives section
        sections['learning_objectives'] = self._build_learning_objectives_section(strategy_config)
        
        # Build priority guidance section
        if learning_priorities:
            sections['priority_guidance'] = self._build_priority_guidance_section(learning_priorities)
        
        # Build instruction templates section
        if strategy_config.instruction_templates:
            sections['instruction_templates'] = self._build_instruction_templates_section(strategy_config)
        
        return sections
    
    def _build_analysis_criteria_section(self, strategy_config: LearningStrategyConfig) -> List[str]:
        """Build analysis criteria section from strategy configuration.
        
        Args:
            strategy_config: Learning strategy configuration
            
        Returns:
            List[str]: Analysis criteria prompt lines
        """
        criteria_section = [
            f"## Specialized Analysis Criteria - {strategy_config.name}",
            "",
            f"**Strategy Focus**: {strategy_config.description}",
            "",
            "Analyze the agent's performance using these domain-specific criteria:",
            ""
        ]
        
        # Add weighted analysis criteria from strategy config
        for criterion in strategy_config.analysis_criteria:
            # Use weight indicators for visual priority
            weight_indicator = self._get_weight_indicator(criterion.weight)
            criteria_section.append(
                f"- {weight_indicator} **{criterion.criterion.replace('_', ' ').title()}**: {criterion.description}"
            )
        
        # Add focus areas context
        if strategy_config.focus_areas:
            criteria_section.extend([
                "",
                f"**Focus Areas**: {', '.join(strategy_config.focus_areas)}",
                ""
            ])
        
        return criteria_section
    
    def _build_competency_assessments_section(self, competency_configs: List[CompetencyConfig]) -> List[str]:
        """Build competency assessments section from competency configurations.
        
        Args:
            competency_configs: List of competency configurations
            
        Returns:
            List[str]: Competency assessment prompt lines
        """
        assessment_section = [
            "## Competency-Focused Assessment:",
            "",
            "Evaluate the agent's competencies in these specific areas:",
            ""
        ]
        
        for competency in competency_configs:
            assessment_section.extend([
                f"### {competency.name}",
                f"*{competency.description}*",
                "",
                "Assessment criteria:"
            ])
            
            for criterion in competency.assessment_criteria:
                assessment_section.append(f"- {criterion}")
            
            # Add success metrics if available
            if competency.success_metrics:
                assessment_section.extend([
                    "",
                    "Success metrics:"
                ])
                for metric in competency.success_metrics:
                    assessment_section.append(
                        f"- **{metric.metric}**: {metric.description} (target: {metric.target:.0%})"
                    )
            
            assessment_section.append("")
        
        return assessment_section
    
    def _build_learning_objectives_section(self, strategy_config: LearningStrategyConfig) -> List[str]:
        """Build learning objectives section from strategy configuration.
        
        Args:
            strategy_config: Learning strategy configuration
            
        Returns:
            List[str]: Learning objectives prompt lines
        """
        objectives_section = [
            "## Learning Objectives:",
            "",
            "Focus improvements on achieving these strategic learning goals:",
            ""
        ]
        
        for objective in strategy_config.learning_objectives:
            objectives_section.append(f"- {objective}")
        
        objectives_section.append("")
        return objectives_section
    
    def _build_priority_guidance_section(self, learning_priorities: List[Dict[str, Any]]) -> List[str]:
        """Build priority guidance section from agent-specific priorities.
        
        Args:
            learning_priorities: Agent-specific learning priorities
            
        Returns:
            List[str]: Priority guidance prompt lines
        """
        priority_section = [
            "## Learning Priorities:",
            "",
            "Pay special attention to these agent-specific priorities:",
            ""
        ]
        
        # Sort priorities by level
        level_order = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
        sorted_priorities = sorted(
            learning_priorities, 
            key=lambda p: level_order.get(p.get('level', 'medium'), 3)
        )
        
        for priority in sorted_priorities:
            level = priority.get('level', 'medium').upper()
            content = priority.get('content', '')
            context = priority.get('context', '')
            
            priority_indicator = self._get_priority_indicator(priority.get('level', 'medium'))
            priority_section.extend([
                f"- {priority_indicator} **{level}**: {content}",
                f"  *Context*: {context}",
                ""
            ])
        
        return priority_section
    
    def _build_instruction_templates_section(self, strategy_config: LearningStrategyConfig) -> List[str]:
        """Build instruction templates section from strategy configuration.
        
        Args:
            strategy_config: Learning strategy configuration
            
        Returns:
            List[str]: Instruction templates prompt lines
        """
        templates_section = [
            "## Strategy-Specific Guidance:",
            ""
        ]
        
        if 'analysis_focus' in strategy_config.instruction_templates:
            templates_section.extend([
                "**Analysis Focus:**",
                strategy_config.instruction_templates['analysis_focus'],
                ""
            ])
        
        if 'improvement_guidance' in strategy_config.instruction_templates:
            templates_section.extend([
                "**Improvement Guidance:**",
                strategy_config.instruction_templates['improvement_guidance'],
                ""
            ])
        
        return templates_section
    
    def _integrate_specialization_content(
        self, 
        base_prompt: List[str], 
        specialized_sections: Dict[str, List[str]]
    ) -> List[str]:
        """Integrate specialization content into base prompt structure.
        
        Args:
            base_prompt: Base prompt lines
            specialized_sections: Specialized prompt sections
            
        Returns:
            List[str]: Complete integrated prompt
        """
        # Find insertion point after current memory
        insert_index = -1
        for i, line in enumerate(base_prompt):
            if line == "```" and i > 0 and "Current Agent Memory:" in base_prompt[i-2]:
                insert_index = i + 2  # After the closing ``` and empty line
                break
        
        if insert_index == -1:
            # Fallback: insert after memory section
            insert_index = len(base_prompt) // 2
        
        # Build integrated prompt
        integrated_prompt = base_prompt[:insert_index]
        
        # Add specialized sections in order
        section_order = [
            'analysis_criteria',
            'competency_assessments', 
            'learning_objectives',
            'priority_guidance',
            'instruction_templates'
        ]
        
        for section_key in section_order:
            if section_key in specialized_sections:
                integrated_prompt.extend(specialized_sections[section_key])
        
        # Add remaining base prompt content
        integrated_prompt.extend(base_prompt[insert_index:])
        
        return integrated_prompt
    
    def _get_weight_indicator(self, weight: float) -> str:
        """Get visual indicator for criterion weight.
        
        Args:
            weight: Criterion weight value
            
        Returns:
            str: Visual weight indicator
        """
        if weight >= 1.4:
            return "🔴"  # Critical importance
        elif weight >= 1.2:
            return "🟠"  # High importance
        elif weight >= 1.0:
            return "🟡"  # Normal importance
        else:
            return "⚪"  # Lower importance
    
    def _get_priority_indicator(self, level: str) -> str:
        """Get visual indicator for priority level.
        
        Args:
            level: Priority level string
            
        Returns:
            str: Visual priority indicator
        """
        indicators = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '📋',
            'low': '📝'
        }
        return indicators.get(level.lower(), '📋')