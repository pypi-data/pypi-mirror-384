"""
Python Helper Files for Robot Framework.

This package provides Python modules with helper functions decorated with @keyword
for use in Robot Framework test suites.

These keywords can be used directly when importing the main library:
    *** Settings ***
    Library    snaplogic_common_robot
"""

# Import all keyword functions from the modules
from snaplogic_common_robot.libraries.utils import (
    walk_and_render_templates,
    retrieve_asset_id,
    load_env_variables,
    to_file_path_pair,
)


# Define __all__ to specify what gets imported with "from snaplogic_common_robot.python_helper_files import *"
__all__ = [
    # Modules
    'utils',

    
    # Functions from utils
    'walk_and_render_templates',
    'retrieve_asset_id',
    'load_env_variables',
    'to_file_path_pair',
]
    
    # Functions from file_helper
 

# Dictionary mapping keyword names to functions for easier access
KEYWORDS = {
    'Render Env Variables for JSON File': walk_and_render_templates,
    'Retrieve Asset Id': retrieve_asset_id,
    'Load Env Variables': load_env_variables,
    'Get Files In Dir': to_file_path_pair,
}