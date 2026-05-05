import os
import subprocess
from langchain_core.tools import tool


@tool
def write_file(file_path: str, content: str) -> str:
    """
    # Tool: Write File
    
    ## Overview
    Writes the provided content to a file at the specified path. This completely overwrites the existing file.
    
    ## Input Parameters
    * `file_path` (string): The absolute or relative path to the file you want to write to.
    * `content` (string): The complete text content to write into the file. Do not use placeholders; provide the full, executable code.
    
    ## Expected Output
    * Returns a success message if written correctly, or an error message if it fails.
    """
    try:
        # Automatically create nested directories if they don't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to file {file_path}: {str(e)}"
