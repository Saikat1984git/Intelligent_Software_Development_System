import asyncio
import os
import json
from deepagents import create_deep_agent

from tools.debug.analyze_webpage_comprehensively import analyze_webpage_comprehensively
from tools.terminal.execute_cli_tool import execute_cli
from tools.terminal.read_file_tool import read_file
from tools.terminal.write_file_tool import write_file
from tools.debug.get_project_metadata import get_project_metadata

from .subagents.qa_verification_subagent import qa_verification_subagent

from langchain.agents.middleware.summarization import SummarizationMiddleware
# Models
from models.gemini_models import GEMINI_3_FLASH

from deepagents.backends import LocalShellBackend

# --- Rich UI Imports ---
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

from models.gemini_models import GEMINI_3_FLASH_LITE

# Initialize Console globally for the script
console = Console()




# 2. Configure the Summarization Middleware
summarization = SummarizationMiddleware(
    model=GEMINI_3_FLASH_LITE,
    
    # TRIGGER: Run when the conversation hits 15 back-and-forth messages
    trigger=[("messages",30)],
    
    # KEEP: Always leave the last 5 messages totally untouched
    keep=("messages", 20),

    # OPTIONAL: Customize the instruction given to the summarizer model
    summary_prompt="Briefly summarize the key points from earlier in the conversation. Retain any specific facts, names, or code snippets."
)

