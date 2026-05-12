import os
import json
from pathlib import Path
from typing import List, Dict, Any


def create_codebase_structure_v2(folder_path, output_json_path="codebase_structure.json"):
    """
    Creates a compact JSON structure of a codebase with file paths.

    Args:
        folder_path (str): Path to the folder to analyze
        output_json_path (str): Path where the JSON file will be saved

    Returns:
        list: Array of all file paths (not directories) in the codebase
    """

    # Default ignore patterns
    default_ignore_patterns = {
        'node_modules', '__pycache__', '.git', '.venv', 'venv',
        'env', '.env', 'dist', 'build', '.pytest_cache', '.mypy_cache',
        '.tox', '.coverage', 'htmlcov', 'pip-log.txt',
        '.DS_Store', 'Thumbs.db', '.idea', '.vscode', 'coverage',
        '.next', '.nuxt', 'out', '.cache', '.parcel-cache'
    }

    default_ignore_extensions = {
        # Python
        '.pyc', '.pyo', '.pyd', '.egg', '.egg-info',
        # Logs & temp
        '.log', '.tmp', '.temp', '.bak', '.old', '.swp', '.swo', '.pid',
        # Compiled binaries
        '.exe', '.dll', '.so', '.dylib', '.o', '.a', '.out', '.class',
        # Java / JVM
        '.jar', '.war', '.ear', '.iml',
    }

    file_paths = []
    structure = {}

    folder = Path(folder_path)
    project_name = folder.name

    for root, dirs, files in os.walk(folder):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if d not in default_ignore_patterns]

        # Get relative path from folder
        rel_root = Path(root).relative_to(folder)

        # Build structure
        current = structure
        if rel_root.parts:
            for part in rel_root.parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        for file in files:
            # Check ignore extensions
            ext = Path(file).suffix.lower()
            if ext in default_ignore_extensions:
                continue

            if file in default_ignore_patterns:
                continue

            rel_path = str(rel_root / file) if rel_root else file
            file_paths.append(rel_path)

            # Add to structure
            current[file] = rel_path

    # Save to JSON
    output_data = {project_name: structure}

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    return file_paths


def analyze_project_complete(
    project_path: str,
    output_json: str = "analyzed_codebase.json",
    model: str = "gpt-4o-mini",
    max_concurrent: int = 10,
    logger_function=None
):
    """
    Complete pipeline: Generate codebase structure

    Args:
        project_path: Path to your project folder
        output_json: Output file name
        model: OpenAI model to use (not used in simplified version)
        max_concurrent: Max parallel API calls (not used)
        logger_function: Logger function

    Returns:
        Statistics from the analysis
    """

    if logger_function:
        logger_function.info("=" * 80)
        logger_function.info("CODEBASE ANALYSIS PIPELINE")
        logger_function.info("=" * 80)
        logger_function.info(f"Project: {project_path}")
        logger_function.info(f"Output: {output_json}")

    # Generate codebase structure
    file_paths = create_codebase_structure_v2(
        folder_path=project_path,
        output_json_path=output_json
    )

    stats = {
        "total_files": len(file_paths),
        "output_file": output_json
    }

    if logger_function:
        logger_function.info(f"Structure created with {len(file_paths)} files")

    return stats


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        folder = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "codebase_structure.json"
        files = create_codebase_structure_v2(folder, output)
        print(f"Created structure with {len(files)} files")
    else:
        print("Usage: python codebase_indexer.py <folder_path> [output_json]")