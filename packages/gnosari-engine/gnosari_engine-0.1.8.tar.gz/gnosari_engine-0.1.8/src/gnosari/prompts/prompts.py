"""Core prompt building functions and constants for the Gnosari framework."""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from .tool_prompts import get_tools_definition


def build_agent_system_prompt(
    name: str, 
    instructions: str, 
    agent_tools: List[str] = None, 
    tool_manager = None, 
    agent_config: Dict[str, Any] =  None,
    knowledge_descriptions: Dict[str, str] = None, 
    team_config: Dict[str, Any] = None, 
    real_tool_info: List[Dict] = None
) -> Dict[str, List[str]]:
    """Build system prompt components for any agent (orchestrator or specialized).
    
    Args:
        name: Agent name
        instructions: Agent instructions  
        agent_tools: List of tool names for this agent
        tool_manager: Tool manager instance for getting tool descriptions
        agent_config: Agent configuration dictionary
        knowledge_descriptions: Dictionary mapping knowledge base names to descriptions
        team_config: Team configuration dictionary (for orchestrators)
        real_tool_info: Real tool information for prompt building
        
    Returns:
        Dictionary with 'background', 'steps', and 'output_instructions' lists
    """
    # Load tool definitions if tool_manager is provided
    if tool_manager and team_config and 'tools' in team_config:
        tool_manager.load_tools_from_config(team_config)
    
    background = [
        f"# {name}",
        "",
        instructions,
        "",
    ]
    
    # NEW: Add trait information if configured - INSERTED EARLY for personality context
    if agent_config and 'traits' in agent_config and agent_config['traits']:
        try:
            trait_section = _build_trait_system_prompt_section(agent_config['traits'])
            if trait_section:
                background.extend(trait_section)
                background.append("")
                
                # Log trait application
                trait_names = [trait.get('name', 'unknown') for trait in agent_config['traits']]
                logging.getLogger(__name__).info(f"Applied traits to {name}: {trait_names}")
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to process traits for agent {name}: {e}")
            # Continue without traits rather than failing completely
    
    # Add collaboration mechanisms if configured
    has_delegation = agent_config and 'delegation' in agent_config and agent_config['delegation']
    has_handoffs = agent_config and 'can_transfer_to' in agent_config and agent_config['can_transfer_to']
    
    if has_delegation or has_handoffs:
        background.append("## Team Collaboration")
        mechanisms = []
        if has_delegation:
            mechanisms.append("**delegate_agent tool** for task delegation")
        if has_handoffs:
            mechanisms.append("**handoffs** to transfer conversation control")
        background.append(f"Use {' and '.join(mechanisms)}.")
        background.append("")
        
        # Add specific delegation instructions
        if has_delegation:
            delegation_config = agent_config['delegation']
            background.append("### Delegation Instructions")
            for del_config in delegation_config:
                if isinstance(del_config, dict) and del_config.get('agent') and del_config.get('instructions'):
                    background.append(f"- **{del_config['agent']}**: {del_config['instructions']}")
            background.append("")
        
        # Add specific handoff instructions  
        if has_handoffs:
            can_transfer_to = agent_config['can_transfer_to']
            background.append("### Handoff Instructions")
            for transfer_config in can_transfer_to:
                if isinstance(transfer_config, dict) and transfer_config.get('agent') and transfer_config.get('instructions'):
                    background.append(f"- **{transfer_config['agent']}**: {transfer_config['instructions']}")
            background.append("")

    # NEW: Add learning integration if configured - INSERTED AFTER TRAITS for learning context
    if agent_config and 'learning' in agent_config and agent_config['learning']:
        try:
            learning_section = _build_learning_system_prompt_section(agent_config['learning'])
            if learning_section:
                background.extend(learning_section)
                background.append("")
                
                # Log learning application
                learning_count = len(agent_config['learning'])
                logging.getLogger(__name__).info(f"Applied {learning_count} learnings to {name}")
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to process learnings for agent {name}: {e}")
            # Continue without learnings rather than failing completely

    # NEW: Add event publishing integration if configured
    if agent_config and 'trigger' in agent_config and agent_config['trigger']:
        try:
            trigger_section = _build_event_publish_system_prompt_section(agent_config['trigger'])
            if trigger_section:
                background.extend(trigger_section)
                background.append("")
                
                trigger_count = len(agent_config['trigger'])
                logging.getLogger(__name__).info(f"Added {trigger_count} event triggers to {name}")
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to process event triggers for agent {name}: {e}")

    # Add agent memory if configured
    if agent_config and 'memory' in agent_config and agent_config['memory']:
        memory = agent_config['memory']
        background.append("## Your Memory")
        background.append("")
        background.append("You have the following accumulated knowledge and context from previous interactions:")
        background.append("")
        
        # Handle memory as string or dict
        if isinstance(memory, str):
            background.append(memory)
        elif isinstance(memory, dict):
            # Process memory sections
            for section_name, section_content in memory.items():
                section_display = section_name.replace('_', ' ').title()
                background.append(f"### {section_display}")
                
                if isinstance(section_content, dict):
                    for key, value in section_content.items():
                        key_display = key.replace('_', ' ').title()
                        background.append(f"- **{key_display}**: {value}")
                elif isinstance(section_content, str):
                    background.append(f"{section_content}")
                background.append("")
        
        background.append("**Important**: Use this memory to provide personalized and contextual responses. Update your understanding based on new information.")
        background.append("")

    # Add knowledge base access if configured
    if agent_config and 'knowledge' in agent_config and agent_config['knowledge']:
        knowledge_names = agent_config['knowledge']
        background.append("## Available Knowledge Bases")
        for kb_name in knowledge_names:
            description = knowledge_descriptions.get(kb_name, "") if knowledge_descriptions else ""
            kb_info = f"- **{kb_name}**"
            if description:
                kb_info += f": {description}"
            background.append(kb_info)
        background.append("")
        background.append("**Important**: Use the `knowledge_query` tool with exact knowledge base names. Always search knowledge before responding.")
        background.append("")
    
    # Add tool information using real tool info if available
    tool_sections = get_tools_definition(agent_tools, tool_manager, real_tool_info)
    if tool_sections:
        background.extend(tool_sections)
    
    return {
        "background": background,
        "steps": [],
        "output_instructions": ["Use available tools as needed to fulfill requests."]
    }


