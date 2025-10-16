"""
Configuration Manager for Enhanced Stream Processing

This module provides configuration management for the enhanced stream processing
system with environment-specific settings and validation.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger as log


class ConfigurationManager:
    """Manages configuration for enhanced stream processing."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default path.
        """
        if config_path is None:
            config_path = self._get_default_config_path()
        
        self.config_path = config_path
        self.config = self._load_config()
        self.environment = self._detect_environment()
        
        # Apply environment-specific overrides
        self._apply_environment_config()
        
        log.info(f"Configuration loaded for environment: {self.environment}")
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        base_dir = Path(__file__).parent.parent
        return str(base_dir / "config" / "enhanced_stream_config.yml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                log.info(f"Configuration loaded from {self.config_path}")
                return config
        except FileNotFoundError:
            log.warning(f"Configuration file not found: {self.config_path}")
            return self._get_default_config()
        except yaml.YAMLError as e:
            log.error(f"Error parsing configuration file: {e}")
            return self._get_default_config()
    
    def _detect_environment(self) -> str:
        """Detect the current environment."""
        env = os.getenv('VROUTER_ENV', 'development').lower()
        valid_environments = ['development', 'staging', 'production']
        
        if env not in valid_environments:
            log.warning(f"Unknown environment '{env}', defaulting to 'development'")
            env = 'development'
        
        return env
    
    def _apply_environment_config(self) -> None:
        """Apply environment-specific configuration overrides."""
        if 'environments' not in self.config:
            return
        
        env_config = self.config['environments'].get(self.environment, {})
        if not env_config:
            return
        
        # Recursively merge environment config
        self._deep_merge(self.config, env_config)
        log.info(f"Applied {self.environment} environment configuration")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when file is not available."""
        return {
            'worker_pool': {
                'max_workers': 5,
                'batch_size': 10,
                'timeout_seconds': 300
            },
            'retry_policy': {
                'max_retries': 3,
                'base_delay': 2.0,
                'max_delay': 30.0,
                'exponential_backoff': True
            },
            'monitoring': {
                'enable_metrics': True,
                'metrics_update_interval': 10.0,
                'log_level': 'INFO',
                'alerts': {
                    'high_queue_size': 100,
                    'high_error_rate': 0.1,
                    'low_throughput': 10,
                    'worker_failure_count': 3
                }
            },
            'performance': {
                'batch_processing_interval': 1.0,
                'enable_batch_processing': True,
                'queue_size_limit': 1000
            },
            'features': {
                'enable_enhanced_processing': True,
                'enable_legacy_fallback': True,
                'enable_metrics_export': True,
                'enable_health_checks': True
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Configuration key path (e.g., 'worker_pool.max_workers')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_worker_config(self) -> Dict[str, Any]:
        """Get worker pool configuration."""
        return self.get('worker_pool', {})
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry policy configuration."""
        return self.get('retry_policy', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.get('monitoring', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.get('performance', {})
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags."""
        return self.get('features', {})
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return self.get_feature_flags().get(feature_name, False)
    
    def validate_config(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []
        
        # Validate worker pool config
        max_workers = self.get('worker_pool.max_workers')
        if not isinstance(max_workers, int) or max_workers < 1:
            errors.append("worker_pool.max_workers must be a positive integer")
        
        batch_size = self.get('worker_pool.batch_size')
        if not isinstance(batch_size, int) or batch_size < 1:
            errors.append("worker_pool.batch_size must be a positive integer")
        
        # Validate retry config
        max_retries = self.get('retry_policy.max_retries')
        if not isinstance(max_retries, int) or max_retries < 0:
            errors.append("retry_policy.max_retries must be a non-negative integer")
        
        base_delay = self.get('retry_policy.base_delay')
        if not isinstance(base_delay, (int, float)) or base_delay < 0:
            errors.append("retry_policy.base_delay must be a non-negative number")
        
        # Validate monitoring config
        metrics_interval = self.get('monitoring.metrics_update_interval')
        if not isinstance(metrics_interval, (int, float)) or metrics_interval <= 0:
            errors.append("monitoring.metrics_update_interval must be a positive number")
        
        if errors:
            for error in errors:
                log.error(f"Configuration validation error: {error}")
            return False
        
        log.info("Configuration validation passed")
        return True
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            old_config = self.config.copy()
            self.config = self._load_config()
            self._apply_environment_config()
            
            if self.validate_config():
                log.info("Configuration reloaded successfully")
                return True
            else:
                # Restore old config if validation fails
                self.config = old_config
                log.error("Configuration reload failed validation, keeping old config")
                return False
                
        except Exception as e:
            log.error(f"Error reloading configuration: {e}")
            return False
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get information about the current environment."""
        return {
            'environment': self.environment,
            'config_path': self.config_path,
            'features_enabled': [
                feature for feature, enabled in self.get_feature_flags().items()
                if enabled
            ],
            'worker_count': self.get('worker_pool.max_workers'),
            'batch_size': self.get('worker_pool.batch_size'),
            'retry_max': self.get('retry_policy.max_retries')
        }


# Global configuration instance
_config_manager = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def reload_config() -> bool:
    """Reload the global configuration."""
    global _config_manager
    if _config_manager is not None:
        return _config_manager.reload_config()
    return False
