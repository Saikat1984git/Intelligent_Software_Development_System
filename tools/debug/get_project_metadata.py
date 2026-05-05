import json
import os
from langchain_core.tools import tool

@tool
def get_project_metadata(file_path: str = "project_metadata.json") -> str:
    """
    Reads and parses the project_metadata.json file.
    Use this tool to extract project configuration, build steps, dependencies, 
    or any other metadata required for execution or debugging.
    
    Args:
        file_path: The path to the metadata file. Defaults to "project_metadata.json".
    """
    # Check if the file exists before attempting to open it
    if not os.path.exists(file_path):
        return f"Error: The file '{file_path}' does not exist in the current working directory ({os.getcwd()})."
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
            # Return as a cleanly formatted JSON string so the agent can easily comprehend it
            return json.dumps(metadata, indent=2)
            
    except json.JSONDecodeError as e:
        return f"Error: The file '{file_path}' contains invalid JSON. Details: {str(e)}"
    except PermissionError:
        return f"Error: Permission denied when trying to read '{file_path}'."
    except Exception as e:
        return f"An unexpected error occurred while reading '{file_path}': {str(e)}"