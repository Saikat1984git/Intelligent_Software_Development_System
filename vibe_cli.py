import os
import sys
import time
import random
from datetime import datetime
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.tree import Tree
from rich.align import Align

console = Console()

# --- State Management ---
chat_history = [
    {"role": "assistant", "content": "Vibe Studio Ready. Type /img [path] [prompt] to upload, or /clear to reset.", "type": "text"}
]
terminal_logs = []

def add_log(level, msg, color="white"):
    terminal_logs.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "level": f" {level} ",
        "msg": msg,
        "color": color
    })

def render_ui(layout):
    """Atomically redraws the screen without clearing the buffer."""
    sys.stdout.write("\033[H")
    console.print(layout)
    sys.stdout.write("\033[J")
    sys.stdout.flush()

# --- UI Components ---

def get_chat_content(is_typing=False):
    renderables = []
    
    for msg in chat_history[-7:]:
        renderables.append(Text("")) # Spacer
        
        if msg["role"] == "user":
            user_msg = Text(msg['content'].strip(), style="bold bright_cyan")
            bubble = Panel(user_msg, title="[bold deep_sky_blue1]YOU[/]", title_align="right", border_style="deep_sky_blue1", box=box.ROUNDED, expand=False, padding=(0, 1))
            renderables.append(Align.right(bubble))
            
        else:
            ai_msg = Text(msg['content'].strip(), style="white")
            bubble = Panel(ai_msg, title="[bold plum1]✨ VIBE AGENT[/]", title_align="left", border_style="plum1", box=box.ROUNDED, expand=False, padding=(0, 1))
            renderables.append(Align.left(bubble))
            
    if is_typing:
        renderables.append(Text(""))
        typing_indicator = Text(" ✨ Agent is processing...", style="dim italic plum1")
        renderables.append(Align.left(typing_indicator))
        
    return Panel(Group(*renderables), title="[bold plum1]💬 DIALOGUE FEED[/]", border_style="plum1", box=box.ROUNDED)

def get_terminal_content(is_running):
    term_content = Text()
    max_logs = max(5, console.height - 8)
    
    for log in terminal_logs[-max_logs:]:
        term_content.append(f"{log['timestamp']} ", style="dim")
        term_content.append(log["level"], style=f"bold black on {log['color']}")
        term_content.append(f" {log['msg']}\n", style="bright_white")
    
    if is_running:
        term_content.append("\n 🚀 [bold blink spring_green3]PROCESSING MULTIMODAL DATA...[/]")
    else:
        term_content.append("\n ❯ SYSTEM IDLE", style="bold dim green")
        
    return Panel(term_content, title="[bold spring_green3]🖥️ SYSTEM LOGS[/]", border_style="spring_green3", box=box.ROUNDED)

def get_file_explorer(work_dir):
    tree = Tree(f"📂 [bold bright_blue]{os.path.basename(work_dir)}[/]", guide_style="bright_black")
    try:
        items = os.listdir(work_dir)
        items.sort(key=lambda x: (not os.path.isdir(os.path.join(work_dir, x)), x.lower()))
        
        for file in items[:25]:
            full_path = os.path.join(work_dir, file)
            if os.path.isdir(full_path):
                tree.add(f"📁 [bold cyan]{file}[/]")
            else:
                ext = os.path.splitext(file)[1].lower()
                style = "white"
                icon = "📄"
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']: 
                    style = "bright_magenta bold"
                    icon = "🖼️"
                elif ext in ['.py', '.js', '.json', '.txt']:
                    style = "green"
                    icon = "📜"
                tree.add(f"{icon} [{style}]{file}[/]")
    except: 
        tree.add("[red]Access Denied[/]")
        
    return Panel(tree, title="[bold bright_blue]WORKSPACE[/]", border_style="bright_blue", box=box.ROUNDED)

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=1)
    )
    layout["main"].split_row(
        Layout(name="sidebar", size=30),
        Layout(name="chat", ratio=6),
        Layout(name="terminal", ratio=4)
    )
    return layout

# --- Main Application ---

