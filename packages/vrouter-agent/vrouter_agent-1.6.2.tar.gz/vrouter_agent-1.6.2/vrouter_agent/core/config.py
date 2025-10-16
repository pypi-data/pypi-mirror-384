from pydantic_settings import BaseSettings
import yaml
from vrouter_agent.core.base import AppConfig, Interface

class Settings(BaseSettings):
    config: AppConfig

    @classmethod
    def load_config(cls):
        """
        Load the configuration from the YAML file.
        This method reads the configuration file and initializes the AppConfig object.
        """
        # Load the configuration from the YAML file
        with open("/etc/vrouter-agent/config.yaml", "r") as f:
            raw_config = yaml.safe_load(f)
        return cls(config=AppConfig(**raw_config))


settings = Settings.load_config()


def get_primary_interface(type: str = "lan") -> "Interface":
    """
    Get the primary interface of the specified type (lan or wan).
    
    Args:
        type: The type of interface to get (default is 'lan').
        
    Returns:
        The interface object of the specified type.
    Raises:
        ValueError: If no primary interface of the specified type is found.
    """
    primary_interfaces = [
        interface for interface in settings.config.interfaces
        if interface.is_primary and interface.type == type
    ]
    
    if not primary_interfaces:
        raise ValueError(f"No primary {type} interface found.")
    
    return primary_interfaces[0]
    
    
    