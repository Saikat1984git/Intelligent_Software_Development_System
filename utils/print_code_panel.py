import os
from dotenv import load_dotenv
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

from models.openai_models import GPT_51_CODEX_MINI, GPT_4O_MINI, GPT_52_CHAT , GPT_5_MINI_TEST
from models.gemini_models import GEMINI_31_PRO, GEMINI_25_PRO, GEMINI_3_FLASH, GEMINI_25_FLASH, GEMINI_25_FLASH_LITE


console = Console()


def print_code_panel(file_path: str, content: str):
    # Detect language from file extension
    ext = file_path.split(".")[-1]

    language_map = {
        "py": "python",
        "java": "java",
        "html": "html",
        "js": "javascript",
        "ts": "typescript",
        "css": "css",
        "json": "json",
        "yml": "yaml",
        "yaml": "yaml",
    }

    language = language_map.get(ext, "text")

    syntax = Syntax(
        content,
        language,
        line_numbers=True,
        word_wrap=True
    )

    panel = Panel(
        syntax,
        title=f"📄 {os.path.basename(file_path)}",
        subtitle=f"Path: {file_path}",
        border_style="cyan",
        padding=(1,2)
    )

    console.print(panel)