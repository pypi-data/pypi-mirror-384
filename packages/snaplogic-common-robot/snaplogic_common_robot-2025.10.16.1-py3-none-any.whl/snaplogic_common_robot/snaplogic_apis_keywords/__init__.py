"""
Common APIs Keywords for Robot Framework.

This package provides Robot Framework resource files with keywords for API testing
and platform operations.

The resource files can be imported in Robot Framework tests using:
    *** Settings ***
    Resource    snaplogic_common_robot/snaplogic_apis_keywords/snaplogic_apis.resource
    Resource    snaplogic_common_robot/snaplogic_apis_keywords/snaplogic_keywords.resource
"""

import os
import pkg_resources

# Define __all__ to specify what gets imported with "from snaplogic_common_robot.snaplogic_apis_keywords import *"
__all__ = [
    # The resource files are not directly importable in Python,
    # but we list them here for documentation purposes
    'snaplogic_apis.resource',
    'snaplogic_keywords.resource',
    'common_utilities.resource',
    'get_resource_path'
]

def get_resource_path(resource_name):
    """
    Get the full path to a resource file in this package.
    
    This is useful for programmatically locating resource files
    when they're installed as part of a Python package.
    
    Args:
        resource_name: Name of the resource file (e.g., 'snaplogic_apis.resource')
        
    Returns:
        Full path to the resource file
    """
    return pkg_resources.resource_filename('snaplogic_common_robot.snaplogic_apis_keywords', resource_name)