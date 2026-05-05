import os
import json
from typing import Dict, Any

from rich.console import Console

# Assuming these are imported from your existing modules
from agents.states.CodebaseState import CodebaseState
from utils.extract_text_from_response import extract_text_from_response
from models.gemini_models import GEMINI_3_FLASH

console = Console()

def load_skills_node(state: CodebaseState) -> Dict[str, Any]:
    """
    LangGraph Node: Scans a skill directory, selects relevant 
    files using an LLM based on requirements, and loads their contents 
    into the 'skills_text' state variable as a dictionary mapping 
    file paths to file contents.
    """
    print("INFO: STARTING: Load Skills agent node")

    requirements = state.get("requirements", "")
    skills_path = state.get("skills")  # This is a single string path
    execution_log = state.get("execution_log", [])
    execution_log.append(" STARTING: Load Skills agent node")

    print(f"DEBUG: Received requirements: {requirements}")
    print(f"DEBUG: Received skills path: {skills_path}")
    print(f"DEBUG: Skill folder path: {skills_path}")

    # 1. Handle empty or missing skills input
    if not skills_path or not isinstance(skills_path, str) or not os.path.isdir(skills_path):
        print("INFO: No valid skills folder provided. Proceeding with empty skills text.")
        execution_log.append("No valid skills folder provided. Skipping skill loading.")
        return {"skills_text": {}}

    # 2. Gather all available files using os.walk to handle nested directories
    available_files = {}  # Map 'folder_name/file_name' to its absolute path
    
    # Filter out binaries so we don't crash on read or waste LLM context
    excluded_extensions = ('.jar', '.class', '.pyc', '.exe', '.zip', '.tar', '.gz', '.png', '.jpg')

    for root, _, files in os.walk(skills_path):
        for filename in files:
            if not filename.endswith(excluded_extensions):
                full_path = os.path.join(root, filename)
                
                # Create a clean relative key like 'struts-1-development/SKILL.md'
                # replace('\\', '/') ensures consistent formatting across Windows/Linux
                display_name = os.path.relpath(full_path, skills_path).replace('\\', '/')
                available_files[display_name] = full_path

    print(f"INFO: Found {len(available_files)} skill files across the provided folder.")
    execution_log.append(f"Found {len(available_files)} skill files in the provided folder.")
    
    if not available_files:
        print("INFO: No files found in the provided skills folder.")
        return {"skills_text": {}}

    # 3. Prompt the LLM to pick the right files
    llm = GEMINI_3_FLASH
    file_list_json = json.dumps(list(available_files.keys()), indent=2)
    
    prompt = f"""You are an expert technical lead setting up a project workspace.
Read the project requirements and select the most relevant skill/guideline files from the available list.

### PROJECT REQUIREMENTS
{requirements}

### AVAILABLE SKILL FILES
{file_list_json}

### INSTRUCTIONS
1. Analyze the requirements to determine the tech stack, architecture, and necessary practices.
2. Select ONLY the file paths from the "AVAILABLE SKILL FILES" list that are highly relevant to building this project.
3. Return your selection strictly as a JSON list of strings.
4. DO NOT include markdown blocks (no ```json), explanations, or any other text. Return ONLY the raw JSON array.
5. Always use docker-essentials skill as default.

Example output:
["struts-1-development/SKILL.md", "windows-powershell-skill/SKILL.md"]
"""

    print("INFO: Invoking LLM to dynamically select relevant skill files...")
    execution_log.append("Invoking LLM to select relevant skill files based on requirements.")
    
    try:
        response = llm.invoke(prompt)
        raw_text = extract_text_from_response(response).strip()

        # Clean JSON if the model added markdown blocks anyway
        if raw_text.startswith("```"):
            start_idx = raw_text.find("[")
            end_idx = raw_text.rfind("]")
            if start_idx != -1 and end_idx != -1:
                raw_text = raw_text[start_idx:end_idx+1]

        selected_keys = json.loads(raw_text)
        print(f"INFO: LLM selected the following skill files: {selected_keys}")
        execution_log.append(f"LLM selected {len(selected_keys)} skill files: {selected_keys}")

        # 4. Read the contents of the selected files into a dictionary
        skills_text_dict: Dict[str, str] = {}
        for key in selected_keys:
            if key in available_files:
                filepath = available_files[key]
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # Store the raw content; the key already identifies the file
                        skills_text_dict[key] = f.read()
                except Exception as e:
                    print(f"WARNING: Could not read selected file {filepath}: {e}")
            else:
                print(f"WARNING: LLM hallucinated or altered file path: {key}")

        if not skills_text_dict:
             print("INFO: No valid skills could be loaded from the selection.")

        print(f"INFO: Successfully loaded {len(skills_text_dict)} dynamic skills files.")
        execution_log.append(f"Successfully loaded {len(skills_text_dict)} skill files into state.")
        
        # Return the dictionary to update the state
        return {
            "skills_text": skills_text_dict,
            "status": "skills_loaded",
            "execution_log": execution_log
        }

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM skill selection: {e}. Raw: {raw_text}"
        print(f"ERROR: {error_msg}")
        return {"error": error_msg, "skills_text": {}}
        
    except Exception as e:
        error_msg = f"Error in load_skills_node: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {"error": error_msg, "skills_text": {}}