import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from langchain_core.messages import HumanMessage, AIMessage

# Import the orchestrator function
from orchestrator.orchestrator import orchestrator

# Initialize Rich Console
console = Console()

async def chat_loop():
    """Main loop for the terminal-based chatbot."""
    # Store conversation history
    history = []
    
    # Render Welcome Banner
    welcome_text = Text("🤖 Welcome to the iSDS Orchestrator CLI", style="bold cyan", justify="center")
    welcome_text.append("\nType your requirements, tasks, or system commands below.", style="italic white")
    welcome_text.append("\nType 'exit' or 'quit' to terminate the session.", style="dim white")
    console.print(Panel(welcome_text, border_style="cyan"))

    while True:
        try:
            # 1. Get User Input
            console.print()
            user_input = console.input("[bold green]❯ You:[/bold green] ").strip()

            # Handle exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[bold red]Shutting down Orchestrator CLI... Goodbye![/bold red]")
                sys.exit(0)

            # Skip empty inputs
            if not user_input:
                continue

            # 2. Process Input via Orchestrator
            # Display a spinner while the agent decides and executes
            with console.status("[bold yellow]Orchestrator is analyzing and routing...[/bold yellow]", spinner="aesthetic"):
                response = await orchestrator(text=user_input, history=history)
            
            # 3. Update Conversation History
            history.append(HumanMessage(content=user_input))
            history.append(AIMessage(content=response))

            # 4. Render Response
            # Render as Markdown to handle code blocks and formatting natively
            response_md = Markdown(response)
            console.print(Panel(
                response_md, 
                title="[bold blue]Orchestrator[/bold blue]", 
                title_align="left",
                border_style="blue"
            ))

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully during the input prompt
            console.print("\n[bold red]Operation cancelled. Type 'exit' to quit.[/bold red]")
            continue
        except Exception as e:
            # Catch and display any execution errors within a styled error panel
            console.print(Panel(
                f"[bold red]System Error:[/bold red] {str(e)}", 
                title="Exception", 
                border_style="red"
            ))

if __name__ == "__main__":
    # Graceful handling of the asyncio event loop
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        console.print("\n[bold red]System terminated.[/bold red]")
        sys.exit(0)