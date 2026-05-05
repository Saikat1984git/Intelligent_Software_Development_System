import pathlib

def generate_tree(path, indent="", ignore_list=None):
    if ignore_list is None:
        ignore_list = {'.git', '__pycache__', 'node_modules', '.venv', '.DS_Store'}
    
    path = pathlib.Path(path)
    
    # Get all items in directory and filter them
    items = [item for item in path.iterdir() if item.name not in ignore_list]
    
    # Sort: Directories first, then files
    items.sort(key=lambda x: (x.is_file(), x.name.lower()))

    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        
        print(f"{indent}{connector}{item.name}")
        
        if item.is_dir():
            # Extend the indent for sub-directories
            new_indent = indent + ("    " if is_last else "│   ")
            generate_tree(item, new_indent, ignore_list)

if __name__ == "__main__":
    # Define your ignore list here
    to_ignore = {
        '.git', 
        '__pycache__', 
        'node_modules', 
        '.venv', 
        'dist', 
        '.DS_Store',
        '*.pyc' # Note: simple strings used here for exact matching
    }
    
    root_dir = "."  # Current directory
    print(f"Project Root: {pathlib.Path(root_dir).absolute().name}")
    generate_tree(root_dir, ignore_list=to_ignore)