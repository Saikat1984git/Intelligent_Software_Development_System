import asyncio
import os
import platform
import shutil
import sys
from datetime import datetime
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.create_project_structure_tool import create_project_structure_tool
from tools.write_file_tool import write_file_tool
from tools.debug.fetch_webpage_content import fetch_webpage_content
from tools.debug.capture_website_screenshot import capture_website_screenshot

from models.openai_models import GPT_51_CODEX_MINI, GPT_4O_MINI, GPT_52_CHAT , GPT_5_MINI_TEST
from models.gemini_models import GEMINI_31_PRO, GEMINI_25_PRO, GEMINI_3_FLASH, GEMINI_25_FLASH, GEMINI_25_FLASH_LITE


from agents.codegen_agent import run_codegeneration_agent
from agents.debug_agent import run_debugging_agent
from utils import should_continue_debugging


load_dotenv()


# --- Constants for Workspace Setup ---
ROOT_PATH = os.getcwd()
SKILLS_DIR = os.path.join(ROOT_PATH, "skills")
BASE_DIR = os.path.join(ROOT_PATH, "generated")

def get_timestamped_dir():
    """Generates and creates a timestamped directory for isolated execution."""
    # Example: 2026-03-08_10-45-30
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(BASE_DIR, f"latest_{timestamp}")

    # Create directory (safe even if exists)
    os.makedirs(path, exist_ok=True)

    return path


async def main():
    user_requirements = (
      """
    scientific calculator that can perform all mathematical operations in angular, with a user-friendly interface and responsive design. The calculator should have buttons for digits 0-9, basic operations (+, -, *, /), a clear button (C), and an equals button (=). The interface should display the current input and the result of calculations. Additionally, the design should be responsive to work well on both desktop and mobile devices.

"""
    )
    print("🚀 Starting the AI Software Architect...")
    
    # 1. --- SETUP ISOLATED WORKSPACE ---
    TARGET_ROOT = get_timestamped_dir()
    target_skills_dir = os.path.join(TARGET_ROOT, "skills")
    
    # Copy all skills into the target path before changing directories
    if os.path.exists(SKILLS_DIR):
        print(f"📁 Copying skills to isolated environment...")
        shutil.copytree(SKILLS_DIR, target_skills_dir, dirs_exist_ok=True)
    else:
        print(f"⚠️  WARNING: Source skills directory '{SKILLS_DIR}' not found.")
        print("Creating an empty 'skills' directory in the target path to prevent agent errors.")
        os.makedirs(target_skills_dir, exist_ok=True)

    # Move the Python execution context into the new isolated folder
    os.chdir(TARGET_ROOT)
    print(f"🔒 Agent will operate in isolated directory: {TARGET_ROOT}\n")
    
    print("⚙️  Running code generation...")
    execution_agent_summary = await run_codegeneration_agent(
        user_requirements=user_requirements,
    )
    print("✅ Code generation complete!\n")

    # --- THE INTERACTIVE LANGCHAIN DECISION GATE ---
    user_response = input("🤔 Do you want to start the debugging process now? ")
    
    print("🤖 Analyzing response...")
    wants_to_debug = await should_continue_debugging(user_response)
    
    if not wants_to_debug:
        print("🛑 User opted to skip debugging. Exiting process...")
        return  # Safely exit the function
    # -----------------------------------------------

    print("\n🐞 Starting the debugging process...")
    # 2. Starting the debugging process
    debugging_agent_summary = await run_debugging_agent(
        requirement=user_requirements,
        previous_output=execution_agent_summary,
        root_path=TARGET_ROOT
    )
    print("🐞🔫 Debugging process complete!\n")
    
    print("✅ All tasks finished!")
     

if __name__ == "__main__":
    asyncio.run(main())