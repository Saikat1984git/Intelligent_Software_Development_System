import os
from langchain_core.tools import tool

@tool
def read_file(file_path: str) -> str:
    """
    # Tool: Read File
    
    ## Overview
    Reads the content of a file at the specified path. Use this to inspect code before attempting to fix it.
    
    ## Input Parameters
    * `file_path` (string): The absolute or relative path to the file you want to read.
    
    ## Expected Output
    * Returns the contents of the file as a string. If the file cannot be found or read, returns an error message.
    """
    try:
        # 1. Strip extraneous whitespace or quotes that an LLM might accidentally pass
        cleaned_path = file_path.strip("'\" ")
        
        # 2. Expand '~' to the user's home directory if it's used in the path
        expanded_path = os.path.expanduser(cleaned_path)
        
        # 3. Resolve to a strict absolute path
        absolute_path = os.path.abspath(expanded_path)
        
        # 4. Open the file using the fully resolved path
        with open(absolute_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        # Provide the resolved path in the error so the LLM knows exactly where it tried to look
        resolved = absolute_path if 'absolute_path' in locals() else cleaned_path
        return f"Error reading file. Attempted path: {resolved}. Exception: {str(e)}"