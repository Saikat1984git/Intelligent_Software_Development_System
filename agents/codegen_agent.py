import os
import shutil
import asyncio
from datetime import datetime
from typing import TypedDict, Optional, List, Dict, Any
from deepagents import CompiledSubAgent
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END


from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

from agents.states.CodebaseState import CodebaseState
from tools.codegenerator.generate_codebase_structure import generate_codebase_structure_node
from tools.codegenerator.generate_project_files import generate_project_files_node
from tools.codegenerator.load_skills_node import load_skills_node
from tools.codegenerator.execute_skill_scripts_node import execute_skill_scripts_node
from tools.codegenerator.summarize import summarize_codebase_node


console = Console()
load_dotenv()  # Load environment variables from .env file if it exists

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

from langgraph.graph import StateGraph, START, END

# --- Define the Router Function ---
def should_execute_scripts(state: CodebaseState) -> str:
    return "end" 
    """
    Conditional router: Checks if skills were loaded.
    If skills_text is not empty, route to script execution.
    Otherwise, skip to file generation.
    """
    skills = state.get("skills_text")
    
    # This evaluates to True if skills is a non-empty list, dict, or string
    if skills: 
        print("ROUTER: Skills found. Routing to 'execute_skill_scripts'.")
        return "execute_skill_scripts"
    
    print("ROUTER: No skills found. Skipping to 'generate_files'.")
    return "end"  # This will route to the END node, which we will handle in the graph definition

# --- Update the Graph Builder ---
def build_codebase_graph():
    """
    Constructs and compiles the LangGraph state machine.
    """
    # Initialize the graph with our custom state
    workflow = StateGraph(CodebaseState)

    # 1. Add the nodes to the graph
    workflow.add_node("load_skills", load_skills_node)
    workflow.add_node("generate_structure", generate_codebase_structure_node)
    workflow.add_node("execute_skill_scripts", execute_skill_scripts_node)  # <-- Added new node
    workflow.add_node("generate_files", generate_project_files_node)
    workflow.add_node("summarize", summarize_codebase_node)

    # 2. Define the base execution flow
    workflow.add_edge(START, "load_skills")
    # workflow.add_edge(START, "generate_structure")
    workflow.add_edge("load_skills", "generate_structure")
    workflow.add_edge("generate_structure", "generate_files")
    
    # 3. Add the CONDITIONAL edge after file generation
    workflow.add_conditional_edges(
        "generate_files",               # The node we are coming from
        should_execute_scripts,         # The routing function
        {
            # Map the string returned by the router to the actual node names
            "execute_skill_scripts": "execute_skill_scripts",
            "end": "summarize"          # <-- FIX 1: Go to summarize instead of END
        }
    )
    
    # 4. If we routed to the scripts node, send it to summarize afterward
    workflow.add_edge("execute_skill_scripts", "summarize") # <-- FIX 2: Go to summarize instead of END
    
    # 5. Finally, the summarize node finishes the graph
    workflow.add_edge("summarize", END)                     # <-- FIX 3: End the graph here
    
    

    # Compile the graph into an executable application
    return workflow.compile()







# code_generation_graph = build_codebase_graph()
# code_generation_subagent = CompiledSubAgent(
#     name="Codebase Generation Agent",
#     description="An agent that generates a codebase structure, creates project files, and executes skill scripts based on user requirements.",
#     runnable=code_generation_graph
# )






# --- Main Execution ---
async def run_codegeneration_agent(user_requirements):
    """
    Main function to run the code generation agent workflow.
    This function sets up an isolated workspace, runs the code generation workflow,
    and then prompts the user to decide whether to proceed with debugging.
        The workflow includes:
        1. Loading skills
        2. Generating codebase structure
        3. Conditionally executing skill scripts if skills were loaded
        4. Generating project files
        5. Summarizing the generated codebase

    """
    
    # # 2. --- DEFINE REQUIREMENTS ---
    # user_requirements = (
    #     "Create a scifi looking scientific calculator web app using struts with a sleek, modern design."
    # )
    
    # 3. --- RUN LANGGRAPH WORKFLOW ---
    app = build_codebase_graph()
    
    # Define the initial state inputs
    # We use "./skills" because we've already changed the working directory to TARGET_ROOT
    initial_state = {
        "requirements": user_requirements,
        "skills": "./skills"
    }

    console.rule("[bold green]STARTING LANGGRAPH STREAMING WORKFLOW")
    final_state = initial_state.copy() if isinstance(initial_state, dict) else {}
    
    try:
        # 'updates' mode shows you the output of each node as it finishes
        async for event in app.astream(initial_state, stream_mode="updates"):
            for node_name, output in event.items():
                console.print(Panel(
                    f"Finished executing node: [bold magenta]{node_name}[/bold magenta]",
                    title="Node Update",
                    border_style="blue"
                ))
                
                # Optionally print the keys updated in the state
                if output:
                    for key, value in output.items():

                        console.print(f"[bold cyan]{key}[/bold cyan] updated")

                        console.print(
                            Panel(
                                str(value),
                                title=f"Content of {key}",
                                border_style="green"
                            )
                        )

                        # 2. Accumulate the state updates
                        # NOTE: This assumes standard key overwriting. 
                        final_state[key] = value
        console.print("\n[bold yellow]✨ Workflow Complete![/bold yellow]")
        console.print(
            Panel(
                str(final_state), 
                title="🏁 Final Complete State", 
                border_style="bold yellow",
                expand=False
            )
        )

        return f"""PROJECT PATH:{os.getcwd()}\nAGENT SUMMARY:{final_state["agent_summary"] if "agent_summary" in final_state else "No agent summary available."}"""


    except Exception as e:
        console.print(f"\n[bold red]FATAL ERROR during streaming:[/bold red] {e}")
        # This will help you find exactly which line in which node failed
        import traceback
        console.print(traceback.format_exc())

    console.rule("[bold green]WORKFLOW COMPLETE")

if __name__ == "__main__":
    # Run the async loop
    run_codegeneration_agent()