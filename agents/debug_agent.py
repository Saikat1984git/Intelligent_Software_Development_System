import asyncio
import os
import json
from deepagents import create_deep_agent

from agents.code_fixing_agent import code_fixing_agent
from tools.debug.analyze_webpage_comprehensively import analyze_webpage_comprehensively
from tools.terminal.execute_cli_tool import execute_cli
from tools.terminal.read_file_tool import read_file
from tools.terminal.write_file_tool import write_file
from tools.terminal.edit_file_tool import edit_file
from tools.debug.get_project_metadata import get_project_metadata

from .subagents.qa_verification_subagent import qa_verification_subagent

from langchain.agents.middleware.summarization import SummarizationMiddleware
# Models
from models.gemini_models import GEMINI_3_FLASH, GEMINI_31_PRO
from models.openai_models import GPT_4O_MINI, GPT_5_MINI_TEST, GPT_52_CHAT, GPT_51_CODEX_MINI

from deepagents.backends import LocalShellBackend

# --- Rich UI Imports ---
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel


from typing import Any, Iterable


from models.gemini_models import GEMINI_3_FLASH_LITE

# Initialize Console globally for the script
console = Console()

DEBUG_MODEL = GPT_51_CODEX_MINI
SUMMARIZATION_MODEL = GPT_4O_MINI


def get_attr_or_key(obj: Any, name: str, default=None):
    """Safely read either an attribute or a dict key."""
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def usage_to_dict(usage: Any) -> dict:
    """Normalize usage metadata from dict/object/None."""
    if not usage:
        return {}

    if isinstance(usage, dict):
        return usage

    out = {}
    for key in ("input_tokens", "output_tokens", "total_tokens"):
        value = getattr(usage, key, None)
        if value is not None:
            out[key] = value
    return out


def stringify_any(value: Any) -> str:
    """
    Convert almost anything into a safe display string.
    Handles:
    - str
    - dict
    - list / tuple / set
    - LangChain message objects
    - OpenAI structured content arrays
    - arbitrary Python objects
    """
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    # OpenAI / LangChain structured content list
    if isinstance(value, (list, tuple, set)):
        parts = []
        for item in value:
            if isinstance(item, dict):
                item_type = item.get("type")

                # Prefer plain text chunks
                if item_type == "text" and "text" in item:
                    parts.append(str(item.get("text", "")))
                    continue

                # Sometimes structured messages may contain nested content
                if "content" in item:
                    parts.append(stringify_any(item["content"]))
                    continue

                parts.append(json.dumps(item, indent=2, ensure_ascii=False, default=str))
            else:
                parts.append(stringify_any(item))

        return "\n".join(p for p in parts if p.strip())

    # Dict
    if isinstance(value, dict):
        if "text" in value and isinstance(value["text"], str):
            return value["text"]

        if "content" in value:
            return stringify_any(value["content"])

        return json.dumps(value, indent=2, ensure_ascii=False, default=str)

    # LangChain message objects often expose `.content`
    content = getattr(value, "content", None)
    if content is not None:
        return stringify_any(content)

    # Fallback for any other object
    return str(value)


def extract_messages_list(messages_update: Any) -> list:
    """
    Normalize different message container shapes into a list.
    Works with:
    - plain list
    - objects with `.value`
    - single message object
    """
    if messages_update is None:
        return []

    if hasattr(messages_update, "value"):
        messages_update = messages_update.value

    if isinstance(messages_update, list):
        return messages_update

    if isinstance(messages_update, tuple):
        return list(messages_update)

    # Sometimes a single message gets returned
    return [messages_update]


def extract_tool_calls(message: Any) -> list:
    """
    Normalize tool calls from dict/object/message.
    Returns a list of dict-like tool calls.
    """
    tool_calls = get_attr_or_key(message, "tool_calls", None)
    if not tool_calls:
        return []

    if isinstance(tool_calls, list):
        return tool_calls

    return [tool_calls]


def safe_latest_message_content(message: Any) -> str:
    """
    Extract a safe printable content string from any message shape.
    """
    content = get_attr_or_key(message, "content", None)
    if content is not None:
        return stringify_any(content)

    # Some providers place text-like output in other fields
    for field in ("text", "output_text", "message", "body"):
        val = get_attr_or_key(message, field, None)
        if val is not None:
            return stringify_any(val)

    return stringify_any(message)




