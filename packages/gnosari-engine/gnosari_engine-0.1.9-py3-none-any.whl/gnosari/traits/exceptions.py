"""Trait-specific exception classes."""


class TraitConfigurationError(Exception):
    """Custom exception for trait configuration errors."""
    
    def __init__(self, message: str, agent_name: str = None, trait_name: str = None, error_code: str = None):
        self.message = message
        self.agent_name = agent_name
        self.trait_name = trait_name
        self.error_code = error_code
        super().__init__(self.message)


class TraitValidationError(TraitConfigurationError):
    """Exception for trait validation failures."""
    pass


class TraitProcessingError(TraitConfigurationError):
    """Exception for trait processing failures."""
    pass