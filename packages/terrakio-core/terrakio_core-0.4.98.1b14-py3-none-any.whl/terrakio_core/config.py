import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from .exceptions import ConfigurationError

# Default configuration file locations
DEFAULT_CONFIG_FILE = os.path.join(os.environ.get("HOME", ""), ".tkio_config.json")
DEFAULT_API_URL = "https://dev-au.terrak.io"

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
    
    if not config_path.exists():
        logger.info("No API key found. Please provide an API key to use this client.")
        return {
            'url': DEFAULT_API_URL,
            'key': None,
            'is_logged_in': False,
            'user_email': None,
            'token': None
        }
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
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
        
        config = {
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