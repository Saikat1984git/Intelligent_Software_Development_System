import json
import os
import re
from typing import Dict, Any, Optional, List, TypedDict

from rich.console import Console
from rich.panel import Panel

# Assuming these are imported from your existing modules
from utils.extract_text_from_response import extract_text_from_response
from models.gemini_models import GEMINI_31_PRO

console = Console()

# 1. Define the LangGraph State
class CodebaseState(TypedDict):
    requirements: str
    skills_text: Optional[Dict[str, str]]  # mapping 'folder_name/file_name' -> file content
    skills:   Optional[str]  # folder path of skills , example "/skills/"
    project_structure: Optional[Dict[str, Any]]
    file_paths: Optional[List[str]]
    metadata_file: Optional[str]
    status: Optional[str]
    error: Optional[str]
    execution_log: Optional[List[str]]
    agent_summary: Optional[str]

