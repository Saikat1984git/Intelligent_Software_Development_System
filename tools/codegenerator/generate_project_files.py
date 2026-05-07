import json
import os
import asyncio
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

# Assuming these imports match your project
from agents.states.CodebaseState import CodebaseState
from models.openai_models import GPT_51_CODEX_MINI, GPT_53_CODEX
from utils.extract_text_from_response import extract_text_from_response

load_dotenv()
console = Console()



CODE_GENERATION_MODEL = GPT_53_CODEX

def print_code_panel(file_path: str, content: str):
    """Helper to print code via rich (mock implementation)."""
    syntax = Syntax(content, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=file_path))

def get_dependent_files_contents(dependent_paths: List[str]) -> str:
    """
    Reads the contents of the generated dependent files from the disk.
    Returns a formatted string to be injected into the LLM prompt.
    """
    if not dependent_paths:
        return "No local dependent files."
    print(f"INFO: Reading contents of {" ,".join(dependent_paths)} dependent files for prompt context...")

    contents = []
    for path in dependent_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                contents.append(f"--- FILE: {path} ---\n{file_content}")
            except Exception as e:
                contents.append(f"--- FILE: {path} ---\n[Error reading file: {e}]")
        else:
            contents.append(f"--- FILE: {path} ---\n[Warning: File not found on disk. It may not have been generated correctly.]")
            
    return "\n\n".join(contents)

async def _generate_and_save_file(
    file_path: str,
    file_metadata: Dict[str, Any],
    requirements: str,
    skills_context: str,
    codebase_structure_str: str,
    dependent_contents_str: str,
    llm: Any,
    semaphore: asyncio.Semaphore,
) -> bool:
    """Helper function to asynchronously generate and save a single file."""
    async with semaphore:
        print(f"INFO: Generating file: {file_path}...")
        
        # Extract the highly specific generation prompt generated in the previous step
        specific_generation_prompt = file_metadata.get("generation_promt", "Follow best practices for this file type.")

        prompt = prompt = f"""You are an expert, principal-level software engineer. Generate production-ready code for a specific file in a project.

            <context>
            PROJECT REQUIREMENTS:
            {requirements}

            SKILLS / GUIDELINES:
            {skills_context}

            COMPLETE CODEBASE STRUCTURE:
            {codebase_structure_str}

            TARGET FILE PATH:
            {file_path}
            
            FILE-SPECIFIC GENERATION INSTRUCTIONS:
            {specific_generation_prompt}
            </context>
            
            <dependent_files_context>
            The following are the exact contents of the local files that THIS file depends on. 
            Analyze them carefully to ensure perfect compatibility, correct imports, and matching function signatures:
            
            {dependent_contents_str}
            </dependent_files_context>

            <instructions>
            1. ANALYZE the complete project structure to understand:
              - The overall architecture and framework being used
              - How this file fits into the larger project
              - What other files this file needs to import or reference
              - What naming conventions and patterns are used

            2. CONSIDER the file's location and purpose:
              - Is it a configuration file? Use proper format (JSON, YAML, ENV, etc.)
              - Is it a source code file? Use appropriate imports from other files
              - Is it a documentation file? Be comprehensive and accurate
              - Is it a script file? Include proper shebang and executable logic

            3. GENERATE complete, production-ready code that:
              - Follows best practices for the detected language/framework
              - Includes proper imports referencing actual files in the project structure
              - Has comprehensive error handling and logging
              - Contains inline comments explaining key logic
              - Is syntactically correct and immediately usable
              - Maintains consistency with the overall project architecture

            4. SPECIAL CASES (CRITICAL):
              - For package.json: Include all necessary dependencies with latest versions
              - For README.md: Include project overview, setup, and strictly Docker-based usage instructions
              - For run.sh: Include environment setup, dependency installation, and run commands
              - For config files: Use values that match the project requirements
              - For test files: Create realistic test cases
              - For Dockerfile(s): Use multi-stage builds, minimal base images (e.g., alpine), and optimize layer caching.
              - For docker-compose.yml: STRICTLY restrict the build `context` to the specific service directory (e.g., `.` or `./frontend`). NEVER use parent directories (e.g., `..`) to prevent massive daemon transfers.
              - For .dockerignore: Explicitly exclude heavy/temporary directories (`node_modules`, `.git`, `dist`, `build`, `.env`, etc.) to guarantee fast build context uploads.

            5. IMPORTANT RULES:
              - Reference other files in the structure when appropriate (e.g., imports)
              - Use consistent naming patterns across the project
              - Ensure all paths and imports align with the codebase structure
              - Make the code cohesive with the rest of the project
              - ALL UI graphics/images MUST be implemented as inline or referenced `.svg` files. Do not use or reference PNG, JPG, or GIF formats.
            </instructions>

            <output_format>
            Return ONLY the raw code/content for the file.
            NO markdown code blocks (no ```)
            NO explanations or commentary.
            NO extra text.
            Just the exact content that should be written to {file_path}.
            </output_format>

            Generate the file content now:"""

        try:
                # Using ainvoke for asynchronous generation
                response = await llm.ainvoke(prompt)
                content = extract_text_from_response(response).strip()

                # Clean up markdown formatting if the model still outputs it
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip().startswith("```"):
                        lines = lines[:-1]
                    content = "\n".join(lines)

                print_code_panel(file_path, content)

                # --- THE FIX ---
                # Extract the directory path
                dir_name = os.path.dirname(file_path)
                
                # Only attempt to create directories if the file isn't at the root level
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                # ---------------

                # Write the generated code to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"SUCCESS: Saved {file_path}")
                return True

        except Exception as e:
                print(f"ERROR: Failed to generate {file_path}: {str(e)}")
                return False

