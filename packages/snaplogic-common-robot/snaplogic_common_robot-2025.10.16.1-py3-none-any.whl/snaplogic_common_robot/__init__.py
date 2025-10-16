"""
SLIM Common Robot Framework package.

This package provides common Robot Framework keywords and Python helper functions
for SLIM automation testing.

Import this package to access all keywords from all modules.


"""

# Import Python modules with @keyword decorators
from snaplogic_common_robot.libraries.utils import (
    walk_and_render_templates,
    retrieve_asset_id,
    load_env_variables,
    to_file_path_pair
)

# Import subpackages to make them available
from snaplogic_common_robot import snaplogic_apis_keywords

# Define __all__ to specify what gets imported with "from snaplogic_common_robot import *"
__all__ = [
    # Python helper functions with @keyword decorators
    'walk_and_render_templates',
    'retrieve_asset_id',
    'load_env_variables',
    'to_file_path_pair',
    
    # Subpackages
    'snaplogic_apis_keywords',
    'libraries',
    
    # Robot Framework specific
    'get_keyword_names',
    'run_keyword',
    'get_keyword_documentation'
]

# Robot Framework library information
ROBOT_LIBRARY_SCOPE = 'GLOBAL'
ROBOT_LIBRARY_VERSION = '1.0.0'  # You may want to make this dynamic

# Dictionary mapping keyword names to functions
KEYWORDS = {
    'Render Env Variables for JSON File': walk_and_render_templates,
    'Retrieve Asset Id': retrieve_asset_id,
    'Load Env Variables': load_env_variables,
    'Get Files In Dir': to_file_path_pair,
  
}

def get_keyword_names():
    """Return a list of keyword names that this library provides.
    
    This function is required by Robot Framework to get the available keywords.
    """
    return list(KEYWORDS.keys())

def run_keyword(name, args):
    """Run the specified keyword with the given arguments.
    
    This function is required by Robot Framework to execute keywords.
    """
    if name in KEYWORDS:
        return KEYWORDS[name](*args)
    else:
        raise ValueError(f"Keyword '{name}' not found")

def get_keyword_documentation(name):
    """Return documentation for the specified keyword.
    
    This function is optional but helpful for Robot Framework to provide documentation.
    """
    if name in KEYWORDS:
        return KEYWORDS[name].__doc__ or f"Documentation for '{name}' not available"
    else:
        return f"Keyword '{name}' not found"