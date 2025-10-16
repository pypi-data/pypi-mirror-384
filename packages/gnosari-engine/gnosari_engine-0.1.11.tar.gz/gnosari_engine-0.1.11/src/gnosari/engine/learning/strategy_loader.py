"""Learning strategy and competency component loader for the Gnosari framework."""

from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml
from ...schemas.learning import LearningStrategyConfig, CompetencyConfig


class LearningStrategyLoader:
    """Loads learning strategy and competency components from YAML configurations.
    
    This loader follows the Gnosari modular configuration pattern, supporting both
    modular team directories and single-file team configurations with embedded
    learning components.
    """
    
    def __init__(self, team_directory: Path):
        """Initialize strategy loader for a team configuration.
        
        Args:
            team_directory: Path to team configuration directory or file
        """
        self.team_directory = team_directory
        self.strategies_cache: Dict[str, LearningStrategyConfig] = {}
        self.competencies_cache: Dict[str, CompetencyConfig] = {}
        self._embedded_strategies: Optional[Dict[str, Any]] = None
        self._embedded_competencies: Optional[Dict[str, Any]] = None
        
        # Initialize embedded components if using single file configuration
        self._load_embedded_components()
    
    def _load_embedded_components(self):
        """Load embedded learning components from single-file configuration."""
        if self.team_directory.is_file() and self.team_directory.suffix in ['.yaml', '.yml']:
            try:
                with open(self.team_directory, 'r') as f:
                    team_config = yaml.safe_load(f)
                
                # Extract embedded learning components
                self._embedded_strategies = team_config.get('learning_strategies', {})
                self._embedded_competencies = team_config.get('learning_competencies', {})
                
            except Exception:
                # If file doesn't exist or parse error, use empty configs
                self._embedded_strategies = {}
                self._embedded_competencies = {}
    
    def load_strategy(self, strategy_id: str) -> LearningStrategyConfig:
        """Load learning strategy configuration by ID.
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            LearningStrategyConfig: Loaded and validated strategy configuration
            
        Raises:
            ValueError: If strategy not found or validation fails
        """
        if strategy_id in self.strategies_cache:
            return self.strategies_cache[strategy_id]
        
        strategy_config = self._load_strategy_config(strategy_id)
        
        # Auto-infer ID from filename/key following Gnosari pattern
        strategy_config['id'] = strategy_id
        
        # Validate and create schema instance
        try:
            validated_strategy = LearningStrategyConfig(**strategy_config)
            self.strategies_cache[strategy_id] = validated_strategy
            return validated_strategy
        except Exception as e:
            raise ValueError(f"Invalid learning strategy configuration for '{strategy_id}': {str(e)}")
    
    def _load_strategy_config(self, strategy_id: str) -> Dict[str, Any]:
        """Load raw strategy configuration from file or embedded config.
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            Dict[str, Any]: Raw strategy configuration
            
        Raises:
            ValueError: If strategy not found
        """
        # Try embedded strategies first (single-file configuration)
        if self._embedded_strategies and strategy_id in self._embedded_strategies:
            return self._embedded_strategies[strategy_id].copy()
        
        # Try modular file configuration
        if self.team_directory.is_dir():
            strategy_path = self.team_directory / "learning" / "strategies" / f"{strategy_id}.yaml"
            if strategy_path.exists():
                with open(strategy_path, 'r') as f:
                    return yaml.safe_load(f)
        
        raise ValueError(f"Learning strategy '{strategy_id}' not found")
    
    def load_competency(self, competency_id: str) -> CompetencyConfig:
        """Load competency focus configuration by ID.
        
        Args:
            competency_id: Competency identifier
            
        Returns:
            CompetencyConfig: Loaded and validated competency configuration
            
        Raises:
            ValueError: If competency not found or validation fails
        """
        if competency_id in self.competencies_cache:
            return self.competencies_cache[competency_id]
        
        competency_config = self._load_competency_config(competency_id)
        
        # Auto-infer ID from filename/key following Gnosari pattern
        competency_config['id'] = competency_id
        
        # Validate and create schema instance
        try:
            validated_competency = CompetencyConfig(**competency_config)
            self.competencies_cache[competency_id] = validated_competency
            return validated_competency
        except Exception as e:
            raise ValueError(f"Invalid competency configuration for '{competency_id}': {str(e)}")
    
    def _load_competency_config(self, competency_id: str) -> Dict[str, Any]:
        """Load raw competency configuration from file or embedded config.
        
        Args:
            competency_id: Competency identifier
            
        Returns:
            Dict[str, Any]: Raw competency configuration
            
        Raises:
            ValueError: If competency not found
        """
        # Try embedded competencies first (single-file configuration)
        if self._embedded_competencies and competency_id in self._embedded_competencies:
            return self._embedded_competencies[competency_id].copy()
        
        # Try modular file configuration
        if self.team_directory.is_dir():
            competency_path = self.team_directory / "learning" / "competencies" / f"{competency_id}.yaml"
            if competency_path.exists():
                with open(competency_path, 'r') as f:
                    return yaml.safe_load(f)
        
        raise ValueError(f"Learning competency '{competency_id}' not found")
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available learning strategy IDs.
        
        Returns:
            List[str]: Available strategy identifiers
        """
        strategies = set()
        
        # Add embedded strategies
        if self._embedded_strategies:
            strategies.update(self._embedded_strategies.keys())
        
        # Add modular strategies
        if self.team_directory.is_dir():
            strategies_dir = self.team_directory / "learning" / "strategies"
            if strategies_dir.exists():
                strategies.update(f.stem for f in strategies_dir.glob("*.yaml"))
        
        return sorted(strategies)
    
    def get_available_competencies(self) -> List[str]:
        """Get list of available competency focus IDs.
        
        Returns:
            List[str]: Available competency identifiers
        """
        competencies = set()
        
        # Add embedded competencies
        if self._embedded_competencies:
            competencies.update(self._embedded_competencies.keys())
        
        # Add modular competencies
        if self.team_directory.is_dir():
            competencies_dir = self.team_directory / "learning" / "competencies"
            if competencies_dir.exists():
                competencies.update(f.stem for f in competencies_dir.glob("*.yaml"))
        
        return sorted(competencies)
    
    def has_learning_configuration(self) -> bool:
        """Check if team has any learning configuration available.
        
        Returns:
            bool: True if learning strategies or competencies are available
        """
        return bool(self.get_available_strategies() or self.get_available_competencies())
    
    def get_default_strategy_config(self) -> Dict[str, Any]:
        """Get default strategy configuration for fallback scenarios.
        
        Returns:
            Dict[str, Any]: Default general-purpose strategy configuration
        """
        return {
            'id': 'general',
            'name': 'General Learning Strategy',
            'description': 'General-purpose learning approach for all agent types',
            'category': 'general',
            'tags': ['general', 'fallback'],
            'focus_areas': ['communication', 'effectiveness', 'accuracy'],
            'analysis_criteria': [
                {
                    'criterion': 'clarity',
                    'description': 'Are the instructions clear and unambiguous?',
                    'weight': 1.0
                },
                {
                    'criterion': 'completeness',
                    'description': 'Do they cover the scenarios seen in conversations?',
                    'weight': 1.0
                },
                {
                    'criterion': 'effectiveness',
                    'description': 'Do they lead to helpful and accurate responses?',
                    'weight': 1.0
                }
            ],
            'learning_objectives': [
                'Improve clarity of communication',
                'Enhance response accuracy',
                'Increase user satisfaction'
            ],
            'instruction_templates': {
                'analysis_focus': 'Focus on general communication effectiveness and clarity.',
                'improvement_guidance': 'Improve clarity, completeness, and effectiveness of responses.'
            }
        }