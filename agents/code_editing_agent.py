import os
import json
import sys
import base64
from typing import List, Dict, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

# Import our tools
from tools.codebase_indexer import create_codebase_structure_v2, analyze_project_complete
from tools.file_editor import apply_file_edits


# Pydantic models for structured output
class FileContent(BaseModel):
    file_path: str = Field(description="The relative file path")
    content: str = Field(description="The rewritten code content")

class RewrittenFiles(BaseModel):
    files: List[FileContent] = Field(description="List of files with rewritten content")


def choose_edit_filepaths(json_filepath: str, edit_prompt: str, max_paths: int = 8) -> List[str]:
    """
    Simple file path selector based on the project structure JSON.
    """
    json_path = Path(json_filepath)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_filepath}")

    with json_path.open("r", encoding="utf-8") as f:
        project_struct = json.load(f)

    # Extract all file paths from structure
    all_files = []

    def extract_files(data, prefix=""):
        if isinstance(data, dict):
            for key, value in data.items():
                path = f"{prefix}/{key}" if prefix else key
                if isinstance(value, dict):
                    # It's a directory
                    extract_files(value, path)
                else:
                    # It's a file - the value is the full path
                    all_files.append(value if isinstance(value, str) else path)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    all_files.append(item)

    extract_files(project_struct)

    # Simple heuristic: find files that match keywords in the prompt
    keywords = edit_prompt.lower().split()
    scored_files = []

    for f in all_files:
        filename = os.path.basename(f).lower()
        score = 0
        for kw in keywords:
            if kw in filename:
                score += 10
            if kw in f.lower():
                score += 5
        scored_files.append((score, f))

    # Sort by score and return top matches
    scored_files.sort(key=lambda x: -x[0])
    return [f[1] for f in scored_files[:max_paths]]


def read_file_contents(file_paths: List[str], root_path: str) -> Dict[str, str]:
    """Read content from all specified files."""
    file_contents = {}
    for rel_path in file_paths:
        full_path = Path(root_path) / rel_path
        if not full_path.exists():
            print(f"File not found: {full_path}, will be created")
            file_contents[rel_path] = ""
            continue
        with open(full_path, "r", encoding="utf-8") as f:
            file_contents[rel_path] = f.read()
    return file_contents


