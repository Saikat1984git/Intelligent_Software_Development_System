import docker
import base64
import json
import re
from datetime import datetime
from fnmatch import fnmatch

# Assuming these are imported from your deepagents framework
from deepagents.backends.protocol import BackendProtocol, WriteResult, EditResult
from deepagents.backends.utils import FileInfo, GrepMatch

class DockerLinuxBackend(BackendProtocol):
    def __init__(self, container_id_or_name: str, workspace_prefix: str = "/workspace"):
        """
        Initializes the connection to a running Docker container.
        workspace_prefix: The root directory inside the container to sandbox operations.
        """
        self.client = docker.from_env()
        self.container = self.client.containers.get(container_id_or_name)
        self.workspace_prefix = workspace_prefix.rstrip("/")
        
        # Ensure the workspace directory exists inside the container
        self.container.exec_run(f"mkdir -p {self.workspace_prefix}")

    def _map_path(self, path: str) -> str:
        """Translates virtual absolute paths (/src/app.py) to container paths."""
        clean_path = path if path.startswith("/") else "/" + path
        return f"{self.workspace_prefix}{clean_path}"

    def _run_python_in_container(self, script: str) -> dict:
        """Executes a python script inside the container safely and returns JSON."""
        # Wrap the script to return JSON payload or error string
        b64_script = base64.b64encode(script.encode('utf-8')).decode('utf-8')
        cmd = f"sh -c 'echo {b64_script} | base64 -d | python3'"
        
        exit_code, output = self.container.exec_run(cmd)
        output_str = output.decode('utf-8').strip()
        
        if exit_code != 0:
            return {"error": output_str}
        try:
            return json.loads(output_str)
        except json.JSONDecodeError:
            return {"error": "Failed to parse container output"}

    def ls_info(self, path: str) -> list[FileInfo]:
        """Server-side listing utilizing standard OS modules inside the container."""
        full_path = self._map_path(path)
        
        # We run this inside the container to get accurate posix stats regardless of the base image
        script = f"""
import os, stat, json
path = "{full_path}"
res = []
try:
    if os.path.exists(path) and os.path.isdir(path):
        for f in os.listdir(path):
            fp = os.path.join(path, f)
            st = os.stat(fp)
            # Send back timestamp and size
            res.append({{"name": f, "size": st.st_size, "mtime": st.st_mtime}})
    print(json.dumps({{"data": res}}))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
        """
        result = self._run_python_in_container(script)
        
        if "error" in result:
            return [] # deepagents usually expects empty list on fail for ls
            
        return [
            FileInfo(
                path=f"{path.rstrip('/')}/{item['name']}",
                size=item['size'],
                modified_at=datetime.fromtimestamp(item['mtime'])
            ) for item in result.get("data", [])
        ]

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        """Fetches file content from the container."""
        full_path = self._map_path(file_path)
        exit_code, output = self.container.exec_run(f"cat {full_path}")
        
        if exit_code != 0:
            return f"Error: File not found or permission denied at '{file_path}'"
            
        content = output.decode('utf-8')
        return content[offset:offset+limit]

    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        """Fetches candidate files and scans content in the local Python runtime."""
        try:
            regex = re.compile(pattern)
        except re.error:
            return f"Error: Invalid regex pattern '{pattern}'"

        target_dir = path if path else "/"
        files_to_check = self.glob_info(glob or "*", target_dir)
        
        matches = []
        for file_info in files_to_check:
            # Read the full file content (ignoring limit for grep purposes)
            full_path = self._map_path(file_info.path)
            exit_code, output = self.container.exec_run(f"cat {full_path}")
            
            if exit_code != 0:
                continue
                
            content = output.decode('utf-8')
            for match in regex.finditer(content):
                line_num = content.count('\n', 0, match.start()) + 1
                matches.append(GrepMatch(
                    path=file_info.path,
                    line=line_num,
                    content=match.group(0)
                ))
        return matches

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Applies glob filtering over the container directory tree."""
        full_path = self._map_path(path)
        
        # Recursive walk inside the container to avoid pulling massive directories locally
        script = f"""
import os, fnmatch, json
root_dir = "{full_path}"
pattern = "{pattern}"
res = []
try:
    for dirpath, _, filenames in os.walk(root_dir):
        for f in fnmatch.filter(filenames, pattern):
            fp = os.path.join(dirpath, f)
            st = os.stat(fp)
            # Remove the host prefix so the agent only sees the virtual path
            virtual_path = fp.replace(root_dir, "{path.rstrip('/')}").replace("//", "/")
            res.append({{"path": virtual_path, "size": st.st_size, "mtime": st.st_mtime}})
    print(json.dumps({{"data": res}}))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
        """
        result = self._run_python_in_container(script)
        if "error" in result:
            return []
            
        return [
            FileInfo(
                path=item['path'],
                size=item['size'],
                modified_at=datetime.fromtimestamp(item['mtime'])
            ) for item in result.get("data", [])
        ]

    def write(self, file_path: str, content: str) -> WriteResult:
        """Writes a new file to the container using Base64 to bypass shell escaping rules."""
        full_path = self._map_path(file_path)
        
        # Check if exists (Create-only semantics)
        exit_code, _ = self.container.exec_run(f"test -e {full_path}")
        if exit_code == 0:
             return WriteResult(error=f"File already exists at {file_path}. Use edit() to modify.", files_update=None)
             
        # Encode content to base64
        b64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Create directories and decode base64 straight into the file
        cmd = f"sh -c 'mkdir -p $(dirname {full_path}) && echo {b64_content} | base64 -d > {full_path}'"
        exit_code, output = self.container.exec_run(cmd)
        
        if exit_code != 0:
            return WriteResult(error=f"Container write failed: {output.decode('utf-8')}", files_update=None)
            
        return WriteResult(path=file_path, files_update=None)

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        """Reads, replaces in the local host process, and writes back via Base64."""
        full_path = self._map_path(file_path)
        
        # 1. Read
        exit_code, output = self.container.exec_run(f"cat {full_path}")
        if exit_code != 0:
            return EditResult(error=f"File not found at {file_path}")
            
        current_content = output.decode('utf-8')
        occurrences = current_content.count(old_string)
        
        if occurrences == 0:
            return EditResult(error=f"String '{old_string}' not found in file.")
        if occurrences > 1 and not replace_all:
            return EditResult(error=f"String '{old_string}' found {occurrences} times. Must specify replace_all=True.")

        # 2. Replace
        count = -1 if replace_all else 1
        updated_content = current_content.replace(old_string, new_string, count)
        
        # 3. Write Back
        b64_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
        cmd = f"sh -c 'echo {b64_content} | base64 -d > {full_path}'"
        
        write_code, write_out = self.container.exec_run(cmd)
        if write_code != 0:
            return EditResult(error=f"Failed to save edits: {write_out.decode('utf-8')}")
            
        return EditResult(path=file_path, occurrences=occurrences if replace_all else 1)