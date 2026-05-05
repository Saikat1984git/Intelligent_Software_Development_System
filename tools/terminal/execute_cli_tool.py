import os
import subprocess
from langchain_core.tools import tool


@tool
def execute_cli(command: str) -> str:
    """
    # Tool: Execute CLI Command
    
    ## Overview
    Executes a shell command on the host system and returns the output (stdout and stderr).
    Crucial for checking Docker logs (e.g., `docker logs container_name`), running `ls` to find files, or executing test scripts.
    
    ## Input Parameters
    * `command` (string): The standard shell command to execute.
    
    ## Expected Output
    * Returns the exit code along with standard output and standard error.
    
    ## Limitations
    * Commands have a strict 30-second timeout. Do NOT run interactive commands or start servers that run indefinitely in the foreground (like `npm start` or `python main.py` without daemonizing).
    """
    try:
        # shell=True allows for piping and environment variable expansion
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        output = f"Exit Code: {result.returncode}\n"
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
            
        return output
    except subprocess.TimeoutExpired:
        return f"Error: Command '{command}' timed out after 30 seconds. Ensure you are not running blocking commands."
    except Exception as e:
        return f"Error executing command '{command}': {str(e)}"