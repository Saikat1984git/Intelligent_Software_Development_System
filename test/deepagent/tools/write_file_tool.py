from pathlib import Path
from langchain_core.tools import tool

@tool
def write_file_tool(file_path: str, content: str) -> str:
    """
    Creates a file at the specified file_path and writes the provided content to it.
    Automatically creates any necessary parent directories.
    
    Args:
        file_path: The relative or absolute path where the file should be created (e.g., 'src/main/index.py').
        content: The string content to write into the file.
        
    Returns:
        A success message or an error message.
    """
    try:
        # Convert string to Path object for easier manipulation
        path = Path(file_path)
        
        # Ensure the parent directories exist (creates them if they don't)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content to the file safely
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"Success: File successfully created and written to '{file_path}'."
    
    except Exception as e:
        return f"Error: Failed to write to '{file_path}'. Details: {str(e)}"

# --- Example Usage ---
# If you want to test the tool manually before giving it to an agent:
# result = write_file_tool.invoke({
#     "file_path": "src/main/index.py", 
#     "content": "print('hello world')"
# })
# print(result)