def _build_dependency_levels(files_dict: Dict[str, Any]) -> List[List[str]]:
    """
    Sorts files into execution levels based on their dependencies.
    Level 0 runs first, Level 1 depends on Level 0, etc.
    """
    levels = []
    resolved = set()
    pending = set(files_dict.keys())

    while pending:
        current_level = []
        for file_path in list(pending):
            deps = files_dict[file_path].get("dependent_files", [])
            
            # A file is ready if all its dependencies are already generated (resolved)
            # OR if a dependency doesn't actually exist in our file list (e.g., it's an external library)
            is_ready = all(dep in resolved or dep not in files_dict for dep in deps)
            
            if is_ready:
                current_level.append(file_path)

        if not current_level:
            # Circular dependency safeguard: If we have pending files but NONE are ready, 
            # force the remaining files into the final level to prevent an infinite loop.
            print(f"WARNING: Circular dependency detected among remaining files: {pending}")
            current_level = list(pending)

        levels.append(current_level)
        resolved.update(current_level)
        pending.difference_update(current_level)

    return levels



async def generate_project_files_node(state: CodebaseState) -> Dict[str, Any]:
    """
    LangGraph Node: Asynchronously generates the code for each file using 
    the project structure defined in the state, ordered by dependency levels.
    """
    print("INFO: STARTING: Generate Project Files Node")

    # 1. Extract inputs from State
    requirements = state.get("requirements", "")
    skills_dict = state.get("skills_text", {})
    history = state.get("execution_log", [])
    execution_log = [f"\nStarting file generation based on project structure and requirements.\n"] 

    skills_context = "No specific skills or guidelines provided. Rely on default best practices."
    
    # 2. Resolve skills context
    if skills_dict:
        formatted_skills = [f"--- SKILL FILE: {filepath} ---\n{content}" for filepath, content in skills_dict.items()]
        skills_context = "\n\n".join(formatted_skills)

    # 3. Retrieve the structure directly from the state
    codebase_json = state.get("project_structure")
    # project_name = codebase_json.get("project_name", "generated_project") if codebase_json else "generated_project"
    
    # Fallback to reading from disk if state is somehow missing it
    if not codebase_json:
        metadata_file = state.get("metadata_file", "project_metadata.json")
        if not os.path.exists(metadata_file):
            return {"status": "error", "error": f"Codebase structure missing from state and disk."}
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                codebase_json = json.load(f)
        except Exception as e:
            return {"status": "error", "error": f"Failed to load fallback JSON: {e}"}

    # Extract the files dictionary based on our new structured format
    files_dict = codebase_json.get("files", {})
    if not files_dict:
        return {"status": "error", "error": "No file configurations found in project structure."}

    # 4. Determine execution levels
    execution_levels = _build_dependency_levels(files_dict)
    total_files = len(files_dict)
    
    print(f"INFO: Collected {total_files} files to generate across {len(execution_levels)} dependency levels.")
    execution_log.append(f"Collected {total_files} files spread across {len(execution_levels)} execution levels.")
    
    codebase_structure_str = json.dumps(codebase_json, indent=2)

    # 5. Concurrency setup
    max_concurrent_calls = 7
    semaphore = asyncio.Semaphore(max_concurrent_calls)
    llm = CODE_GENERATION_MODEL # Or GEMINI_31_PRO if preferred

    successful_files = []

    # 6. Execute generation level by level (WITH EXPLICIT BATCHING)
    for i, level_files in enumerate(execution_levels):
        print(f"\n>>> STARTING LEVEL {i} ({len(level_files)} files) <<<")
        execution_log.append(f"Executing Level {i} with files: {level_files}")

        # Break the level's files into chunks of `max_concurrent_calls`
        for chunk_start in range(0, len(level_files), max_concurrent_calls):
            chunk_files = level_files[chunk_start : chunk_start + max_concurrent_calls]
            
            print(f"    --- Processing Batch: {len(chunk_files)} files (Indices {chunk_start} to {chunk_start + len(chunk_files) - 1}) ---")
            
            tasks = []
            for path in chunk_files:
                file_metadata = files_dict[path]
                dependent_paths = file_metadata.get("dependent_files", [])
                
                # Read the real contents of dependencies to pass into the prompt
                dependent_contents_str = get_dependent_files_contents(dependent_paths)

                tasks.append(
                    _generate_and_save_file(
                        file_path=path,  # Prepend project name to the path inside this function
                        file_metadata=file_metadata,
                        requirements=requirements,
                        skills_context=skills_context,
                        codebase_structure_str=codebase_structure_str,
                        dependent_contents_str=dependent_contents_str,
                        llm=llm,
                        semaphore=semaphore
                    )
                )

            # Run all files in the current CHUNK concurrently and wait for them to finish
            results = await asyncio.gather(*tasks)
            
            # Track successes for this specific chunk
            chunk_successes = [path for path, success in zip(chunk_files, results) if success]
            successful_files.extend(chunk_successes)

    execution_log.append(f"File generation completed. Successfully generated {len(successful_files)}/{total_files} files.")

    # 7. Return the updates to the LangGraph state
    return {
        "status": "success",
        "generated_files": successful_files,
        "execution_log": history + execution_log
    }

    