def run_app():
    add_log("START", "Multimodal Engine Online", "cyan")
    add_log("INFO", "Neural pathways initialized.", "blue")
    add_log("SYS", "Awaiting user input...", "spring_green3")
    
    default_dir = os.getcwd()
    console.print(Panel(
        "[bold bright_magenta]⚡ VIBE STUDIO CLI [v9.1][/]\n[dim]Cyberpunk Mode Active • Type 'exit' to quit", 
        box=box.DOUBLE_EDGE, 
        border_style="cyan",
        padding=(1, 2)
    ))
    
    work_dir = console.input(f"\n[bold cyan]📁 Select Workspace Path:[/] ") or default_dir
    work_dir = os.path.abspath(work_dir)

    ui_layout = make_layout()
    
    sys.stdout.write("\033[2J") 
    sys.stdout.flush()

    while True:
        ui_layout["header"].update(Panel(Text(f" VIBE STUDIO  |  {work_dir} ", justify="center", style="bold bright_white"), style="on bright_magenta", box=box.SIMPLE))
        ui_layout["sidebar"].update(get_file_explorer(work_dir))
        ui_layout["chat"].update(get_chat_content(is_typing=False))
        ui_layout["terminal"].update(get_terminal_content(is_running=False))
        ui_layout["footer"].update(Text(" Commands: /img [path] [prompt] | /clear | Type 'exit' to quit ", justify="center", style="dim italic black on bright_white"))

        render_ui(ui_layout)
        
        user_input = console.input("[bold bright_magenta]❯ [/]")
        
        if user_input.lower() in ['exit', 'quit']: 
            break
        if not user_input.strip():
            continue

        if user_input.strip().lower() == "/clear":
            chat_history.clear()
            chat_history.append({"role": "assistant", "content": "Vibe Studio Ready. Type /img [path] [prompt] to upload, or /clear to reset.", "type": "text"})
            terminal_logs.clear()
            add_log("SYS", "Buffers cleared by user.", "spring_green3")
            continue

        chat_history.append({"role": "user", "content": user_input, "type": "text"})
        is_image = user_input.startswith("/img ")
        
        ui_layout["chat"].update(get_chat_content(is_typing=True))
        final_response = ""
        
        if is_image:
            remainder = user_input[5:].strip()
            img_path = ""
            user_prompt = ""
            
            # --- SMART PATH PARSER ---
            if remainder.startswith('"') or remainder.startswith("'"):
                quote_char = remainder[0]
                end_quote_idx = remainder.find(quote_char, 1)
                if end_quote_idx != -1:
                    img_path = remainder[1:end_quote_idx]
                    user_prompt = remainder[end_quote_idx+1:].strip()
            else:
                # Dynamically scan backwards for valid unquoted paths with spaces
                parts = remainder.split(" ")
                found_path = False
                for i in range(len(parts), 0, -1):
                    test_path = " ".join(parts[:i])
                    if os.path.exists(test_path):
                        img_path = test_path
                        user_prompt = " ".join(parts[i:]).strip()
                        found_path = True
                        break
                
                # Fallback if the path is genuinely invalid or typoed
                if not found_path:
                    fallback_parts = remainder.split(" ", 1)
                    img_path = fallback_parts[0]
                    user_prompt = fallback_parts[1] if len(fallback_parts) > 1 else ""
            # -------------------------
                
            img_logs = [
                ("UPLOAD", f"Detecting target: {os.path.basename(img_path)}", "bright_magenta"),
                ("MEM", "Allocating VRAM for visual matrix...", "blue"),
                ("VISION", "Analyzing pixel clusters...", "plum1"),
                ("DONE", "Visual mapping complete.", "spring_green3")
            ]
            
            for lvl, msg_text, col in img_logs:
                add_log(lvl, msg_text, col)
                ui_layout["terminal"].update(get_terminal_content(is_running=True))
                render_ui(ui_layout)
                time.sleep(0.15)
            
            if os.path.exists(img_path):
                base_resp = f"🖼️ Image loaded: `{os.path.basename(img_path)}`."
                if user_prompt:
                    base_resp += f"\nProcessed your prompt: '{user_prompt}'."
                else:
                    base_resp += "\nWhat would you like me to do with this image?"
                final_response = base_resp
            else:
                add_log("ERROR", "File not found.", "red")
                ui_layout["terminal"].update(get_terminal_content(is_running=False))
                render_ui(ui_layout)
                final_response = f"I couldn't locate the image at `{img_path}`. If the path has spaces and is incorrect, try wrapping it in quotes."
        
        else:
            text_logs = [
                ("SCAN", "Parsing NLP token matrix...", "bright_blue"),
                ("LOAD", "Querying contextual memory...", "magenta"),
                ("NET", "Routing through neural pathways...", "cyan"),
                ("COMPUTE", "Synthesizing response vectors...", "plum1"),
                ("DONE", "Output stream ready.", "spring_green3")
            ]
            
            for lvl, msg_text, col in text_logs:
                add_log(lvl, msg_text, col)
                ui_layout["terminal"].update(get_terminal_content(is_running=True))
                render_ui(ui_layout)
                time.sleep(0.15) 
            
            responses = [
                "I've processed your request successfully.",
                "That sounds like a great idea. I've updated the workspace context.",
                "Executing the parameters you specified. Check the logs for details.",
                "Analyzing... everything looks nominal on my end."
            ]
            final_response = random.choice(responses)

        if final_response:
            chat_history.append({"role": "assistant", "content": final_response, "type": "text"})

def main():
    sys.stdout.write("\033[?1049h")
    sys.stdout.flush()
    try:
        run_app()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?1049l")
        sys.stdout.flush()
        console.print("[bold green]Shutting down Vibe Studio... Goodbye![/]")

if __name__ == "__main__":
    main()