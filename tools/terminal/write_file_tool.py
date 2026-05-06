import os
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
        # 1. Strip extraneous whitespace or quotes that an LLM might accidentally pass
        cleaned_path = file_path.strip("'\" ")
        
        # 2. Expand '~' to the user's home directory if it's used in the path
        expanded_path = os.path.expanduser(cleaned_path)
        
        # 3. Resolve to a strict absolute path
        absolute_path = os.path.abspath(expanded_path)
        
        # 4. Automatically create nested directories if they don't exist using the resolved path
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
        
        # 5. Write the file using the fully resolved path
        with open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"Successfully wrote to {absolute_path}"
        
    except Exception as e:
        # Provide the resolved path in the error so the LLM knows exactly where it tried to write
        resolved = absolute_path if 'absolute_path' in locals() else cleaned_path
        return f"Error writing to file. Attempted path: {resolved}. Exception: {str(e)}"