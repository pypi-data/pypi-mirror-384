# Importing necessary modules
import os
import logging
import traceback
from typing import Dict, List

# Importing necessary modules for config-loader
from config import ConfigClient
from requests.auth import HTTPBasicAuth

# Function to dynamically retrieve nested keys
def get_nested_config(config: Dict[str, str], key_parts: List[str]) -> str:
    """Retrieving nested configuration values from dictionary using list of keys

    Args:
        config (Dict[str, str]): The dictionary containing nested configuration data.
        key_parts (List[str]): List of keys passed as input to know which key-value pairs to search for and returning values.

    Returns:
        str: The final value if all keys in `key_parts` do exist and lead to a value; Otherwise None if key is invalid or missing.
    """
    
    value = config
    for part in key_parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
        if value is None:
            break
    return value

# Function to load configuration/environment variables
def load_cnf(service_name: str, required_keys: List[str], logger: logging.Logger) -> Dict[str, str]:
    """
    Loads configuration and environment variables for a specified service.

    This function first attempts to retrieve configuration values from a Spring Cloud Config Server.
    If the server is unavailable, it falls back to loading values from the local OS environment.
    The configuration values are fetched based on a list of required keys, and the resulting key-value
    pairs are stored in a dictionary.

    Args:
        service_name (str): The name of the service requesting the configuration, used in constructing 
                            the Spring Cloud Config Server URL.
        required_keys (List[str]): List of required configuration keys, expected in uppercase with 
                                   underscores to represent nested configurations.

    Returns:
        Dict[str, str]: A dictionary of loaded environment variables, where each required key is associated
                        with its retrieved value from either the Config Server or the local environment. If a 
                        value is unavailable, the corresponding key will map to `None`.
    """
    
    # Final variables
    ENVIRONMENT: str = os.getenv(key = 'ENVIRONMENT', default = 'dev')
    BASE_URL: str = os.getenv(key = 'BASE_URL')
    USERNAME: str = os.getenv(key = 'EMP_CONFIG_USERNAME')
    PASSWORD: str = os.getenv(key = 'EMP_ENCRYPT_KEY')
    
    # Dictionary to store environment variables
    env_vars: Dict[str, str] = {'ENVIRONMENT' : ENVIRONMENT}
    
    # Establishing connection to Spring Cloud Config Server 'CNF-S'
    try:
        cc: ConfigClient = ConfigClient(
            address = f'{BASE_URL}:8888',
            label = ENVIRONMENT,
            app_name = service_name,
            profile = ENVIRONMENT
        )
        cc.get_config(auth = HTTPBasicAuth(username = USERNAME, password = PASSWORD))
    except SystemExit:
        logger.warning(f'Error occurred in establishing connection with Spring Cloud Config Server \'(CNF-S)\' at environment \'{ENVIRONMENT}\'')
        
        # Fallback: In case Spring Cloud Config Server 'CNF-S' is not available - Loading environment variables from local OS / Profile
        try:
            for key in required_keys:
                if key not in env_vars.keys():
                    env_vars[key] = os.getenv(key = key)
            logger.info(f'Environment variables loaded successfully from local OS at environment \'{ENVIRONMENT}\'')
        except Exception as e:
            logger.error(f'Error occurred in loading environment variables from local OS at environment \'{ENVIRONMENT}\': {repr(e)} - {traceback.print_exc()}')
            raise
    else:
        
        # Loading environemnt variables from Spring Config Server 'CNF-S'
        try:
            config: Dict[str, str] = cc.config
            for key in required_keys:
                if key not in env_vars.keys():
                    key_parts = [part.lower() for part in key.split(sep = '_')]
                    value = get_nested_config(config = config, key_parts = key_parts)
                    env_vars[key] = value
            logger.info(f'Environment variables loaded successfully from Spring Cloud Config Server \'(CNF-S)\' at environment \'{ENVIRONMENT}\'')
        except Exception as e:
            logger.error(f'Error occurred in loading environment variables from Spring Cloud Config Server \'(CNF-S)\' at environment \'{ENVIRONMENT}\': {repr(e)} - Trace: {traceback.print_exc()}')
            raise
    # Returning built env_vars dictionary
    return env_vars