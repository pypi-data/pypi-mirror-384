import os
import json
import re
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from robot.api.deco import keyword


@keyword("Render Env Variables for JSON File")
def walk_and_render_templates(template_path, env_variables):
    """
    Renders Jinja2 templates with environment variables and returns the parsed JSON.
    Accepts either a file path or a directory path.
    
    Args:
        template_path: Path to a JSON template file or directory containing templates
        env_variables: Dictionary of variables to use for rendering
        
    Returns:
        List of parsed JSON objects
    """
    # Check if the path is a file or directory
    is_file = os.path.isfile(template_path)
    
    if is_file:
        # Handle single file case
        template_dir = os.path.dirname(template_path)
        template_filename = os.path.basename(template_path)
        
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False
        )
        
        try:
            template = env.get_template(template_filename)
            render = template.render(env_variables)
            payload = json.loads(render)
            return [payload]  # Return as a list to maintain compatibility
        except Exception as e:
            print(f"Error processing template {template_path}: {str(e)}")
            raise
    else:
        # Handle directory case (original functionality)
        template_dir = template_path
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False
        )

        # Walk through the directory
        rendered_content = []
        for root, _, files in os.walk(template_dir):
            for filename in files:
                if filename.endswith('.json'):  # Only process JSON files
                    try:
                        # Get relative path from template_dir
                        rel_path = os.path.relpath(os.path.join(root, filename), template_dir)
                        template = env.get_template(rel_path)
                        render = template.render(env_variables)
                        payloads = json.loads(render)
                        rendered_content.append(payloads)
                    except Exception as e:
                        print(f"Error processing template {os.path.join(root, filename)}: {str(e)}")
                        # Continue processing other files instead of failing completely
        
        if not rendered_content:
            raise FileNotFoundError(f"No valid JSON templates found in {template_dir}")
            
        return rendered_content


@keyword("Retrieve Asset Id")
def retrieve_asset_id(list_account_response_json):
    try:
        entries = list_account_response_json.get('response_map', {}).get('entries', [])
        if entries:
            return entries[0]['asset_id']
        else:
            raise Exception("Account not found in the response.")
    except KeyError as e:
        raise Exception(f"Missing expected key in response JSON: {e}")


@keyword("Load Env Variables")
def load_env_variables(env_file_path):
    """
    Load variables from a .env file.
    """
    # Load the environment variables from .env file
    load_dotenv(env_file_path)
    
    # Create a dictionary with all environment variables
    env_variables = {}
    for key, value in os.environ.items():
        env_variables[key] = value
    
    return env_variables


@keyword("Get Files In Dir")
def to_file_path_pair(dir_path):
    files_list = []

    for root, dirs, files in os.walk(dir_path):
        if not files and not dirs:
            continue

        for file in files:
            full_path = os.path.join(root, file)
            files_list.append((file, full_path))

    return files_list