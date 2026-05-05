import os
from typing import Dict, Any

def print_tree(data: Dict[str, Any]) -> str:
    """
    Takes the structured CodebaseMap dictionary, builds a nested folder tree 
    from the flat file paths, and returns it as a formatted string.
    """
    # Ensure we are working with the expected structure
    if not isinstance(data, dict) or "files" not in data:
        return "Invalid codebase data structure."

    project_name = data.get("project_name", "project_root")
    files = data.get("files", {})

    # 1. Reconstruct the nested folder tree from flat paths
    nested_tree = {}
    for file_path, metadata in files.items():
        # Clean the path to handle accidental leading/trailing slashes
        clean_path = file_path.strip('/')
        if not clean_path:
            continue
            
        parts = clean_path.split('/')
        current_level = nested_tree
        
        # Traverse and build the intermediate folder structure
        for part in parts[:-1]:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        
        # Place the metadata dictionary at the leaf node (the file)
        current_level[parts[-1]] = metadata

    # 2. Helper function to recursively format the tree string
    def _build_lines(node: Dict[str, Any], indent: str = "") -> str:
        lines = []
        
        # Sort items so folders appear before files, or alphabetically
        # (Optional, but makes the output cleaner)
        items = sorted(node.items(), key=lambda x: (isinstance(x[1], dict) and "description" in x[1], x[0]))
        
        for i, (key, value) in enumerate(items):
            is_last = (i == len(items) - 1)
            marker = "└── " if is_last else "├── "
            
            # Identify a file: it has our metadata keys (like 'description' or 'generation_promt')
            if isinstance(value, dict) and "description" in value:
                description = value.get("description", "No description provided.")
                lines.append(f"{indent}{marker}{key}  # {description}")
            
            # Identify a folder: it's a dictionary representing nested contents
            elif isinstance(value, dict):
                lines.append(f"{indent}{marker}{key}/")
                extension = "    " if is_last else "│   "
                subtree = _build_lines(value, indent + extension)
                if subtree:
                    lines.append(subtree)
                    
        return "\n".join(lines)

    # 3. Combine the root project name and the generated tree string
    tree_string = f"{project_name}/\n" + _build_lines(nested_tree)
    return tree_string