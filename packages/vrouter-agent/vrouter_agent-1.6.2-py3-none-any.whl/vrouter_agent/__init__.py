"""
USDN vRouter-agent package for executing orders on each node.

This package provides the core functionality for the vrouter-agent,
including order execution, configuration management, and monitoring.
"""

__version__ = "1.4.0"
__author__ = "Phan Dang"
__email__ = "phan.dang@usdatanetworks.com"
__license__ = "US Data Networks. All rights reserved."

# Make commonly used classes and functions available at package level
try:
    # Don't import main module to avoid conflicts when running with python -m
    # from .main import app
    from .config_manager import ConfigManager
    from .agent import Agent
    from .enhanced_stream_processor import EnhancedStreamProcessor
    from .monitoring import MonitoringService
except ImportError:
    # Handle import errors gracefully during package installation
    pass

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__license__",
    # "app",  # Removed to avoid import conflicts with python -m execution
    "ConfigManager",
    "Agent",
    "EnhancedStreamProcessor",
    "MonitoringService",
]