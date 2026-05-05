import json
import os
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field
from agents.states.CodebaseState import CodebaseState
from langchain_core.messages import HumanMessage, AIMessage

from rich.console import Console
from rich.panel import Panel

from pprint import pprint

# Assuming these are defined in your project
from models.gemini_models import GEMINI_31_PRO
from utils import print_tree

console = Console()

# -------------------------------------------------------------------
# 1. NEW PYDANTIC MODELS FOR STRUCTURED OUTPUT
# -------------------------------------------------------------------

class FunctionMetadata(BaseModel):
    name: str = Field(description="Name of the function.")
    description: str = Field(description="What the function does.")
    parameters: List[str] = Field(description="List of parameter names/types.")
    returns: str = Field(description="Return type of the function.")

class FileMetadata(BaseModel):
    description: str = Field(
        description="A summary of the file's purpose and logic."
    )
    generation_promt: str = Field(
        description="A highly detailed system prompt that an LLM can use later to write the actual code for this file."
    )
    file_type: str = Field(
        description="The file extension (e.g., js, ts, py, java, sh, json, yml, md, env)"
    )
    dependencies: List[str] = Field(
        description="List of external libraries or internal modules required (e.g., ['react', 'express', 'langchain'])."
    )
    exports: List[str] = Field(
        description="List of public symbols, classes, or functions exported from this file."
    )
    public_functions: List[FunctionMetadata] = Field(
        default_factory=list,
        description="Details about the public functions in this file."
    )
    dependent_files: List[str] = Field(
        default_factory=list,
        description="List of other file paths in this codebase that THIS file relies on."
    )

class CodebaseMap(BaseModel):
    project_name: str
    files: Dict[str, FileMetadata] = Field(
        description="A dictionary where the key is the full file path (e.g., 'src/main.py') and the value is the file's metadata."
    )

# -------------------------------------------------------------------
# 2. REFACTORED LANGGRAPH NODE
# -------------------------------------------------------------------

def generate_codebase_structure_node(state: CodebaseState) -> Dict[str, Any]:
    """
    LangGraph Node: Generates an initial codebase structure using an LLM.
    Reads requirements and skills from the state, and returns state updates.
    """
    print("INFO: STARTING: Generate Codebase Structure Node")

    # 1. Extract inputs from State
    requirements = state.get("requirements", "")
    skills_dict = state.get("skills_text", {})
    history = state.get("execution_log", [])

    execution_log = []
    execution_log.append("STARTING: Generate Codebase Structure agent Node")

    skills_context = "No specific skills or guidelines provided. Rely on default best practices."
    
    # 2. Resolve skills context
    if skills_dict:
        formatted_skills = [
            f"--- SKILL FILE: {filepath} ---\n{content}" 
            for filepath, content in skills_dict.items()
        ]
        skills_context = "\n\n".join(formatted_skills)

    print(f"DEBUG: Resolved skills context for LLM:\n{skills_context[:1000]}...")
    execution_log.append("Resolved skills context for LLM input.")

    # 3. Setup LLM with Structured Output
    base_llm = GEMINI_31_PRO
    llm = base_llm.with_structured_output(CodebaseMap)

    system_prompt = f"""You are an expert software architect. Analyze the provided requirements and generate a production-ready codebase structure.

### GOAL
Generate a structured JSON mapping of the complete codebase based on the user's requirements.

### SKILLS / CONTEXT
{skills_context}

### ARCHITECTURAL & CONTENT RULES
- TECH STACK: If the user specifies a tech stack, strictly follow it. If none is specified, select the best modern, scalable, industry-grade stack.
- COMPLETENESS: Include all necessary files for a real production project (e.g., package.json, .env.example, .gitignore, README.md, Dockerfile, docker-compose.yml).
- ASSET RESTRICTIONS: All UI graphics/images MUST be `.svg` files. PNG, JPG, and GIF are STRICTLY FORBIDDEN.
- DICTIONARY FORMAT: Ensure the output is a flat dictionary where keys are the full file paths (e.g., "frontend/src/App.tsx") and values contain the required metadata.
- GENERATION PROMPT: Provide a highly detailed `generation_promt` for each file. This prompt will be passed to a coder agent later to actually write the file's contents.
"""
    
    user_prompt = f"\n\n### USER REQUIREMENTS\n{requirements}"
    
    print("INFO: Invoking LLM to generate codebase structure...")
    execution_log.append("Invoking LLM to generate codebase structure based on requirements and skills.")
    
    try:
        messages = [
            AIMessage(content=f"LLM Output History:\n{chr(10).join(history)}"),
            HumanMessage(content=system_prompt + user_prompt),
        ]
        
        # The LLM will natively return the Pydantic CodebaseMap object
        response: CodebaseMap = llm.invoke(messages)
        
        # Convert the Pydantic object back to a standard Python dictionary for saving/logging
        codebase_dict = response.model_dump()

        print("INFO: Codebase structure successfully generated by LLM.")
        print(json.dumps(codebase_dict, indent=4))  # For debugging purposes, can be removed in production

        console.print(
            Panel.fit(
                print_tree(codebase_dict), 
                title="LLM Generated File Mapping",
                border_style="green"
            )
        )

        output_filename = 'project_metadata.json'
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(codebase_dict, f, indent=4)
        
        print(f"INFO: Codebase structure successfully saved to {output_filename}")
        execution_log.append(f"Codebase structure successfully generated and saved to {output_filename}.")
        
        # Extract file paths directly from the dictionary keys
        file_paths = list(codebase_dict["files"].keys())

        print(f"INFO: CODEBASE_GENERATED - total_files_identified: {len(file_paths)}")
        execution_log.append(f"Codebase generation complete. Total files identified: {len(file_paths)}.")

        return {
            "status": "success",
            "metadata_file": output_filename,
            "file_paths": file_paths,
            "project_structure": codebase_dict,
            "execution_log": history + execution_log
        }

    except Exception as e:
        error_msg = f"GENERATE_CODEBASE_ERROR: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {"status": "error", "error": error_msg}