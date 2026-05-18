import os
import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

# Assuming your composite tool and models are imported here
from models.openai_models import GPT_51_CODEX_MINI

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("CodebaseAnalyzer")

# =====================================================================
# Configuration
# =====================================================================
# How many files the LLM will process simultaneously in one batch
PARALLEL_THREAD_COUNT = 10

# Global semaphore to enforce the concurrent batch limit
semaphore = asyncio.Semaphore(PARALLEL_THREAD_COUNT)

# =====================================================================
# 1. Structured Output Schemas (Pydantic)
# =====================================================================

class PublicFunction(BaseModel):
    name: str = Field(description="The name of the function.")
    description: str = Field(description="A brief description of what the function does.")
    parameters: List[str] = Field(description="List of parameter names the function accepts.")
    returns: str = Field(description="The return type of the function.")

class FileMetadata(BaseModel):
    description: str = Field(description="A brief description of the file's purpose.")
    generation_promt: str = Field(description="A detailed prompt that could be used to regenerate this file.")
    file_type: str = Field(description="The file extension or type (e.g., 'json', 'ts', 'js', 'yml', 'Dockerfile').")
    dependencies: List[str] = Field(description="List of external libraries, packages, or frameworks used.")
    exports: List[str] = Field(description="List of modules, classes, or components exported by this file.")
    public_functions: List[PublicFunction] = Field(description="List of public functions or methods defined in this file.")
    dependent_files: List[str] = Field(description="List of other internal project files that this file depends on.")

# =====================================================================
# 2. Async Workers
# =====================================================================

async def _analyze_single_file(file_path: Path, relative_path: str) -> tuple[str, Optional[Dict[str, Any]]]:
    """Reads an individual file and invokes the structured LLM chain asynchronously."""
    
    # The semaphore ensures only PARALLEL_THREAD_COUNT files enter this block at once
    async with semaphore:
        logger.info(f"Starting analysis for file: {relative_path}")
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Skipping binary/unreadable file: {relative_path} (Reason: {e})")
            return relative_path, None

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert software architect analyzing a codebase. Extract the structural "
                "metadata for the provided file according to the required schema. Ensure the "
                "'generation_promt' is highly detailed so a coding agent could recreate the file perfectly."
            )),
            ("human", "File Path: {filepath}\n\nFile Content:\n{content}\n\nAnalyze this file and extract its metadata.")
        ])

        # Bind schema to structural engine
        llm_with_structure = GPT_51_CODEX_MINI.with_structured_output(FileMetadata)
        chain = prompt | llm_with_structure

        try:
            # API invocation call
            result: FileMetadata = await chain.ainvoke({
                "filepath": relative_path, 
                "content": content
            })
            logger.info(f"✓ Completed analysis for: {relative_path}")
            return relative_path, result.model_dump()
        except Exception as e:
            logger.error(f"✗ Error analyzing {relative_path}: {str(e)}")
            return relative_path, None

# =====================================================================
# 3. Main Logic Execution Entry Point
# =====================================================================

def analyze_codebase_agent(codebase_path: str) -> str:
    """
    Analyzes the complete codebase and creates a project metadata summary using GPT_51_CODEX_MINI.
    The resulting JSON is saved directly into the root directory of the codebase.
    """
    base_path = Path(codebase_path).resolve()
    if not base_path.exists():
        raise FileNotFoundError(f"Provided path does not exist: {base_path}")
        
    project_name = base_path.name
    
    # Output file strictly targets the root of the provided codebase directory
    output_file_path = base_path / "project_metadata.json"
    
    ignore_dirs = {'.git', 'node_modules', '__pycache__', 'dist', 'build', '.angular', '.idea', '.vscode', '.next'}
    ignore_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.woff', '.woff2', '.ttf', '.eot', '.mp4')

    async def _run_analysis():
        tasks = []
        logger.info(f"Scanning target codebase directory: {base_path}")
        
        for root, dirs, files in os.walk(base_path):
            # Prune directories to ignore out-of-scope trees
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                # Ensure we do not analyze the output file itself
                if file == "project_metadata.json" or file.endswith(ignore_extensions):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(base_path).as_posix()
                
                # Append async task (will be throttled by semaphore internally)
                tasks.append(_analyze_single_file(file_path, relative_path))
        
        total_files = len(tasks)
        if total_files == 0:
            logger.warning("No eligible text files found for scanning.")
            return {"project_name": project_name, "files": {}}
            
        logger.info(f"Gathered {total_files} files. Commencing batched parallel analysis ({PARALLEL_THREAD_COUNT} at a time)...")
        results = await asyncio.gather(*tasks)
        
        files_metadata = {}
        for rel_path, meta_dict in results:
            if meta_dict is not None:
                files_metadata[rel_path] = meta_dict
                
        return {
            "project_name": project_name,
            "files": files_metadata
        }

    # Block on the worker loop
    project_metadata = asyncio.run(_run_analysis())
    
    logger.info(f"Compiling final metadata file structure for writing to root directory...")
    
    # Write directly to the base_path
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(project_metadata, f, indent=4)

    analysis_result = (
        f"Analyzed codebase at {base_path} with GPT_51_CODEX_MINI. "
        f"Successfully processed {len(project_metadata['files'])} files. "
        f"Metadata written to {output_file_path}"
    )
    logger.info(f"Execution complete. Output destination: {output_file_path}")
    return analysis_result

# =====================================================================
# 4. Testing Block
# =====================================================================
if __name__ == "__main__":
    logger.info("Initializing runtime simulation pipeline for local verification...")
    
    # To test on your actual codebase, change this path to: 
    test_target_dir = r"D:\Development\new_vibe_code\generated\latest_2026-05-08_20-24-30"
    # test_target_dir = Path("D:/Development/new_vibe_code\generated\latest_2026-05-08_20-24-30")
    

    
    try:
        # Note: Requires valid API connection keys in your environment.
        summary_log = analyze_codebase_agent(str(test_target_dir))
        print("\n" + "="*60 + "\nFINAL OUTPUT LOG SUMMARY:\n" + summary_log + "\n" + "="*60)
    except Exception as error:
        logger.exception(f"Pipeline crashed during execution analysis trace: {error}")
