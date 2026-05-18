import json
import os
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field
from agents.states.CodebaseState import CodebaseState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from rich.console import Console
from rich.panel import Panel

from pprint import pprint

# Assuming these are defined in your project
from models.gemini_models import GEMINI_31_PRO
from models.openai_models import GPT_53_CODEX, GPT_52_CHAT, GPT_5_MINI_TEST
from utils import print_tree



GENERATION_LLM = GEMINI_31_PRO
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
    base_llm = GENERATION_LLM
    llm = base_llm.with_structured_output(CodebaseMap)

    system_prompt = f"""You are an expert software architect. Analyze the provided requirements and generate a production-ready codebase structure.

### GOAL
Generate a structured JSON mapping of the complete codebase based on the user's requirements.

### SKILLS / CONTEXT
{skills_context}

========================
CORE ARCHITECTURAL RULES
========================
- TECH STACK:
  - If the user specifies a stack → strictly follow it
  - If not → choose a modern, scalable, production-grade stack

- DOCKER-FIRST ARCHITECTURE (MANDATORY):
  - EVERY project MUST include:
    - Dockerfile (for each service if multi-service)
    - docker-compose.yml (REQUIRED, even for single-service apps)
  - The application MUST be fully runnable via Docker ONLY
  - Database initialization MUST use an `init.db` file (e.g., an `init.sql` or setup script) that is mounted and executed by `docker-compose.yml` to automatically load schema and seed data on startup.
  - Define:
    - Services (frontend, backend, db, etc.)
    - Networks
    - Volumes (if needed)
    - Environment variables
  - Ensure inter-service communication works via Docker networking
  - No assumptions of local runtime outside Docker

- PRODUCTION COMPLETENESS:
  Include ALL required files for a real-world deployable project:
  - package.json / requirements.txt / pom.xml (depending on stack)
  - .env.example (REQUIRED)
  - .gitignore
  - .dockerignore (REQUIRED to prevent massive build context transfers)
  - README.md (must include Docker run instructions)
  - TESTDOC.md (REQUIRED for QA agent testing instructions)
  - Dockerfile(s)
  - docker-compose.yml
  - init.db (REQUIRED if a database is used, for loading initial data)
  - Config files (tsconfig, eslint, nginx, etc. as needed)

- SCALABILITY & STRUCTURE:
  - Follow clean architecture principles
  - Separate concerns (API, services, config, components, etc.)
  - Design for extensibility and maintainability

- ASSET RESTRICTIONS:
  - ALL UI graphics/images MUST be `.svg`
  - PNG, JPG, GIF are STRICTLY FORBIDDEN

========================
OUTPUT FORMAT RULES
========================
- Return a FLAT JSON dictionary
- Keys = FULL file paths (e.g., "frontend/src/App.tsx")
- Values = metadata object for each file

Each file MUST include:
- "description": Purpose of the file
- "generation_prompt": A HIGHLY DETAILED prompt for a coder agent

========================
GENERATION PROMPT REQUIREMENTS
========================
Each `generation_prompt` MUST:
- Be implementation-ready (no ambiguity)
- Include:
  - Exact responsibilities of the file
  - Key logic/components/classes
  - Expected inputs/outputs
  - Dependencies/imports
  - Integration with other files/services
- Be detailed enough that another agent can generate the file WITHOUT guessing

========================
DOCKER & DATABASE REQUIREMENTS
========================
- .dockerignore MUST:
  - Be generated for the root of the build context.
  - Explicitly exclude heavy, non-essential folders (e.g., `node_modules`, `.git`, `dist`, `build`, `.env`) to optimize daemon transfer sizes.

- Dockerfile(s) MUST:
  - Use optimized base images
  - Follow best practices (layer caching, minimal size, security)
  - Correct working directory and build steps
  - Proper CMD/ENTRYPOINT

- docker-compose.yml MUST:
  - Define all services clearly
  - Include:
    - build context (MUST be strictly scoped, e.g., `context: .` or `context: ./service_name`. NEVER use a parent directory like `..` to prevent massive context uploads)
    - ports
    - environment variables
    - volumes (if needed)
    - depends_on
  - Database Services MUST map the `init.db` file to the container's initialization directory (e.g., `/docker-entrypoint-initdb.d/`) to guarantee automated data loading.
  - Ensure full system runs with:
    docker compose up --build

- README.md MUST:
  - Include exact Docker commands to run the system
  - No local (non-Docker) setup instructions

========================
QA TESTING REQUIREMENTS (TESTDOC.md)
========================
- You MUST generate a `TESTDOC.md` file designed specifically for a QA_AGENT.
- This document must contain comprehensive, step-by-step instructions on how to test the application UI and APIs.
- It MUST explicitly define:
  - Exact dummy data to input into forms or API requests.
  - Specific UI interactions (e.g., "Click the 'Submit' button", "Navigate to '/dashboard'", "Toggle the theme switch").
  - Expected behaviors, visual changes, and assertions the QA_AGENT should verify after each action.
  - Edge cases and error states to trigger and validate.

========================
FINAL CONSTRAINTS
========================
- Do NOT omit Docker under any condition
- Do NOT assume local execution environments
- Do NOT generate incomplete structures
- Do NOT include unused or placeholder files
- Ensure the project is runnable end-to-end via Docker

"""
    user_prompt = f"\n\n### USER REQUIREMENTS\n{requirements}"
    
    print("INFO: Invoking LLM to generate codebase structure...")
    execution_log.append("Invoking LLM to generate codebase structure based on requirements and skills.")
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            AIMessage(content=f"LLM Output History:\n{chr(10).join(history)}"),
            HumanMessage(content=user_prompt),
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