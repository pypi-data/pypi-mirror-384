"""Celery configuration for Gnosari queue system."""

import os
from typing import Any, Dict


class CeleryConfig:
    """Celery configuration class following best practices."""
    
    # Broker and Result Backend
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Task Serialization
    task_serializer = "json"
    accept_content = ["json"]
    result_serializer = "json"
    
    # Task Result Configuration
    result_expires = 3600  # 1 hour
    result_persistent = True
    
    # Task Routing - Unified queue for all tasks and events
    task_routes = {
        "gnosari.queue.consumers.*": {"queue": "gnosari-events"}
    }
    
    # Worker Configuration
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = False
    
    # Task Configuration
    task_acks_late = True
    task_reject_on_worker_lost = True
    task_track_started = True
    
    # Timezone
    timezone = "UTC"
    enable_utc = True
    
    # Security
    worker_hijack_root_logger = False
    worker_log_color = False
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith("_") and attr != "get_config"
        }