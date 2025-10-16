"""Utility functions for schema validation and normalization."""

import re


def normalize_identifier(value: str) -> str:
    """
    Normalize an identifier to be alphanumeric with underscores.
    
    This function handles trait names, component IDs, and other identifiers
    by converting them to a consistent format.
    
    Args:
        value: The input identifier string
        
    Returns:
        Normalized identifier string
        
    Raises:
        ValueError: If the identifier is empty after normalization
        
    Examples:
        >>> normalize_identifier("Customer Obsessed")
        'customer_obsessed'
        >>> normalize_identifier("Multi  Word   Name")
        'multi_word_name'
        >>> normalize_identifier("kebab-case-name")
        'kebab-case-name'
    """
    if not isinstance(value, str):
        raise ValueError("Identifier must be a string")
    
    # Convert to lowercase and replace spaces and other non-alphanumeric chars with underscores
    normalized = re.sub(r'[^a-zA-Z0-9_-]', '_', value.lower())
    
    # Remove multiple consecutive underscores
    normalized = re.sub(r'_+', '_', normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    if not normalized:
        raise ValueError('Identifier cannot be empty after normalization')
    
    return normalized


def create_identifier_validator(field_name: str = "identifier"):
    """
    Create a Pydantic validator function for identifier normalization.
    
    Args:
        field_name: Name of the field being validated (for error messages)
        
    Returns:
        Validator function that can be used with Pydantic
    """
    def validator_func(cls, v):
        try:
            return normalize_identifier(v)
        except ValueError as e:
            raise ValueError(f"{field_name.title()} {str(e).lower()}")
    
    validator_func.__name__ = f"validate_{field_name}"
    validator_func.__doc__ = f"Normalize {field_name} to be alphanumeric with underscores."
    
    return validator_func