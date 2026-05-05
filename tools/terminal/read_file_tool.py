import os
import subprocess
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
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"
