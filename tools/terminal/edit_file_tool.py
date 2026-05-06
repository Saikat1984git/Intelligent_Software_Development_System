import os
from langchain_core.tools import tool

@tool
def edit_file(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """
    # Tool: Edit File
    
    ## Overview
    Edits an existing file by replacing a specific string with a new string. Useful for precise modifications without rewriting the whole file.
    
    ## Input Parameters
    * `file_path` (string): The absolute or relative path to the file you want to edit.
    * `old_string` (string): The exact string you want to find and replace.
    * `new_string` (string): The string to insert in place of `old_string`.
    * `replace_all` (boolean): If true, replaces all occurrences of `old_string`. If false, replaces only the first occurrence. Defaults to false.
    
    ## Expected Output
    * Returns a success message if the edit is successful, or an error message if the file or string is not found.
    """
    try:
        # 1. Strip extraneous whitespace or quotes
        cleaned_path = file_path.strip("'\" ")
        
        # 2. Expand '~' to the user's home directory
        expanded_path = os.path.expanduser(cleaned_path)
        
        # 3. Resolve to a strict absolute path
        absolute_path = os.path.abspath(expanded_path)
        
        # 4. Check if the file actually exists
        if not os.path.exists(absolute_path):
            return f"Error: File does not exist at {absolute_path}"
            
        # 5. Read the current file content
        with open(absolute_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 6. Verify the old string is actually in the file
        if old_string not in content:
            return f"Error: The exact string '{old_string}' was not found in {absolute_path}. No changes were made."
            
        # 7. Perform the replacement
        # string.replace() uses count=-1 for all occurrences, or count=1 for just the first
        count = -1 if replace_all else 1
        new_content = content.replace(old_string, new_string, count)
        
        # 8. Write the updated content back to the file
        with open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        occurrence_text = "all occurrences" if replace_all else "first occurrence"
        return f"Successfully edited {absolute_path} (Replaced {occurrence_text})."
        
    except Exception as e:
        # Provide the resolved path in the error for debugging
        resolved = absolute_path if 'absolute_path' in locals() else cleaned_path
        return f"Error editing file. Attempted path: {resolved}. Exception: {str(e)}"