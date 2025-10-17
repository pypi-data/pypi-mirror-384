"""
Configuration management for the Kusto MCP server.
"""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

from .exceptions import ValidationError
from .logging_config import get_logger

logger = get_logger("config")


@dataclass
class ClusterConfig:
    """Configuration for a Kusto cluster"""
    name: str
    connection_string: str
    databases: List[str]
    description: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class CacheConfig:
    """Configuration for caching"""
    schema_cache_size: int = 500
    schema_cache_ttl_hours: int = 24
    query_handle_ttl_hours: int = 1
    enable_persistent_cache: bool = True
    cache_directory: str = "cache"


@dataclass
class PerformanceConfig:
    """Configuration for performance settings"""
    max_concurrent_queries: int = 10
    query_timeout_seconds: int = 30
    enable_query_metrics: bool = True
    enable_performance_logging: bool = True


@dataclass
class AntiHallucinationConfig:
    """Configuration for anti-hallucination features"""
    enable_schema_validation: bool = True
    enable_query_validation: bool = True
    enable_result_verification: bool = True
    max_sample_size: int = 100
    validation_timeout_seconds: int = 10


@dataclass
class ServerConfig:
    """Main server configuration"""
    clusters: List[ClusterConfig]
    cache: CacheConfig
    performance: PerformanceConfig
    anti_hallucination: AntiHallucinationConfig
    log_level: str = "INFO"
    enable_debug_mode: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """Create ServerConfig from dictionary"""
        clusters = [ClusterConfig(**cluster) for cluster in data.get('clusters', [])]
        cache = CacheConfig(**data.get('cache', {}))
        performance = PerformanceConfig(**data.get('performance', {}))
        anti_hallucination = AntiHallucinationConfig(**data.get('anti_hallucination', {}))
        
        return cls(
            clusters=clusters,
            cache=cache,
            performance=performance,
            anti_hallucination=anti_hallucination,
            log_level=data.get('log_level', 'INFO'),
            enable_debug_mode=data.get('enable_debug_mode', False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ServerConfig to dictionary"""
        return {
            'clusters': [asdict(cluster) for cluster in self.clusters],
            'cache': asdict(self.cache),
            'performance': asdict(self.performance),
            'anti_hallucination': asdict(self.anti_hallucination),
            'log_level': self.log_level,
            'enable_debug_mode': self.enable_debug_mode
        }


class ConfigManager:
    """Manages server configuration"""
    
    def __init__(self, config_file: str = "src/core/config.json"):
        self.config_file = config_file
        self._config: Optional[ServerConfig] = None
    
    def load_config(self) -> ServerConfig:
        """Load configuration from file"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.info(f"Config file {config_path} not found, creating default config")
            return self._create_default_config()
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            self._config = ServerConfig.from_dict(data)
            logger.info(f"Configuration loaded from {config_path}")
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise ValidationError(f"Invalid configuration file: {e}")
    
    def save_config(self, config: ServerConfig):
        """Save configuration to file"""
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            self._config = config
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            raise ValidationError(f"Failed to save configuration: {e}")
    
    def get_config(self) -> ServerConfig:
        """Get current configuration"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def _create_default_config(self) -> ServerConfig:
        """Create default configuration"""
        # Try to load clusters from legacy connection_strings.json
        clusters = self._load_legacy_clusters()
        
        config = ServerConfig(
            clusters=clusters,
            cache=CacheConfig(),
            performance=PerformanceConfig(),
            anti_hallucination=AntiHallucinationConfig()
        )
        
        # Save default config
        self.save_config(config)
        return config
    
    def _load_legacy_clusters(self) -> List[ClusterConfig]:
        """Load clusters from legacy connection_strings.json"""
        legacy_file = Path("cache/connection_strings.json")
        
        if not legacy_file.exists():
            logger.warning("No cluster configuration found")
            return []
        
        try:
            with open(legacy_file, 'r') as f:
                legacy_data = json.load(f)
            
            clusters = []
            for cluster_name, cluster_data in legacy_data.items():
                if isinstance(cluster_data, dict):
                    cluster = ClusterConfig(
                        name=cluster_name,
                        connection_string=cluster_data.get('connection_string', ''),
                        databases=cluster_data.get('databases', []),
                        description=cluster_data.get('description'),
                        tags=cluster_data.get('tags', [])
                    )
                    clusters.append(cluster)
            
            logger.info(f"Loaded {len(clusters)} clusters from legacy configuration")
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to load legacy configuration: {e}")
            return []
    
    def validate_config(self, config: ServerConfig) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not config.clusters:
            errors.append("No clusters configured")
        
        for i, cluster in enumerate(config.clusters):
            if not cluster.name:
                errors.append(f"Cluster {i}: name is required")
            
            if not cluster.connection_string:
                errors.append(f"Cluster {cluster.name}: connection_string is required")
            
            if not cluster.databases:
                errors.append(f"Cluster {cluster.name}: at least one database is required")
        
        if config.cache.schema_cache_size <= 0:
            errors.append("Cache size must be positive")
        
        if config.cache.schema_cache_ttl_hours <= 0:
            errors.append("Cache TTL must be positive")
        
        if config.performance.max_concurrent_queries <= 0:
            errors.append("Max concurrent queries must be positive")
        
        return errors


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> ServerConfig:
    """Get the current server configuration"""
    return config_manager.get_config()


def reload_config() -> ServerConfig:
    """Reload configuration from file"""
    return config_manager.load_config()