def _build_trait_system_prompt_section(traits: List[Dict[str, Any]]) -> List[str]:
    """Build the personality traits section for system prompts.
    
    Args:
        traits: List of trait configuration dictionaries
        
    Returns:
        List of formatted prompt lines for the traits section
    """
    if not traits:
        return []
    
    # Validate traits structure
    valid_traits = []
    for trait in traits:
        if isinstance(trait, dict) and trait.get('name') and trait.get('instructions'):
            valid_traits.append(trait)
        else:
            logging.getLogger(__name__).warning(f"Skipping invalid trait: {trait}")
    
    if not valid_traits:
        return []
    
    prompt_lines = [
        "## 🎭 Your Personality Traits",
        "",
        "You embody the following personality traits that fundamentally shape how you interact, respond, and approach tasks:",
        ""
    ]
    
    # Add each trait with clear formatting
    for i, trait in enumerate(valid_traits, 1):
        trait_name = trait['name'].replace('_', ' ').replace('-', ' ').title()
        description = trait.get('description', '')
        instructions = trait['instructions']
        weight = trait.get('weight', 1.0)
        
        # Trait header with emphasis
        prompt_lines.append(f"### {i}. **{trait_name} Trait**")
        
        # Add description if available
        if description:
            prompt_lines.append(f"*{description}*")
            prompt_lines.append("")
        
        # Core trait instructions with clear formatting
        prompt_lines.append("**How to embody this trait:**")
        
        # Split instructions into sentences for better readability
        instruction_sentences = instructions.strip().split('. ')
        if len(instruction_sentences) > 1:
            for sentence in instruction_sentences:
                if sentence.strip():
                    # Ensure proper punctuation
                    clean_sentence = sentence.strip()
                    if not clean_sentence.endswith('.') and not clean_sentence.endswith('!') and not clean_sentence.endswith('?'):
                        clean_sentence += '.'
                    prompt_lines.append(f"- {clean_sentence}")
        else:
            prompt_lines.append(f"- {instructions}")
        
        # Add weight indication if different from default
        if weight != 1.0:
            if weight > 1.0:
                prompt_lines.append(f"- **Emphasis Level:** Strong (weight: {weight}) - Make this trait prominent in your responses")
            else:
                prompt_lines.append(f"- **Emphasis Level:** Subtle (weight: {weight}) - Apply this trait lightly")
        
        prompt_lines.append("")
    
    # Add integration instructions
    prompt_lines.extend([
        "## 🎯 Trait Integration Guidelines",
        "",
        "**Core Principles:**",
        "1. **Natural Expression:** Let these traits flow naturally through your responses rather than forcing them",
        "2. **Task Balance:** Always prioritize being helpful and accurate while expressing your personality",
        "3. **Context Awareness:** Adapt trait intensity based on the situation (more professional for business, more relaxed for casual)",
        "4. **Consistency:** Maintain these personality characteristics throughout the entire conversation",
        "5. **Authenticity:** Make these traits feel genuine and integrated, not like separate behaviors",
        "",
    ])
    
    return prompt_lines


