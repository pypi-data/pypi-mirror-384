"""Celery app configuration for Gnosari queue system."""

from celery import Celery
from .config import CeleryConfig


def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    app = Celery("gnosari")
    
    # Load configuration
    app.config_from_object(CeleryConfig)
    
    # Auto-discover tasks in consumers module
    app.autodiscover_tasks(["gnosari.queue.consumers"])
    
    return app


# Global Celery app instance
celery_app = create_celery_app()