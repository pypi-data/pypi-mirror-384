import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from .exceptions import ConfigurationError

# Default configuration file locations
DEFAULT_CONFIG_FILE = os.path.join(os.environ.get("HOME", ""), ".tkio_config.json")
DEFAULT_API_URL = "https://api.terrak.io"

def read_config_file(config_file: str = DEFAULT_CONFIG_FILE, logger: logging.Logger = None) -> Dict[str, Any]:
    """
    Read and parse the configuration file.
    
    Args:
        config_file: Path to the configuration file
        logger: Logger object to log messages
    Returns:
        Dict[str, Any]: Configuration parameters with additional flags:
                       'is_logged_in': True if user is logged in
                       'user_email': The email of the logged in user
                       'token': Personal token if available
        
    Note:
        This function no longer raises ConfigurationError. Instead, it creates an empty config
        file if one doesn't exist and returns appropriate status flags.
    """
    config_path = Path(os.path.expanduser(config_file))
    # the first circumstance is that the config file does not exist
    # that we need to login before using any of the functions
    # Check if config file exists
    if not config_path.exists():
        # Create an empty config file
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump({}, f)
        logger.info("No API key found. Please provide an API key to use this client.")
        return {
            'url': DEFAULT_API_URL,
            'key': None,
            'is_logged_in': False,
            'user_email': None,
            'token': None
        }
    
    try:
        # Read the config file
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Read the config file data
        # Check if config has an API key
        if not config_data or 'TERRAKIO_API_KEY' not in config_data or not config_data.get('TERRAKIO_API_KEY'):
            logger.info("No API key found. Please provide an API key to use this client.")
            return {
                'url': DEFAULT_API_URL,
                'key': None,
                'is_logged_in': False,
                'user_email': None,
                'token': config_data.get('PERSONAL_TOKEN')
            }
        logger.info(f"Currently logged in as: {config_data.get('EMAIL')}")
        # this meanb that we have already logged in to the tkio account
        
        # Convert the JSON config to our expected format
        config = {
            # Always use the default URL, not from config file
            'url': DEFAULT_API_URL,
            'key': config_data.get('TERRAKIO_API_KEY'),
            'is_logged_in': True,
            'user_email': config_data.get('EMAIL'),
            'token': config_data.get('PERSONAL_TOKEN')
        }
        return config
            

    except Exception as e:
        logger.info(f"Error reading config: {e}")
        logger.info("No API key found. Please provide an API key to use this client.")
        return {
            'url': DEFAULT_API_URL,
            'key': None,
            'is_logged_in': False,
            'user_email': None,
            'token': None
        }

def create_default_config(email: str, api_key: str, config_file: str = DEFAULT_CONFIG_FILE) -> None:
    """
    Create a default configuration file in JSON format.
    
    Args:
        email: User email
        api_key: Terrakio API key
        config_file: Path to configuration file
        
    Raises:
        ConfigurationError: If the configuration file can't be created
    """
    config_path = Path(os.path.expanduser(config_file))
    
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        config_data = {
            "EMAIL": email,
            "TERRAKIO_API_KEY": api_key
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
            
    except Exception as e:
        raise ConfigurationError(f"Failed to create configuration file: {e}")