def _build_learning_system_prompt_section(learnings: List[Dict[str, Any]], max_learnings: int = 10) -> List[str]:
    """Build the learnings section for system prompts with priority ordering.
    
    Args:
        learnings: List of learning configuration dictionaries
        max_learnings: Maximum number of learnings to include
        
    Returns:
        List of formatted prompt lines for the learnings section
    """
    if not learnings:
        return []
    
    # Validate and filter learnings
    valid_learnings = []
    for learning in learnings:
        if _validate_learning_for_prompt(learning):
            valid_learnings.append(learning)
        else:
            logging.getLogger(__name__).warning(f"Skipping invalid learning: {learning}")
    
    if not valid_learnings:
        return []
    
    # Sort by priority weight (descending), then by usage_count, then by updated_at
    sorted_learnings = sorted(
        valid_learnings,
        key=lambda x: (
            _get_learning_priority_weight(x.get('priority', 'medium')),
            x.get('usage_count', 0),
            x.get('updated_at', '')
        ),
        reverse=True
    )[:max_learnings]
    
    prompt_lines = [
        "## 📚 Your Accumulated Learnings",
        "",
        "Apply these insights from past experiences. Priorities guide application weight:",
        ""
    ]
    
    # Group learnings by type for organization
    learnings_by_type = {}
    for learning in sorted_learnings:
        learning_type = learning.get('type', 'general')
        if learning_type not in learnings_by_type:
            learnings_by_type[learning_type] = []
        learnings_by_type[learning_type].append(learning)
    
    # Add each type section with priority indicators
    for learning_type, type_learnings in learnings_by_type.items():
        type_display = learning_type.replace('_', ' ').title()
        priority_indicator = _get_learning_priority_indicator(type_learnings[0].get('priority', 'medium'))
        
        prompt_lines.append(f"### {priority_indicator} {type_display}")
        
        for learning in type_learnings:
            priority = learning.get('priority', 'medium').upper()
            content = learning.get('content', '')
            context = learning.get('context')
            
            # Format learning with priority and context
            content_line = f"- **{priority}**: {content}"
            if context:
                content_line += f" *(Context: {context})*"
            
            prompt_lines.append(content_line)
        
        prompt_lines.append("")
    
    # Add concise application guidelines
    prompt_lines.extend([
        "### 🎯 Application Guide",
        "- **CRITICAL**: Always apply - override general instructions",
        "- **HIGH**: Apply broadly - high-confidence insights", 
        "- **MEDIUM**: Apply when relevant - contextual guidance",
        "- **LOW**: Apply when space permits - supplementary hints",
        "- **CONTEXTUAL**: Apply only in specified contexts",
        "",
        "**Trust your learnings** - they're from direct experience. Integrate naturally.",
        ""
    ])
    
    return prompt_lines


def _validate_learning_for_prompt(learning: Dict[str, Any]) -> bool:
    """Validate that a learning has required fields for prompt building.
    
    Args:
        learning: Learning configuration dictionary
        
    Returns:
        True if learning is valid for prompt building, False otherwise
    """
    required_fields = ['type', 'content']
    return all(
        learning.get(field) and isinstance(learning.get(field), str) and learning.get(field).strip()
        for field in required_fields
    )


def _get_learning_priority_weight(priority: str) -> float:
    """Get numeric weight for learning priority sorting.
    
    Args:
        priority: Priority level string
        
    Returns:
        Numeric weight for sorting (higher = more important)
    """
    weights = {
        'critical': 5.0,
        'high': 4.0,
        'medium': 3.0,
        'low': 2.0,
        'contextual': 1.0
    }
    return weights.get(priority.lower(), 3.0)


