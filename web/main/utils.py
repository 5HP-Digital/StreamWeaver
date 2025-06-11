import os
import json
import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

class ConfigStore:
    """
    A file-based key-value store for persisting settings and configuration in JSON format.
    
    This class provides methods to read, write, and update configuration data stored in JSON files.
    The storage location is determined by the CONFIG_DIR environment variable.
    """
    
    def __init__(self, namespace=None):
        """
        Initialize the ConfigStore with an optional namespace.
        
        Args:
            namespace (str, optional): A namespace to organize configuration files.
                                      If provided, files will be stored in a subdirectory.
        """
        self.namespace = namespace
        self.config_dir = self._get_config_dir()
        
        # Create the config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
    
    def _get_config_dir(self):
        """
        Get the configuration directory based on environment variables.
        
        Returns:
            Path: The path to the configuration directory.
        """
        # Get the CONFIG_DIR from environment variables
        config_path = settings.CONFIG_DIR

        # Create a Path object
        config_dir = Path(config_path)
        
        # If namespace is provided, add it to the path
        if self.namespace:
            config_dir = config_dir / self.namespace
        
        return config_dir
    
    def _get_file_path(self, key):
        """
        Get the file path for a given key.
        
        Args:
            key (str): The key for the configuration.
        
        Returns:
            Path: The path to the configuration file.
        """
        # Sanitize the key to ensure it's a valid filename
        safe_key = key.replace(':', '_').replace('/', '_')
        return self.config_dir / f"{safe_key}.json"
    
    def get(self, key, default=None):
        """
        Get the configuration value for a given key.
        
        Args:
            key (str): The key for the configuration.
            default (any, optional): The default value to return if the key doesn't exist.
        
        Returns:
            any: The configuration value, or the default if the key doesn't exist.
        """
        file_path = self._get_file_path(key)
        
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            return default
        except Exception as e:
            logger.error(f"Error reading configuration for key {key}: {str(e)}")
            return default
    
    def set(self, key, value):
        """
        Set the configuration value for a given key.
        
        Args:
            key (str): The key for the configuration.
            value (any): The value to store. Must be JSON serializable.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        file_path = self._get_file_path(key)
        
        try:
            # Ensure the directory exists
            os.makedirs(file_path.parent, exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(value, f, indent=2, sort_keys=True, default=str)
            return True
        except Exception as e:
            logger.error(f"Error writing configuration for key {key}: {str(e)}")
            return False
    
    def delete(self, key):
        """
        Delete the configuration for a given key.
        
        Args:
            key (str): The key for the configuration.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        file_path = self._get_file_path(key)
        
        try:
            if file_path.exists():
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting configuration for key {key}: {str(e)}")
            return False
    
    def list_keys(self):
        """
        List all configuration keys in the store.
        
        Returns:
            list: A list of all keys in the store.
        """
        try:
            if not self.config_dir.exists():
                return []
            
            keys = []
            for file_path in self.config_dir.glob('*.json'):
                key = file_path.stem.replace('_', ':')
                keys.append(key)
            return keys
        except Exception as e:
            logger.error(f"Error listing configuration keys: {str(e)}")
            return []