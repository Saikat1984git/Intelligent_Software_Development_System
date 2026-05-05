import os
import json
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Define the schema for strict input validation
class ProjectStructureInput(BaseModel):
    structure_json: str = Field(
        description="A JSON-formatted string representing the project hierarchy. See tool description for exact formatting."
    )
    base_path: Optional[str] = Field(
        default=".", 
        description="The root directory path where the structure should be created. Defaults to current directory."
    )

@tool("create_project_structure", args_schema=ProjectStructureInput)
def create_project_structure_tool(structure_json: str, base_path: str) -> str:
    """
    Creates a complete project directory and file structure with empty files on the local filesystem.
    
    The LLM must provide a valid JSON string where keys are folder/file names. 
    Nested objects represent subdirectories, and empty strings ("") represent files.

    SAMPLE INPUT (structure_json):
    '{
        "my_new_app": {
            "src": {
                "__init__.py": "",
                "main.py": "",
                "helpers": {
                    "utils.py": ""
                }
            },
            "tests": {
                "test_main.py": ""
            },
            "requirements.txt": "",
            "README.md": ""
        }
    }'

    SAMPLE OUTPUT (Success):
    "Success! Project structure created at '/absolute/path/to/base_path/my_new_app'"

    SAMPLE OUTPUT (Error):
    "Error: Failed to parse JSON. Please provide a valid JSON string..."
    """
    try:
        # Parse the JSON string provided by the LLM
        structure = json.loads(structure_json)
    except json.JSONDecodeError as e:
        return f"Error: Failed to parse JSON. Please provide a valid JSON string. Details: {e}"

    def _build_tree(current_path: str, current_struct: dict):
        for name, content in current_struct.items():
            item_path = os.path.join(current_path, name)
            
            if isinstance(content, dict):
                # It's a directory: create it and recurse
                os.makedirs(item_path, exist_ok=True)
                _build_tree(item_path, content)
            else:
                # It's a file: create parent dirs if needed, then create empty file
                os.makedirs(os.path.dirname(item_path), exist_ok=True)
                with open(item_path, 'w') as f:
                    pass # Creates an empty file

    try:
        # Ensure the base directory exists
        os.makedirs(base_path, exist_ok=True)
        # Start the recursive creation
        _build_tree(base_path, structure)
        return f"Success! Project structure created at '{os.path.abspath(base_path)}'"
    except Exception as e:
        return f"An error occurred while creating the file system structure: {e}"