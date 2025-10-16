"""
Utilities for setting up LLM providers with the OpenAI Agents SDK.
"""

import logging
from typing import Optional

from .base import provider_registry


def setup_provider_for_model(model: str) -> bool:
    """
    Configure the OpenAI Agents SDK to use the appropriate provider for a model.
    
    This function automatically detects which provider should be used based on
    the model name and configures the OpenAI Agents SDK accordingly.
    
    Args:
        model: Model name (e.g., "gpt-4o", "claude-3-5-sonnet", "deepseek-chat")
        
    Returns:
        True if provider was set up successfully, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Get the appropriate provider for this model
        provider = provider_registry.get_provider_for_model(model)
        
        if not provider:
            logger.warning(f"No provider found for model '{model}', using default OpenAI client")
            return False
        
        # Create the client for this provider
        client = provider.create_client()
        
        if not client:
            logger.error(f"Failed to create client for provider '{provider.get_provider_name()}'")
            return False
        
        # Set this as the default OpenAI client for the Agents SDK
        try:
            from agents import set_default_openai_client
            set_default_openai_client(client)
            logger.info(f"Set up {provider.get_provider_name()} provider for model '{model}'")
            return True
            
        except ImportError:
            logger.error("OpenAI Agents SDK not available - cannot set default client")
            return False
            
    except Exception as e:
        logger.error(f"Failed to setup provider for model '{model}': {e}")
        return False


def setup_provider_by_name(provider_name: str, api_key: Optional[str] = None) -> bool:
    """
    Set up a specific provider by name.
    
    Args:
        provider_name: Name of the provider ("openai", "anthropic", "deepseek")
        api_key: Optional API key to use (overrides environment variable)
        
    Returns:
        True if provider was set up successfully, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        provider = provider_registry.get_provider(provider_name)
        
        if not provider:
            logger.error(f"Provider '{provider_name}' not found")
            return False
        
        # Override API key if provided
        if api_key:
            provider.config.api_key = api_key
        
        # Create the client
        client = provider.create_client()
        
        if not client:
            logger.error(f"Failed to create client for provider '{provider_name}'")
            return False
        
        # Set as default
        try:
            from agents import set_default_openai_client
            set_default_openai_client(client)
            logger.info(f"Set up {provider_name} provider")
            return True
            
        except ImportError:
            logger.error("OpenAI Agents SDK not available - cannot set default client")
            return False
            
    except Exception as e:
        logger.error(f"Failed to setup provider '{provider_name}': {e}")
        return False


def list_available_models() -> dict:
    """
    List all available models from all registered providers.
    
    Returns:
        Dictionary mapping provider names to their supported models
    """
    return provider_registry.list_supported_models()


def get_provider_for_model(model: str) -> Optional[str]:
    """
    Get the provider name that supports a given model.
    
    Args:
        model: Model name
        
    Returns:
        Provider name or None if no provider supports the model
    """
    provider = provider_registry.get_provider_for_model(model)
    return provider.get_provider_name() if provider else None