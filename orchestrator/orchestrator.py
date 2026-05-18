import asyncio
import os
import platform
import shutil
import sys
from datetime import datetime
from typing import List

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

# --- Rich Library Imports for Fullscreen TUI ---
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from agents.code_editing_agent import code_editing_agent
from agents.codegen_agent import run_codegeneration_agent
from agents.debug_agent import run_debugging_agent
from agents.qa_testing_agent import qa_testing_with_requirements
from agents.subagents.code_analyzer_subagent import analyze_codebase_agent

from models.openai_models import GPT_51_CODEX_MINI, GPT_4O_MINI, GPT_52_CHAT , GPT_5_MINI_TEST
from models.gemini_models import GEMINI_31_PRO, GEMINI_25_PRO, GEMINI_3_FLASH, GEMINI_25_FLASH, GEMINI_25_FLASH_LITE

# Initialize Rich Console
console = Console()

# --- 1. Define LangChain Tools ---

ROOT_PATH = os.getcwd()
SKILLS_DIR = os.path.join(ROOT_PATH, "skills")
BASE_DIR = os.path.join(ROOT_PATH, "generated")

def get_timestamped_dir():
    """Generates and creates a timestamped directory for isolated execution."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(BASE_DIR, f"latest_{timestamp}")
    os.makedirs(path, exist_ok=True)
    return path

def ensure_project_metadata(project_folder_path: str):
    """
    Checks if project_metadata.json exists in the target directory. 
    If not, it triggers the code analyzer subagent to generate it.
    """
    metadata_file = os.path.join(project_folder_path, "project_metadata.json")
    if not os.path.exists(metadata_file):
        console.print(f"[bold yellow]⚠️ project_metadata.json not found in {project_folder_path}[/bold yellow]")
        console.print("[dim]🔍 Running Code Analyzer Agent to map the codebase...[/dim]")
        try:
            # Call the synchronous wrapper of the analyzer agent
            analyzer_result = analyze_codebase_agent(project_folder_path)
            console.print("[green]✅ Codebase mapping complete. Metadata generated.[/green]")
            console.print(f"[dim]{analyzer_result}[/dim]")
        except Exception as e:
            console.print(f"[bold red]❌ Failed to generate project_metadata.json: {str(e)}[/bold red]")
            raise e
    else:
        console.print("[dim]✅ project_metadata.json found. Proceeding with existing architecture map...[/dim]")

@tool
async def generate_code_tool(user_requirements: str) -> str:
    """
    Main tool to run the code generation workflow. 
    Use this when the user wants to build a new application or generate a codebase from scratch based on requirements.
    """
    console.print("[bold cyan]🚀 Starting the AI Software Architect...[/bold cyan]")
    
    # 1. --- SETUP ISOLATED WORKSPACE ---
    TARGET_ROOT = get_timestamped_dir()
    target_skills_dir = os.path.join(TARGET_ROOT, "skills")
    
    # Copy all skills into the target path before changing directories
    if os.path.exists(SKILLS_DIR):
        console.print("[dim]📁 Copying skills to isolated environment...[/dim]")
        shutil.copytree(SKILLS_DIR, target_skills_dir, dirs_exist_ok=True)
    else:
        console.print(f"[bold yellow]⚠️ WARNING: Source skills directory '{SKILLS_DIR}' not found.[/bold yellow]")
        console.print("[dim]Creating an empty 'skills' directory in the target path to prevent agent errors.[/dim]")
        os.makedirs(target_skills_dir, exist_ok=True)

    # Move the Python execution context into the new isolated folder
    os.chdir(TARGET_ROOT)
    console.print(f"[green]🔒 Agent will operate in isolated directory: {TARGET_ROOT}[/green]\n")
    
    console.print("[bold blue]⚙️ Running code generation...[/bold blue]")
    summary = await run_codegeneration_agent(user_requirements)
    return f"Code generation completed. Summary: {summary}"


@tool
async def run_and_debug_code_tool(requirement: str, previous_output: str, root_path: str = ".") -> str:
    """
    OIt trys to run the generated code and if it encounters errors, it invokes the debugging agent to fix issues.
    Use this when the user wants to execute the generated code and automatically debug any issues that arise during execution.
    """
    console.print("[bold yellow]🐛 Starting Debugging Agent...[/bold yellow]")
    result = await run_debugging_agent(requirement, previous_output, root_path)
    return f"Debugging completed. Result: {result}"


@tool
def edit_code_tool(edit_prompt: str, project_folder_path: str) -> str:
    """
    Analyzes project metadata and edits existing files.
    Use this when the user wants to fix an issue or modify specific code files within an existing project folder.
    """
    console.print("[bold magenta]📝 Starting Code Editing Agent...[/bold magenta]")

    # Check and generate project metadata if it's missing before attempting to edit
    ensure_project_metadata(project_folder_path)
    
    result = code_editing_agent(edit_prompt, project_folder_path)
    return f"Code editing completed. Result: {result}"


@tool
def qa_testing_tool(file_path: str, requirements: str) -> str:
    """
    Runs the QA testing agent.
    Use this when the user wants to test a website or application against specific requirements.
    """
    console.print("[bold red]🧪 Starting QA Testing Agent...[/bold red]")
    qa_testing_with_requirements(file_path, requirements)
    return f"QA Testing completed for requirements: {requirements}"


# --- 2. Orchestrator Function ---

async def orchestrator(text: str, history: List[BaseMessage]) -> str:
    """
    Orchestrates the agent workflows by deciding which tool to run and with what parameters.
    """
    tools = [generate_code_tool, run_and_debug_code_tool, edit_code_tool, qa_testing_tool]
    llm_with_tools = GPT_4O_MINI.bind_tools(tools)
    
    system_prompt = SystemMessage(
        content=(
            "You are an intelligent software architecture orchestrator. "
            "Analyze the user's request and the conversation history. "
            "Decide which underlying agent tool to invoke to fulfill the request. "
            "Extract the necessary parameters from the user's prompt to pass into the tool."
        )
    )
    
    messages = [system_prompt] + history + [HumanMessage(content=text)]
    
    console.print("[bold yellow]🧠 Orchestrator is analyzing the request...[/bold yellow]")
    response = await llm_with_tools.ainvoke(messages)
    
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        console.print(f"[bold green]🔧 Routing to tool:[/bold green] {tool_name}")
        console.print(f"[dim]Parameters: {tool_args}[/dim]")
        
        for t in tools:
            if t.name == tool_name:
                try:
                    tool_result = await t.ainvoke(tool_args)
                    return tool_result
                except Exception as e:
                    return f"❌ Error executing {tool_name}: {str(e)}"
                    
        return f"⚠️ Tool {tool_name} was selected by the LLM but not found in the registry."
    
    else:
        console.print("[dim]💬 No specific agent triggered. Returning standard response.[/dim]")
        return response.content

# --- 3. Fullscreen Terminal UI Loop ---

async def main():
    history: List[BaseMessage] = []
    
    while True:
        # Clear the terminal screen entirely to create a "fullscreen" effect
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Draw the top header spanning the width of the terminal
        header = Panel("[bold cyan]AI Software Architect - Orchestrator Terminal[/bold cyan]", expand=True, style="on dark_blue")
        console.print(header)
        
        # Render conversation history
        if history:
            console.print("\n[bold]Conversation Log:[/bold]")
            for msg in history:
                if isinstance(msg, HumanMessage):
                    console.print(f"[bold green]User:[/bold green] {msg.content}")
                elif isinstance(msg, AIMessage):
                    console.print(f"[bold purple]Agent:[/bold purple] {msg.content}")
            # Visual separator
            console.print("-" * console.width)
        
        # User input prompt
        console.print("")
        user_input = Prompt.ask("[bold yellow]Enter your request (or 'exit' to quit)[/bold yellow]")
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            console.print("[bold green]Goodbye![/bold green]")
            break
            
        console.print("")
        
        # Execute orchestrator and capture response
        try:
            result = await orchestrator(user_input, history)
            
            # Update history with the latest interaction
            history.append(HumanMessage(content=user_input))
            history.append(AIMessage(content=result))
            
            # Print the final result in a highlighted panel
            console.print("\n", Panel(result, title="Execution Result", border_style="green", expand=True))
            
        except Exception as e:
            console.print(Panel(f"An error occurred: {str(e)}", title="Error", border_style="red", expand=True))
        
        # Pause to let the user read the output before the next loop clears the screen
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(0)