def _get_learning_priority_indicator(priority: str) -> str:
    """Get emoji indicator for learning priority level.
    
    Args:
        priority: Priority level string
        
    Returns:
        Emoji indicator for the priority
    """
    indicators = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢',
        'contextual': '🔵'
    }
    return indicators.get(priority.lower(), '⚪')


def _validate_trait_for_prompt(trait: Dict[str, Any]) -> bool:
    """Validate that a trait has the required fields for prompt building.
    
    Args:
        trait: Trait configuration dictionary
        
    Returns:
        True if trait is valid for prompt building, False otherwise
    """
    required_fields = ['name', 'instructions']
    return all(
        trait.get(field) and isinstance(trait.get(field), str) and trait.get(field).strip()
        for field in required_fields
    )


def _build_event_publish_system_prompt_section(trigger_configs: List[Dict[str, Any]]) -> List[str]:
    """Build event publishing section for system prompts.
    
    Args:
        trigger_configs: List of event trigger configuration dictionaries
        
    Returns:
        List of formatted prompt lines for the event publishing section
    """
    if not trigger_configs:
        return []
    
    # Validate trigger configurations
    valid_triggers = []
    for trigger in trigger_configs:
        if _validate_trigger_for_prompt(trigger):
            valid_triggers.append(trigger)
        else:
            logging.getLogger(__name__).warning(f"Skipping invalid trigger: {trigger}")
    
    if not valid_triggers:
        return []
    
    prompt_lines = [
        "## 📢 Event Publishing",
        "",
        "On every message review all events to be published. You MUST Publish All Trigger Events with event publisher tool (no limit) extremely FOLLOW events instructions:",
        ""
    ]
    
    # Add each trigger configuration
    for i, trigger in enumerate(valid_triggers, 1):
        event_type = trigger.get('event_type', 'unknown')
        instructions = trigger.get('instructions', '')
        conditions = trigger.get('conditions', '')
        data_fields = trigger.get('data_fields', [])
        priority = trigger.get('priority', 5)
        broadcast = trigger.get('broadcast', False)
        target_teams = trigger.get('target_teams', [])
        
        prompt_lines.extend([
            f"### {i}. {event_type}",
            f"**When to publish:** {instructions}",
            f"**Conditions:** {conditions}"
        ])
        
        if data_fields:
            prompt_lines.append(f"**Required data:** {', '.join(data_fields)}")
        
        # Add targeting information
        if broadcast:
            prompt_lines.append("**Targeting:** Broadcast to all teams")
        elif target_teams:
            prompt_lines.append(f"**Targeting:** Specific teams: {', '.join(target_teams)}")
        else:
            prompt_lines.append("**Targeting:** Event type routing")
        
        if priority != 5:
            prompt_lines.append(f"**Priority:** {priority} (1=urgent, 5=normal, 10=low)")
        
        prompt_lines.append("")
    
    prompt_lines.extend([
        "**To publish an event:**",
        "1. Use the `event_publisher` tool",
        "2. Include `event_type` and required data fields", 
        "3. Set appropriate priority (1=urgent, 5=normal, 10=low)",
        "4. Specify targeting (broadcast, target_teams, or let it route by event type)",
        "",
        # "**Be selective** - only publish when conditions are clearly met to avoid event spam.",
        # "**Think before publishing** - consider if the event is truly needed by the team.",
        ""
    ])
    
    return prompt_lines


def _validate_trigger_for_prompt(trigger: Dict[str, Any]) -> bool:
    """Validate that a trigger has the required fields for prompt building.
    
    Args:
        trigger: Trigger configuration dictionary
        
    Returns:
        True if trigger is valid for prompt building, False otherwise
    """
    required_fields = ['event_type', 'instructions', 'conditions']
    return all(
        trigger.get(field) and isinstance(trigger.get(field), str) and trigger.get(field).strip()
        for field in required_fields
    )