# 2. Configure the Summarization Middleware
summarization = SummarizationMiddleware(
    model=SUMMARIZATION_MODEL,
    
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
  
    system_prompt = f"""
You are an expert autonomous full-stack execution, debugging, and QA remediation agent.

You are operating on this ABSOLUTE ROOT PATH:

{root_path}

ALL file operations, Docker execution, debugging, and tool calls MUST use this root path as the source of truth.

==================================================
PRIMARY OBJECTIVE
==================================================

Your PRIMARY objective is to:

1. Build and run the application using Docker.
2. Capture and analyze runtime/build errors.
3. Iteratively debug failures.
4. Resolve QA and UI issues.
5. Continue until:
   - the application runs successfully,
   - Docker logs are clean,
   - and QA validation passes completely.

==================================================
ABSOLUTE PATH RULES (CRITICAL)
==================================================

- ALWAYS use FULL ABSOLUTE SYSTEM PATHS for EVERY tool.
- NEVER rely on relative working directories.
- NEVER assume cwd persistence between tool calls.
- NEVER pass shorthand or relative paths to tools.
- ALWAYS resolve the REAL project root path before any operation.

TOOL-SPECIFIC PATH REQUIREMENTS:
- read_file(file_path): file_path MUST be an absolute path.
- write_file(file_path, content): file_path MUST be an absolute path.
- edit_file(file_path, old_string, new_string): file_path MUST be an absolute path.
- code_fixing_agent(..., project_folder_path): project_folder_path MUST be an absolute path.

The TRUE project root path MUST directly contain:
- Dockerfile
- docker-compose.yml
- application source code

Example valid absolute path:

D:\\Development\\new_vibe_code\\generated\\latest_2026-05-06_14-10-43\\retro-rusty-scientific-calculator

Passing incorrect or relative paths to ANY tool is considered a CRITICAL execution failure.

==================================================
AVAILABLE TOOLS
==================================================

1. execute_cli
   - Run Docker commands ONLY.
   - Capture stdout/stderr logs.

2. code_fixing_agent
   - MANDATORY tool for ALL application code fixes.
   - Responsible for:
       - runtime crashes
       - build failures
       - Angular/React/Vue errors
       - backend failures
       - logic bugs
       - API issues
       - dependency injection issues
       - QA failures
       - rendering problems
       - TypeScript/Python/Java/etc errors

3. read_file
   - Read files ONLY when absolutely required.

4. edit_file
   - Use for precise, targeted string replacements in infrastructure/configuration files.
   - Allowed ONLY for: Dockerfile, docker-compose.yml, nginx.conf, .env, deployment configs.
   - NOT allowed: application source code.

5. write_file
   - Use for completely overwriting infrastructure/configuration files.
   - Allowed ONLY for: Dockerfile, docker-compose.yml, nginx.conf, .env, deployment configs.
   - NOT allowed: application source code.

6. qa_verification_subagent
   - Performs UI and functional validation.

7. get_project_metadata
   - Retrieve project structure ONLY if truly required.

==================================================
CORE PRINCIPLES
==================================================

- ALWAYS start with Docker execution.
- ALL execution MUST happen inside Docker.
- NEVER run the app outside Docker.
- NEVER manually fix application code yourself.
- NEVER invent file contents.
- NEVER delete files.
- TRUST <project_metadata> as the primary source of truth.
- Use log-driven debugging only.
- Minimize unnecessary tool usage.
- Always preserve project architecture.

==================================================
STRICT TOOL USAGE RULES
==================================================

--------------------------------------------------
RULE: code_fixing_agent (MANDATORY)
--------------------------------------------------

For ANY application-level issue, you MUST use:

code_fixing_agent

This includes:
- runtime crashes
- blank screens
- Angular bootstrap errors
- React rendering failures
- DI/provider issues
- backend exceptions
- API failures
- UI bugs
- QA failures
- broken functionality
- compilation failures
- missing imports/providers/modules
- logic bugs

You MUST NEVER manually rewrite application code yourself.

When calling code_fixing_agent, you MUST ALWAYS pass:

1. issue
   - COMPLETE error information including:
       - Docker logs
       - stack traces
       - QA feedback
       - browser errors
       - failing behavior
       - affected containers
       - absolute file paths
       - line numbers
       - debugging observations

2. project_folder_path
   - MUST ALWAYS be the FULL ABSOLUTE SYSTEM PATH
     to the ACTUAL project root.
   - NEVER pass relative paths.
   - NEVER pass parent generated folders unless they
     are the actual application root.

--------------------------------------------------
RULE: execute_cli
--------------------------------------------------

Use ONLY for:
- docker compose up --build
- docker build
- docker run
- docker compose logs

DO NOT use for:
- random shell exploration
- unrelated system commands

--------------------------------------------------
RULE: edit_file & write_file
--------------------------------------------------

Use ONLY for:
- Docker configs
- nginx configs
- env files
- infrastructure adjustments

DO NOT:
- modify application source code
- fix logic manually
- refactor application code

PREFERENCE:
Always prefer `edit_file` for targeted modifications. Use `write_file` ONLY if a complete file replacement is necessary. Both MUST use absolute paths.

--------------------------------------------------
RULE: qa_verification_subagent
--------------------------------------------------

ONLY execute AFTER:
- containers run successfully
- no active Docker crashes exist
- logs appear stable

If QA reports ANY failure:
- DO NOT manually fix the issue
- IMMEDIATELY pass the EXACT QA output to:
    code_fixing_agent

--------------------------------------------------
RULE: read_file & get_project_metadata
--------------------------------------------------

Use minimally.

Prefer:
- logs
- metadata context
- delegated fixing through code_fixing_agent

==================================================
MANDATORY EXECUTION LOOP
==================================================

STEP 1 — EXECUTE APPLICATION
--------------------------------------------------

FIRST ACTION MUST ALWAYS BE:

docker compose up --build

Fallback:
- docker build
- docker run

Capture COMPLETE logs.

==================================================

STEP 2 — ANALYZE FAILURES
--------------------------------------------------

Extract:
- exact error message
- stack trace
- affected container
- absolute file path
- line number
- runtime/build phase
- root symptom

==================================================

STEP 3 — CLASSIFY FAILURE
--------------------------------------------------

Determine whether the issue is:

A. Infrastructure / Docker / Config
OR
B. Application Logic / Runtime

==================================================

STEP 4 — APPLY FIX
--------------------------------------------------

IF Infrastructure Issue:
- Use `edit_file` (preferred) or `write_file` using ABSOLUTE paths.

IF Application Issue:
- IMMEDIATELY call:
    code_fixing_agent

DO NOT manually write application code.

==================================================

STEP 5 — REBUILD
--------------------------------------------------

Re-run Docker.

Verify:
- clean startup
- no container crashes
- healthy logs

==================================================

STEP 6 — QA VALIDATION
--------------------------------------------------

Run:
qa_verification_subagent

Validate:
- UI rendering
- functionality
- interactions
- expected requirements

==================================================

STEP 7 — HANDLE QA FAILURES
--------------------------------------------------

If QA reports ANY issue:
- DO NOT fix manually
- IMMEDIATELY pass EXACT QA feedback into:
    code_fixing_agent

Then:
- rebuild
- re-verify

==================================================

STEP 8 — ITERATE
--------------------------------------------------

Continue loop UNTIL:
- Docker fully stable
- zero runtime failures
- QA returns isok = True

==================================================
STOP CONDITION
==================================================

ONLY STOP WHEN:
- Application runs successfully inside Docker
- No runtime/build errors remain
- QA validation passes completely
- All containers remain stable

==================================================
ANTI-LOOP SAFEGUARDS
==================================================

- Track previously attempted fixes.
- NEVER repeat identical failed fixes.
- If stuck:
    - change debugging strategy
    - inspect logs deeper
    - verify absolute paths
    - verify metadata consistency

If code_fixing_agent fails to locate files:
- IMMEDIATELY verify:
    - absolute project path
    - actual project root
    - Dockerfile location
    - metadata path

==================================================
ENVIRONMENT CONTEXT
==================================================

<project_metadata>
{project_metadata_str}
</project_metadata>

==================================================
FINAL BEHAVIOR REQUIREMENTS
==================================================

- Docker-first execution only.
- Log-driven debugging only.
- QA-driven remediation.
- Absolute-path-safe operations across ALL tools.
- No manual application code editing.
- Delegate ALL application fixes to:
    code_fixing_agent
- Continue iterating until full success.
"""

    debug_agent = create_deep_agent(
        model = DEBUG_MODEL, 
        system_prompt= system_prompt,
        backend=file_system_backend,
        # middleware=[summarization],
        tools = [
            qa_verification_subagent,
            read_file,
            write_file,
            edit_file,
            execute_cli,
            get_project_metadata,
            code_fixing_agent
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
            if not isinstance(chunk, dict):
                continue

            for node_name, state in chunk.items():
                if not state or not isinstance(state, dict):
                    continue

                messages_update = state.get("messages")
                messages_list = extract_messages_list(messages_update)

                if not messages_list:
                    continue

                latest_message = messages_list[-1]

                # Usage tracking
                usage = usage_to_dict(get_attr_or_key(latest_message, "usage_metadata", None))
                if usage:
                    current_context_tokens = int(usage.get("input_tokens", 0) or 0)
                    total_input_tokens += int(usage.get("input_tokens", 0) or 0)
                    total_output_tokens += int(usage.get("output_tokens", 0) or 0)

                live.update(
                    generate_status_panel(
                        node=str(node_name),
                        current_context=current_context_tokens,
                        total_in=total_input_tokens,
                        total_out=total_output_tokens,
                    )
                )

                # Tool calls
                tool_calls = extract_tool_calls(latest_message)
                if tool_calls:
                    for tool in tool_calls:
                        tool_name = get_attr_or_key(tool, "name", "unknown_tool")
                        tool_args = get_attr_or_key(tool, "args", {})

                        args_str = stringify_any(tool_args)
                        syntax = Syntax(args_str, "json", theme="monokai", line_numbers=False, word_wrap=True)
                        tool_panel = Panel(
                            syntax,
                            title=f"🔧 Tool Call: {tool_name}",
                            border_style="yellow",
                        )
                        console.print(tool_panel)

                # Output content
                content_text = safe_latest_message_content(latest_message)
                if content_text.strip():
                    content_panel = Panel(
                        content_text,
                        title=f"💬 Agent Output ({node_name})",
                        border_style="magenta",
                    )
                    console.print(content_panel)
                    final_content = content_text

    summary_table = Table(title="Agent Session Summary", show_header=True, header_style="bold blue")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right", style="green")

    summary_table.add_row("Final Context Size (Memory)", f"[bold magenta]{current_context_tokens:,}[/bold magenta]")
    summary_table.add_row("Total Session Input Tokens", f"{total_input_tokens:,}")
    summary_table.add_row("Total Session Output Tokens", f"{total_output_tokens:,}")
    summary_table.add_row("Grand Total", f"[bold yellow]{total_input_tokens + total_output_tokens:,}[/bold yellow]")

    console.print()
    console.print(summary_table)

    return final_content

# --- Example Usage ---
if __name__ == "__main__":    
    req = """
    Create a full-stack enterprise-style vehicle management web application inspired by classic dealership/internal ERP desktop-style systems.

## Tech Stack
### Frontend
- Angular (latest stable version)
- Angular Material + custom CSS for classic enterprise UI styling
- Reactive Forms
- Routing enabled
- Modular architecture

### Backend
- Java Spring Boot
- REST API architecture
- Spring Data JPA
- MySQL database
- DTO + Service + Repository layered architecture

---

# Application Goal

Build a vehicle enquiry and registration management application.

The application should:
1. Allow users to enter vehicle-related information in a large enterprise-style form
2. Save the data into MySQL
3. Submit the form
4. Navigate to another screen/page
5. Display submitted records in a searchable table/grid
6. Allow viewing details of a selected record

---

# UI/UX Requirements

Design the UI similar to old-school enterprise dealership systems:
- Light gray background
- Compact form fields
- Multi-panel layout
- Dense data-oriented interface
- Thin borders
- Small fonts
- Left-aligned labels
- Section/group containers
- Toolbar/menu at top
- Action buttons on right side
- Professional ERP/DMS appearance

The layout should resemble:
- Vehicle Enquiry screen
- Dealer Management System
- Inventory/Order management software
- Classic desktop-business software adapted for web

---

# Frontend Features

## Main Vehicle Entry Screen

Create sections such as:

### Vehicle Details
Fields:
- Stock Number
- VIN
- Model Code
- Model Description
- Colour
- Trim
- Registration Number
- Engine Number
- Location
- Status
- Key Number
- Dealer Comment

### Dealer Details
Fields:
- Request Number
- Dealer Name
- Delivery Point
- Dealer Status

### Shipping Details
Fields:
- Ship Name
- Voyage
- Car Number
- Wharf
- Bond Number
- Days In
- Order Number

### Delivery Details
Fields:
- Dealer ID
- Order Number
- Slip Order
- Delivery Type
- Finance Company
- Release Number

### Sale Details
Fields:
- Registration Status
- Dealer Code
- Registration Date
- Reservation Status

---

# Functional Requirements

## Form Features
- Angular Reactive Forms
- Form validation
- Required field validation
- Date pickers
- Dropdowns
- Submit button
- Reset button

## Backend API
Create REST APIs:

### POST
`/api/vehicles`
- Save vehicle data

### GET
`/api/vehicles`
- Get all vehicle records

### GET BY ID
`/api/vehicles/{id}`
- Get vehicle details

---

# Database Design

Use MySQL.

Create a `vehicles` table with appropriate columns for all fields.

Use:
- Auto increment primary key
- Proper datatypes
- Timestamp fields

---

# Second Screen

Create another Angular page:
`/vehicle-list`

Features:
- Data table/grid
- Pagination
- Search/filter
- Sort columns
- View details button

When clicking a row:
- Navigate to detail page
- Show all stored information in read-only format

---

# Backend Architecture

Use clean layered architecture:

- Controller
- Service
- Repository
- Entity
- DTO

Implement:
- Exception handling
- Validation
- CORS configuration
- API response structure

---

# Angular Architecture

Use:
- Feature modules
- Shared components
- Services for API calls
- Environment configuration
- Angular routing
- Loading indicators

---

# Additional Requirements

- Generate complete project structure
- Include MySQL configuration
- Include API integration
- Include Angular service classes
- Include entity models
- Include DTOs
- Include sample SQL schema
- Include complete CRUD-ready foundation
- Use enterprise coding standards
- Keep the UI responsive but desktop-oriented
- Use reusable components
- Add mock sample data

---

# Styling Instructions

The design should imitate:
- Classic enterprise desktop systems
- ERP software
- Vehicle dealership management systems
- Dense information dashboards

Visual characteristics:
- Gray panels
- Small rectangular inputs
- Blue action buttons
- Compact spacing
- Multi-column layout
- Thin separators
- Minimal animations
- High information density

---

# Expected Output

Generate:
1. Angular frontend code
2. Spring Boot backend code
3. MySQL schema
4. REST API integration
5. Routing setup
6. Complete form screen
7. Listing screen
8. Detail screen
9. Folder structure
10. Setup instructions

The final result should look like a real-world dealership management enterprise application.
"""

    prev_out = """{'requirements': '\nCreate a full-stack enterprise-style vehicle management web application inspired by classic dealership/internal ERP desktop-style systems.\n\n## Tech Stack\n### Frontend\n- Angular      │
│ (latest stable version)\n- Angular Material + custom CSS for classic enterprise UI styling\n- Reactive Forms\n- Routing enabled\n- Modular architecture\n\n### Backend\n- Java Spring Boot\n- REST API        │
│ architecture\n- Spring Data JPA\n- MySQL database\n- DTO + Service + Repository layered architecture\n\n---\n\n# Application Goal\n\nBuild a vehicle enquiry and registration management application.\n\nThe  │
│ application should:\n1. Allow users to enter vehicle-related information in a large enterprise-style form\n2. Save the data into MySQL\n3. Submit the form\n4. Navigate to another screen/page\n5. Display    │
│ submitted records in a searchable table/grid\n6. Allow viewing details of a selected record\n\n---\n\n# UI/UX Requirements\n\nDesign the UI similar to old-school enterprise dealership systems:\n- Light     │
│ gray background\n- Compact form fields\n- Multi-panel layout\n- Dense data-oriented interface\n- Thin borders\n- Small fonts\n- Left-aligned labels\n- Section/group containers\n- Toolbar/menu at top\n-     │
│ Action buttons on right side\n- Professional ERP/DMS appearance\n\nThe layout should resemble:\n- Vehicle Enquiry screen\n- Dealer Management System\n- Inventory/Order management software\n- Classic        │
│ desktop-business software adapted for web\n\n---\n\n# Frontend Features\n\n## Main Vehicle Entry Screen\n\nCreate sections such as:\n\n### Vehicle Details\nFields:\n- Stock Number\n- VIN\n- Model Code\n-   │
│ Model Description\n- Colour\n- Trim\n- Registration Number\n- Engine Number\n- Location\n- Status\n- Key Number\n- Dealer Comment\n\n### Dealer Details\nFields:\n- Request Number\n- Dealer Name\n- Delivery │
│ Point\n- Dealer Status\n\n### Shipping Details\nFields:\n- Ship Name\n- Voyage\n- Car Number\n- Wharf\n- Bond Number\n- Days In\n- Order Number\n\n### Delivery Details\nFields:\n- Dealer ID\n- Order        │
│ Number\n- Slip Order\n- Delivery Type\n- Finance Company\n- Release Number\n\n### Sale Details\nFields:\n- Registration Status\n- Dealer Code\n- Registration Date\n- Reservation Status\n\n---\n\n#          │
│ Functional Requirements\n\n## Form Features\n- Angular Reactive Forms\n- Form validation\n- Required field validation\n- Date pickers\n- Dropdowns\n- Submit button\n- Reset button\n\n## Backend API\nCreate │
│ REST APIs:\n\n### POST\n`/api/vehicles`\n- Save vehicle data\n\n### GET\n`/api/vehicles`\n- Get all vehicle records\n\n### GET BY ID\n`/api/vehicles/{id}`\n- Get vehicle details\n\n---\n\n# Database        │
│ Design\n\nUse MySQL.\n\nCreate a `vehicles` table with appropriate columns for all fields.\n\nUse:\n- Auto increment primary key\n- Proper datatypes\n- Timestamp fields\n\n---\n\n# Second Screen\n\nCreate  │
│ another Angular page:\n`/vehicle-list`\n\nFeatures:\n- Data table/grid\n- Pagination\n- Search/filter\n- Sort columns\n- View details button\n\nWhen clicking a row:\n- Navigate to detail page\n- Show all   │
│ stored information in read-only format\n\n---\n\n# Backend Architecture\n\nUse clean layered architecture:\n\n- Controller\n- Service\n- Repository\n- Entity\n- DTO\n\nImplement:\n- Exception handling\n-   │
│ Validation\n- CORS configuration\n- API response structure\n\n---\n\n# Angular Architecture\n\nUse:\n- Feature modules\n- Shared components\n- Services for API calls\n- Environment configuration\n- Angular │
│ routing\n- Loading indicators\n\n---\n\n# Additional Requirements\n\n- Generate complete project structure\n- Include MySQL configuration\n- Include API integration\n- Include Angular service classes\n-    │
│ Include entity models\n- Include DTOs\n- Include sample SQL schema\n- Include complete CRUD-ready foundation\n- Use enterprise coding standards\n- Keep the UI responsive but desktop-oriented\n- Use         │
│ reusable components\n- Add mock sample data\n\n---\n\n# Styling Instructions\n\nThe design should imitate:\n- Classic enterprise desktop systems\n- ERP software\n- Vehicle dealership management systems\n-  │
│ Dense information dashboards\n\nVisual characteristics:\n- Gray panels\n- Small rectangular inputs\n- Blue action buttons\n- Compact spacing\n- Multi-column layout\n- Thin separators\n- Minimal             │
│ animations\n- High information density\n\n---\n\n# Expected Output\n\nGenerate:\n1. Angular frontend code\n2. Spring Boot backend code\n3. MySQL schema\n4. REST API integration\n5. Routing setup\n6.        │
│ Complete form screen\n7. Listing screen\n8. Detail screen\n9. Folder structure\n10. Setup instructions\n\nThe final result should look like a real-world dealership management enterprise                     │
│ application.\n\n\n', 'skills': None, 'skills_text': None, 'status': 'Succeded', 'execution_log': None, 'metadata_file': None, 'file_paths': None, 'project_structure': None, 'agent_summary': 'Summary of     │
│ Codebase Generation:\nBased on the original requirements and the execution log, here is a summary of the codebase generation task:\n\n### **Project Overview**\nThe goal was to develop a full-stack,         │
│ enterprise-grade Vehicle Management System with a "classic ERP" aesthetic. The application facilitates vehicle enquiry, registration, and inventory management using a dense, information-heavy UI typical of │
│ dealership management systems (DMS).\n\n### **Accomplishments**\nThe system successfully generated a complete, multi-tier architecture consisting of **44 files** across the following layers:\n\n#### **1.   │
│ Backend (Java Spring Boot)**\n- **Architecture:** Implemented a clean DTO-Service-Repository-Entity layered architecture.\n- **Key Components:**\n    - `VehicleController`: REST endpoints for CRUD          │
│ operations (`/api/vehicles`).\n    - `VehicleService` & `VehicleRepository`: Business logic and Spring Data JPA integration.\n    - `Vehicle` Entity & `VehicleDTO`: Comprehensive data mapping for all 30+   │
│ required fields (Stock No, VIN, Shipping details, etc.).\n    - **Configuration:** Global exception handling, CORS configuration for frontend integration, and MySQL database settings via                    │
│ `application.yml`.\n\n#### **2. Frontend (Angular & Material)**\n- **UI/UX:** Created a "classic desktop" look using Angular Material with custom CSS for compact form fields, gray panels, and high-density  │
│ layouts.\n- **Modular Design:** \n    - `VehicleModule`: Encapsulates the vehicle feature set.\n    - **Components:** \n        - `VehicleEntryComponent`: A complex Reactive Form with multi-section panels  │
│ (Vehicle, Dealer, Shipping, Delivery, and Sale details).\n        - `VehicleListComponent`: A searchable, sortable data grid with pagination.\n        - `VehicleDetailComponent`: A read-only view for       │
│ record inspection.\n- **State Management:** Integrated `VehicleService` for API communication and environment-specific configurations.\n\n#### **3. Infrastructure & Database**\n- **Database:** MySQL schema │
│ generation including a `data.sql` file for mock sample data.\n- **Containerization:** Generated `Dockerlines` for both frontend and backend, along with a `docker-compose.yml` for full-stack                 │
│ orchestration.\n- **Documentation:** Provided a `README.md` and `.env.example` for setup and deployment.\n\n### **Execution Highlights**\n- **Success Rate:** **100% (44/44 files generated)**.\n-            │
│ **Execution Flow:** The generation followed a logical 5-level dependency order, ensuring core configurations (Level 0) were established before complex feature modules (Level 4).\n- **Skills Utilized:** The │
│ AI leveraged specialized skills for Docker orchestration and environment configuration to ensure the enterprise application is deployment-ready.\n- **Errors:** No errors were encountered during the file    │
│ generation or structure resolution phases.\n\n### **Final Deliverable**\nThe resulting codebase provides a production-ready foundation for a Vehicle ERP, featuring a robust backend API and a specialized,   │
│ high-density Angular frontend tailored for professional dealership operations.', 'error': None}  """
    root_path = "D:/Development/new_vibe_code/generated/latest_2026-05-07_09-44-03"
    try:
        os.chdir(root_path)
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Path not found: {root_path}")
        exit(1)

    final_result = asyncio.run(run_debugging_agent(req, prev_out, root_path))
    
    console.print(Panel(final_result, title="[bold green]=== Execution Complete ===[/bold green]", border_style="green"))