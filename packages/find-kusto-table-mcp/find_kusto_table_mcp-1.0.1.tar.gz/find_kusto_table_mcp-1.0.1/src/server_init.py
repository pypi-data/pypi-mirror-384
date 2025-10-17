"""
Server Initialization Module

Handles all server startup tasks including:
- Service initialization
- Confidential template auto-loading
- Global configuration
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

from .core.logging_config import get_logger
from .services.schema_cache_service import get_schema_cache_service
from .services.query_template_service import get_query_template_service, QueryParameter, ParameterType
from .services.analytics_engine import create_analytics_engine
from .services.query_optimizer import create_query_optimizer
from .tools.table_discovery import create_smart_table_discovery
from .utils.kusto_client import get_connection_manager

logger = get_logger("server_init")


def initialize_services(cache_dir: str) -> Dict[str, Any]:
    """
    Initialize all service singletons.
    
    Args:
        cache_dir: Directory for cache files
    
    Returns:
        Dictionary of initialized service objects
    """
    logger.info("Initializing services...")
    
    # Initialize services (singletons)
    schema_cache = get_schema_cache_service()
    templates = get_query_template_service()
    table_discovery = create_smart_table_discovery()
    analytics_engine = create_analytics_engine()
    query_optimizer = create_query_optimizer()
    connection_manager = get_connection_manager()
    
    # Override service cache paths with command line arguments
    schema_cache.cache_file = os.path.join(cache_dir, "schema_cache.json")
    schema_cache.notes_file = os.path.join(cache_dir, "table_notes.json")
    
    services = {
        'schema_cache': schema_cache,
        'templates': templates,
        'table_discovery': table_discovery,
        'analytics_engine': analytics_engine,
        'query_optimizer': query_optimizer,
        'connection_manager': connection_manager
    }
    
    logger.info("Services initialized successfully")
    return services


def load_confidential_templates(templates_service):
    """
    Load confidential workflow templates from cache/templates/ directory.
    
    Args:
        templates_service: Query template service instance
    """
    template_dir = Path(__file__).parent.parent / "cache" / "templates"
    
    if not template_dir.exists():
        logger.debug("No confidential templates directory found")
        return
    
    json_files = list(template_dir.glob("*.json"))
    if not json_files:
        logger.debug("No confidential template files found")
        return
    
    logger.info(f"Loading {len(json_files)} confidential template(s) from cache/templates/")
    
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # Convert parameters
            params = [
                QueryParameter(
                    name=p["name"],
                    type=ParameterType(p["type"]),
                    description=p["description"],
                    default_value=p.get("default_value"),
                    required=p.get("required", True)
                )
                for p in template_data["parameters"]
            ]
            
            # Delete existing template if it exists (for confidential template updates)
            template_name = template_data["name"]
            if template_name in templates_service.templates:
                logger.info(f"Updating existing confidential template: {template_name}")
                templates_service.delete_template(template_name)
            
            # Create template
            success, error = templates_service.create_template(
                name=template_name,
                description=template_data["description"],
                query=template_data["query"],
                parameters=params,
                tags=template_data.get("tags", []),
                metadata=template_data.get("metadata", {})
            )
            
            if success:
                logger.info(f"Loaded confidential template: {template_name}")
            else:
                logger.warning(f"Failed to load template {template_name}: {error}")
                
        except Exception as e:
            logger.error(f"Error loading template {filepath.name}: {e}")


__all__ = ['initialize_services', 'load_confidential_templates']