async def run_debugging_agent(
    requirement: str, 
    previous_output: str, 
    root_path: str = ".") -> str:
    """
    Invokes the deep agent with the specific requirement and previous output.
    """
    file_system_backend = LocalShellBackend(root_dir=root_path, virtual_mode=True)  

    # --- 1. Load Static Context (Belongs in System Prompt) ---
    metadata_path = os.path.join(root_path, "project_metadata.json")
    project_metadata_str = "No project_metadata.json found."
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                project_metadata_str = json.dumps(json.load(f), indent=2)
        except Exception as e:
            project_metadata_str = f"Error reading metadata: {e}"

    # --- 2. Define the SYSTEM PROMPT (The Brain & Rules) ---
    system_prompt = f"""You are an expert full-stack execution and debugging agent. Your primary objective is to ALWAYS start by executing the application first, capturing any error logs, and methodically debugging those errors step-by-step.

CRITICAL INSTRUCTION: DO NOT create tasks, plans, or todos to "explore project structure" or "verify files". The complete project structure and file details are already fully provided in the `<project_metadata>` block. You must trust this metadata and skip any manual directory exploration. 

EXECUTION LOOP (MUST FOLLOW EXACTLY):
1. **Execute (Absolute First Step):** Use `execute_cli` to run startup commands (e.g., Docker build/up). Do not explore directories or read files before doing this.
2. **Analyze:** Review captured logs/stack traces from the execution step. Identify the exact error, file, and line.
3. **Read:** If (and only if) an error occurs, use `read_file` on the specific files implicated by the logs. Do not guess contents.
4. **Rewrite:** Use `write_file` to implement a targeted fix for the identified error.
5. **Verify:** Restart via `execute_cli`. Check logs.
6. **Inspect UI:** If the backend is running perfectly, use `qa_verification_subagent` to compare the live webpage against the original requirements. This subagent will also capture any visual bugs or JS errors that don't cause backend crashes.
7. **Iterate/Terminate:** If perfect, terminate. If errors persist, loop back to Step 2.
8. **When to STOP: Only stop when the application is running without any errors AND the QA subagent return isok = True, confirming the app meets the requirements.

ENVIRONMENT CONTEXT
-------------------
<project_metadata>
{project_metadata_str}
</project_metadata>

STRICT CONSTRAINTS & GUARDRAILS:
- DO NOT waste steps exploring the project structure; rely strictly on `<project_metadata>`. Start by executing.
- Never guess file contents or rewrite code without reading the file first.
- Prevent infinite loops by keeping track of previously attempted fixes.
- CRITICAL DOCKER RULE: If you attempt to use Docker and receive an error indicating the Docker daemon is down (e.g., "failed to connect to the docker API"), YOU MUST IMMEDIATELY HALT. Do not attempt local workarounds (like checking java/javac). Stop and alert the user.
"""

    # --- 3. Initialize the Agent ---
    debug_agent = create_deep_agent(
        model = GEMINI_3_FLASH, 
        system_prompt= system_prompt,
        backend=file_system_backend,
        # middleware=[summarization],
        tools = [
            qa_verification_subagent,
            read_file,
            write_file,
            execute_cli,
            get_project_metadata
        ]
    )

    # --- 4. Define the USER PROMPT (The Payload & Trigger) ---
    user_prompt = f"""


TASK
----
You are responsible for running, debugging, and validating the application based on the requirement below.

<requirement>
{requirement}
</requirement>

PREVIOUS CONTEXT
----------------
<context_from_previous_agent>
{previous_output}
</context_from_previous_agent>
    
INSTRUCTIONS
------------
1. Your FIRST action MUST be to execute the application.
2. Identify and fix any runtime, dependency, or configuration issues.
3. Continue iterating until the application runs successfully without errors.
4. Verify that the application behavior satisfies the requirement.
5. If something fails, debug systematically and retry.

OUTPUT REQUIREMENT
------------------
- Provide the fully working URL of the running application.
- Confirm that the application is functioning as intended.
- Mention any fixes or changes you made (briefly).

    """
    
    inputs = {
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }


    # --- 6. Setup Rich Live Display ---
    def generate_status_panel(node="Initializing...", current_context=0, total_in=0, total_out=0):
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("🔄 [bold]Current Node:[/bold]", f"[cyan]{node}[/cyan]")
        table.add_row("🧠 [bold]Current Memory (Context):[/bold]", f"[bold yellow]{current_context:,}[/bold yellow]")
        table.add_row("📥 [bold]Total Session Input:[/bold]", f"[green]{total_in:,}[/green]")
        table.add_row("📤 [bold]Total Session Output:[/bold]", f"[magenta]{total_out:,}[/magenta]")
        table.add_row("📊 [bold]Total Session Tokens:[/bold]", f"[bold white]{total_in + total_out:,}[/bold white]")
        return Panel(table, title="🤖 Agent Status (Live)", border_style="blue", expand=False)
    

    console.print(Panel(f"[bold green]Starting Agent Session[/bold green]\nTarget Path: [italic]{root_path}[/italic]", border_style="green"))

    # Initialize these right before your `with Live(...)` block
    total_input_tokens = 0
    total_output_tokens = 0
    current_context_tokens = 0

    with Live(generate_status_panel(), console=console, refresh_per_second=4, transient=False) as live:
        async for chunk in debug_agent.astream(inputs, stream_mode="updates"):
            for node_name, state in chunk.items():
                
                # 1. Guard Clauses: Skip invalid states
                if not state or not isinstance(state, dict) or not state.get("messages"):
                    continue
                
                messages_update = state["messages"]
                messages_list = messages_update.value if hasattr(messages_update, "value") else messages_update
                
                if not messages_list or not isinstance(messages_list, list):
                    continue
                
                latest_message = messages_list[-1]
                
                # 2. Dual Token Tracking (Memory vs Accumulation)
                if hasattr(latest_message, 'usage_metadata') and latest_message.usage_metadata:
                    usage = latest_message.usage_metadata
                    
                    # Active Context (This will DROP when the summarizer kicks in)
                    current_context_tokens = usage.get('input_tokens', 0) 
                    
                    # Running Session Totals (This will always go UP)
                    total_input_tokens += current_context_tokens
                    total_output_tokens += usage.get('output_tokens', 0)
                
                # Update the UI with both metrics
                live.update(generate_status_panel(
                    node=node_name, 
                    current_context=current_context_tokens, 
                    total_in=total_input_tokens, 
                    total_out=total_output_tokens
                ))

                # 3. Print Tool Calls
                if hasattr(latest_message, 'tool_calls') and latest_message.tool_calls:
                    for tool in latest_message.tool_calls:
                        try:
                            args_str = json.dumps(tool['args'], indent=2)
                        except TypeError:
                            args_str = str(tool['args'])
                        
                        syntax = Syntax(args_str, "json", theme="monokai", line_numbers=False, word_wrap=True)
                        tool_panel = Panel(syntax, title=f"🔧 [bold yellow]Tool Call:[/bold yellow] {tool['name']}", border_style="yellow")
                        console.print(tool_panel)
                        
                # 4. Print Output Text
                elif hasattr(latest_message, 'content') and latest_message.content:
                    content_panel = Panel(latest_message.content, title=f"💬 [bold magenta]Agent Output ({node_name})[/bold magenta]", border_style="magenta")
                    console.print(content_panel)
                    final_content = latest_message.content

    # --- 8. Final Summary ---
    summary_table = Table(title="Agent Session Summary", show_header=True, header_style="bold blue")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right", style="green")
    
    # 1. The final size of the memory after all summarizations
    summary_table.add_row("Final Context Size (Memory)", f"[bold magenta]{current_context_tokens:,}[/bold magenta]")
    
    # 2. The accumulated metrics
    summary_table.add_row("Total Session Input Tokens", f"{total_input_tokens:,}")
    summary_table.add_row("Total Session Output Tokens", f"{total_output_tokens:,}")
    
    # 3. The grand total
    summary_table.add_row("Grand Total", f"[bold yellow]{total_input_tokens + total_output_tokens:,}[/bold yellow]")
    
    console.print()
    console.print(summary_table)
    
    return final_content

# --- Example Usage ---
if __name__ == "__main__":    
    req = """Create  a sici-fi calculator app using  react and nodejs. The app should have a futuristic design and include all features"""

    prev_out = """[Application created]""" 

    root_path = "D:/Development/new_vibe_code/generated/latest_2026-03-23_23-06-31"
    try:
        os.chdir(root_path)
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Path not found: {root_path}")
        exit(1)

    final_result = asyncio.run(run_debugging_agent(req, prev_out, root_path))
    
    console.print(Panel(final_result, title="[bold green]=== Execution Complete ===[/bold green]", border_style="green"))