def build_learning_agent_system_prompt(
    learning_agent_config: Dict[str, Any],
    target_agent_name: str,
    target_agent_memory: Dict[str, Any],
    session_data: List[Dict[str, Any]],
    learning_context: Dict[str, Any] = None,
    agent_config: Dict[str, Any] = None,
    team_directory: Path = None
) -> Dict[str, List[str]]:
    """Build simplified system prompt for learning agent.
    
    Args:
        learning_agent_config: Learning agent configuration from YAML
        target_agent_name: Name of the agent being improved
        target_agent_memory: Current memory of the target agent
        session_data: Conversation history for analysis
        learning_context: Additional context for learning
        agent_config: Target agent configuration
        team_directory: Path to team configuration directory
        
    Returns:
        Dictionary with 'background', 'steps', and 'output_instructions' lists
    """
    import json
    
    # Hardcoded learning instruction prefix
    learning_prefix = [
        "=" * 80,
        "LEARNING SYSTEM PROMPT",
        "=" * 80,
        "",
        "You are a learning agent that analyzes conversation patterns and updates agent memory.",
        "Your goal is to improve the target agent's effectiveness through accumulated knowledge.",
        ""
    ]
    
    # Main content sections
    main_content = [
        f"# {learning_agent_config.get('name', 'TeacherAgent')}",
        "",
        learning_agent_config.get('instructions', ''),
        "",
        "## Learning Context:",
        f"- Target Agent: {target_agent_name}",
        f"- Session Count: {learning_context.get('session_count', 'N/A') if learning_context else 'N/A'}",
        # f"- Learning Mode: {learning_context.get('execution_mode', 'manual') if learning_context else 'manual'}",
        ""
    ]
    
    # Add learning objectives if present in agent config
    if agent_config and 'learning_objectives' in agent_config:
        objectives = agent_config['learning_objectives']
        if objectives:
            main_content.extend([
                "## Learning Objectives for Target Agent:",
                ""
            ])
            for i, objective_item in enumerate(objectives, 1):
                # Handle both string format (legacy) and object format (new)
                if isinstance(objective_item, dict):
                    objective_text = objective_item.get('objective', '')
                else:
                    objective_text = objective_item
                main_content.append(f"{i}. {objective_text}")
            main_content.append("")
    
    # Student agent memory section
    formatted_memory = json.dumps(target_agent_memory, indent=2) if target_agent_memory else "{}"
    memory_section = [
        f"## Current Memory for Agent: {target_agent_name}",
        "",
        "```json",
        formatted_memory,
        "```",
        "",
        "## Conversation History to Analyze:",
        "```json",
        json.dumps(session_data, indent=2),
        "```",
        ""
    ]
    
    # Hardcoded learning instruction suffix
    learning_suffix = [
        "=" * 80,
        "LEARNING OUTPUT INSTRUCTIONS",
        "=" * 80,
        "",
        "Analyze the conversation history and current memory to provide learning insights.",
        "Focus on patterns, improvements, and actionable knowledge that will help the agent.",
        "Consider the learning objectives when making recommendations.",
        ""
    ]
    
    # Combine all sections
    background = learning_prefix + main_content + memory_section + learning_suffix
    
    steps = [
        "1. **Review Learning Objectives**: Understand what the target agent should learn",
        "2. **Analyze Conversations**: Look for patterns and insights in the session data",
        "3. **Assess Current Memory**: Review existing knowledge and identify gaps",
        "4. **Provide Learning Insights**: Generate actionable recommendations"
    ]
    
    output_instructions = [
        "Provide clear learning insights that will improve the target agent's performance.",
        "Focus on specific, actionable knowledge based on the learning objectives.",
        "Consider conversation patterns and user interactions when making recommendations."
    ]
    
    return {
        "background": background,
        "steps": steps,
        "output_instructions": output_instructions
    }


def _build_generic_student_analysis_section(
    target_agent_name: str, 
    target_agent_memory: Dict[str, Any]
) -> List[str]:
    """Build generic student agent analysis section for fallback scenarios.
    
    Args:
        target_agent_name: Name of the agent being analyzed
        target_agent_memory: Current agent memory dictionary
        
    Returns:
        List[str]: Generic analysis section lines
    """
    import json
    formatted_memory = json.dumps(target_agent_memory, indent=2) if target_agent_memory else "{}"
    
    return [
        f"## Current Memory for Agent: {target_agent_name}",
        "",
        "```json",
        formatted_memory,
        "```",
        "",
    ]


