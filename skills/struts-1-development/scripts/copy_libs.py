import argparse
import shutil
import sys
from pathlib import Path

def copy_struts_libraries(destination_path: str):
    """
    Copies all .jar files from the sibling 'libraries' folder to the destination path.
    Designed to be executed as an agent skill/tool.
    """
    # 1. Dynamically find the 'libraries' folder based on this script's location
    # __file__ points to scripts/copy_libs.py
    # .parent points to the 'scripts' folder
    # .parent.parent points to the 'struts-1-development' folder
    script_path = Path(__file__).resolve()
    base_dir = script_path.parent.parent 
    src_path = base_dir / "libraries"
    
    dest_path = Path(destination_path).resolve()

    # 2. Validate that the source 'libraries' folder exists
    if not src_path.exists() or not src_path.is_dir():
        print(f"Error: Source folder not found at '{src_path}'.")
        print("Please ensure the 'libraries' folder exists in the parent directory of this script.")
        sys.exit(1)

    # 3. Ensure the destination directory exists (create it if it doesn't)
    try:
        dest_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"Error: Permission denied to create destination '{dest_path}'.")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating destination directory: {e}")
        sys.exit(1)

    # 4. Find all .jar files in the source folder
    jar_files = list(src_path.glob("*.jar"))
    
    if not jar_files:
        print(f"Notice: No .jar files found in '{src_path}'.")
        return

    print(f"Found {len(jar_files)} .jar files. Starting copy process...")
    
    # 5. Copy the files
    success_count = 0
    for jar_file in jar_files:
        try:
            # shutil.copy2 preserves file metadata (timestamps, etc.)
            shutil.copy2(jar_file, dest_path / jar_file.name)
            print(f" [✓] Copied: {jar_file.name}")
            success_count += 1
        except Exception as e:
            print(f" [✗] Failed to copy {jar_file.name}: {e}")

    print(f"\nOperation complete. Successfully copied {success_count}/{len(jar_files)} files to:\n{dest_path}")

if __name__ == "__main__":
    # Set up argument parsing for the agent to pass the path
    parser = argparse.ArgumentParser(description="Copy Struts .jar libraries to a specified destination.")
    parser.add_argument(
        "destination", 
        type=str, 
        help="The absolute or relative destination path where the .jar files should be copied."
    )
    
    args = parser.parse_args()
    
    # Execute the copy function
    copy_struts_libraries(args.destination)