def rewrite_with_gpt(
    file_paths: List[str],
    root_path: str,
    project_content: str,
    prompt: str,
    model_name: str = "gpt-4o"
) -> Dict[str, str]:
    """Rewrite code using GPT models."""
    from models.openai_models import GPT_53_CODEX, GPT_4O_MINI

    # Use the best available model
    llm = GPT_53_CODEX.with_structured_output(RewrittenFiles)

    # Read file contents
    file_contents = read_file_contents(file_paths, root_path)

    files_json = json.dumps(
        [{"file_path": p, "content": c} for p, c in file_contents.items()],
        indent=2
    )

    system_prompt = (
        "You are an expert code refactoring assistant.\n"
        "You will receive a JSON structure containing multiple code files and a rewriting instruction.\n"
        "Your task:\n"
        "1. Analyze each file's code.\n"
        "2. Apply the requested changes according to the prompt.\n"
        "3. Return the rewritten code for each provided file.\n"
        "4. Identify and generate any new files that are necessary to fully implement the changes.\n"
        "5. Ensure that the rewritten code is functional, maintainable, and adheres to best practices.\n"
        "Maintain code quality, follow best practices, and preserve functionality unless instructed otherwise."
    )

    user_prompt = (
        "Here is the current codebase structure in JSON format:\n\n"
        f"{project_content}\n\n"
        "Here are the files to rewrite:\n\n"
        f"{files_json}\n\n"
        "Rewriting instructions:\n"
        f"{prompt}\n\n"
        "Please rewrite the code for each file according to the instructions above."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    print("Invoking GPT model for code rewriting...")
    response = llm.invoke(messages)

    if not response or not response.files:
        return {}

    return {f.file_path: f.content for f in response.files}


def code_editing_agent(
    edit_prompt: str,
    project_folder_path: str,
    images: list = None,
    logger=None
) -> str:
    """
    Code editing pipeline that uses GPT for rewriting.

    Args:
        edit_prompt: Description of the desired changes
        project_folder_path: Absolute path to the project directory
        images: Optional list of image dicts (not currently used with GPT)
        logger: Optional logger function

    Returns:
        Status message about the operation
    """
    images = images or []

    def log(msg):
        print(msg)
        if logger:
            logger(msg)

    log("=" * 60)
    log("STARTING CODE EDITING PIPELINE")
    log("=" * 60)
    log(f"Project: {project_folder_path}")
    log(f"Prompt: {edit_prompt}")
    if images:
        log(f"Images: {len(images)} file(s)")
    log("=" * 60)

    # Validate project path
    if not os.path.exists(project_folder_path):
        return f"ERROR: Project path does not exist: {project_folder_path}"

    # STEP 1: Analyze project structure
    log("\n[Step 1] Analyzing project structure...")

    class SimpleLogger:
        def __init__(self, func):
            self.func = func
        def info(self, msg, *args):
            self.func(msg % args if args else msg)

    try:
        stats = analyze_project_complete(
            project_path=project_folder_path,
            output_json=os.path.join(project_folder_path, "project_structure.json"),
            logger_function=SimpleLogger(log)
        )
        log(f"Analyzed {stats['total_files']} files")
    except Exception as e:
        log(f"ERROR in analysis: {e}")
        return f"ERROR: Failed to analyze project: {e}"

    json_file = os.path.join(project_folder_path, "project_structure.json")

    # STEP 2: Choose files to edit
    log("\n[Step 2] Selecting files to edit...")
    try:
        filepaths = choose_edit_filepaths(json_file, edit_prompt)
        if not filepaths:
            log("WARNING: No files selected, but continuing...")
            filepaths = []
        log(f"Selected {len(filepaths)} files: {filepaths}")
    except Exception as e:
        log(f"ERROR in file selection: {e}")
        return f"ERROR: Failed to select files: {e}"

    if not filepaths:
        return "WARNING: No files matched the edit request. No changes made."

    # STEP 3: Read file contents and rewrite with GPT
    log("\n[Step 3] Rewriting code with GPT...")

    try:
        # Read project structure for context
        with open(json_file, 'r') as f:
            project_content = f.read()

        rewritten = rewrite_with_gpt(
            file_paths=filepaths,
            root_path=project_folder_path,
            project_content=project_content,
            prompt=edit_prompt
        )
        log(f"Rewritten {len(rewritten)} files")

    except Exception as e:
        log(f"ERROR in code rewriting: {e}")
        import traceback
        log(traceback.format_exc())
        return f"ERROR: Failed to rewrite code: {e}"

    if not rewritten:
        log("WARNING: No content returned from rewrite tool")
        return "WARNING: No content returned from rewrite tool"

    # STEP 4: Apply file edits
    log("\n[Step 4] Applying file edits...")

    try:
        summary = apply_file_edits(
            project_root=project_folder_path,
            file_map=rewritten,
            dry_run=False,
            backup_existing=True,
        )
        log(f"File edits applied: created={summary.get('created', 0)}, updated={summary.get('updated', 0)}, failed={summary.get('failed', 0)}")
    except Exception as e:
        log(f"ERROR applying file edits: {e}")
        import traceback
        log(traceback.format_exc())
        return f"ERROR: Failed to apply edits: {e}"

    # Build success message
    success_parts = []
    if summary.get('created', 0) > 0:
        success_parts.append(f"Created {summary['created']} file(s)")
    if summary.get('updated', 0) > 0:
        success_parts.append(f"Updated {summary['updated']} file(s)")
    if summary.get('failed', 0) > 0:
        success_parts.append(f"Failed {summary['failed']} file(s)")

    result_msg = " | ".join(success_parts) if success_parts else "No changes made"
    log("\n" + "=" * 60)
    log(f"COMPLETE: {result_msg}")
    log("=" * 60)

    return f"Success. {result_msg}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python code_editing_agent.py <project_path> <prompt>")
        sys.exit(1)

    project_path = sys.argv[1]
    prompt = sys.argv[2]

    result = code_editing_agent(
        edit_prompt=prompt,
        project_folder_path=project_path
    )
    print("\nRESULT:", result)