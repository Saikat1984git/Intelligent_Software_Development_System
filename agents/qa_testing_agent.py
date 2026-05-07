import asyncio
import os
import json
import datetime
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# LangChain Imports
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from models.openai_models import GPT_5_MINI_TEST

# Terminal Formatting
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()

AGENT_LLM = GPT_5_MINI_TEST # Standard fast model

def initialize_summarize_file():
    """Sets up the TESTRESULT.md file with a fresh header."""
    header = (
        "# 🧪 Automated QA Execution Summary\n"
        f"**Date Executed:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "**Environment:** Playwright UI MCP\n\n"
        "---\n\n"
        "## 📜 Execution Logs\n\n"
    )
    with open("TESTRESULT.md", "w", encoding="utf-8") as f:
        f.write(header)

def log_task_step(task_name: str, status: str, details: str):
    """Appends the real-time result of an executed task to TESTRESULT.md."""
    icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⛔"
    entry = f"### {icon} {task_name}\n- **Status:** {status}\n- **Execution Details & Debug Log:**\n  {details}\n\n"
    with open("TESTRESULT.md", "a", encoding="utf-8") as f:
        f.write(entry)

def append_final_qa_report(stats_dict, all_tasks_log):
    """Generates a professional QA summary block at the end of the markdown file."""
    total = stats_dict['passed'] + stats_dict['failed'] + stats_dict['blocked']
    
    report = (
        "---\n\n"
        "## 📊 Final Execution Report\n\n"
        "| Metric | Count |\n"
        "| :--- | :--- |\n"
        f"| 📝 **Total Tasks** | {total} |\n"
        f"| ✅ **Passed** | {stats_dict['passed']} |\n"
        f"| ❌ **Failed** | {stats_dict['failed']} |\n"
        f"| ⛔ **Blocked** | {stats_dict['blocked']} |\n\n"
        "### 📌 Task Breakdown\n"
    )
    
    for i, log in enumerate(all_tasks_log):
        icon = "✅" if log['status'] == "PASSED" else "❌" if log['status'] == "FAILED" else "⛔"
        report += f"{i+1}. {icon} **{log['task']}** - {log['status']}\n"
        
    with open("TESTRESULT.md", "a", encoding="utf-8") as f:
        f.write(report)

async def generate_todo_array(testdoc_content):
    """Phase 1: Prompts the LLM to convert the test doc into a pure JSON array of tasks."""
    prompt = f"""Read the following test document and break it down into a chronological list of high-level execution tasks.
    Group micro-steps (like filling multiple fields on the same page) into a single task string.
    
    You MUST return ONLY a valid JSON array of strings. Do not include markdown formatting, code blocks, or explanations.
    Example: ["Navigate to login and fill credentials", "Submit form and verify dashboard loads"]
    
    DOCUMENT:
    {testdoc_content}
    """
    
    console.print("[dim cyan]Generating comprehensive TODO array from document...[/dim cyan]")
    response = await AGENT_LLM.ainvoke([HumanMessage(content=prompt)])
    
    raw_text = response.content.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
        
    try:
        tasks = json.loads(raw_text.strip())
        if not isinstance(tasks, list):
            raise ValueError("Output is not a list")
        return tasks
    except Exception as e:
        console.print(f"[bold red]Failed to parse TODO array. Defaulting to single task. Error: {e}[/bold red]")
        return ["Execute all steps in the test document sequentially."]

async def run_testing_agent(master_prompt, testdoc_content):
    initialize_summarize_file()
    
    # 1. Generate the Array
    tasks = await generate_todo_array(testdoc_content)
    
    table = Table(title="📋 Python TODO Array Tracker", show_lines=True)
    table.add_column("Index", style="bold")
    table.add_column("Task to Execute")
    for i, t in enumerate(tasks):
        table.add_row(str(i+1), t)
    console.print(table)
    console.print("\n")

    # Tracking metrics for the final report
    execution_stats = {"passed": 0, "failed": 0, "blocked": 0}
    all_tasks_log = []

    # 2. Setup MCP and Tools
    server_params = StdioServerParameters(command="cmd", args=["/c", "npx", "-y", "@playwright/mcp@latest"], env=None)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()
            
            openai_tools = [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}} for t in mcp_tools.tools]
            llm_with_tools = AGENT_LLM.bind_tools(openai_tools)
            
            cumulative_context = "" 
            
            # 3. THE CUSTOM PYTHON FOR LOOP
            for index, current_task in enumerate(tasks):
                console.print(Panel(f"[bold yellow]Executing Task {index+1}/{len(tasks)}:[/bold yellow] {current_task}"))
                
                sys_prompt = (
                    "You are a Playwright QA Agent executing a SINGLE step in a larger test script.\n\n"
                    "=== BACKGROUND CONTEXT (UNDERSTAND THIS, BUT DO NOT EXECUTE ALL OF IT) ===\n"
                    f"**Master Goal:** {master_prompt}\n"
                    f"**Full Test Doc:**\n{testdoc_content}\n"
                    "===========================================================================\n\n"
                    "=== PREVIOUS STEPS COMPLETED (BROWSER STATE) ===\n"
                    f"{cumulative_context if cumulative_context else 'None. Browser is freshly opened.'}\n"
                    "================================================\n\n"
                    "=== YOUR CURRENT ASSIGNED TASK ===\n"
                    f"**{current_task}**\n"
                    "==================================\n\n"
                    "INSTRUCTIONS:\n"
                    "1. Use Playwright tools to accomplish ONLY your assigned CURRENT TASK. Do not perform the next steps in the document.\n"
                    "2. If you encounter errors, use your tools to debug (e.g., inspect the accessibility tree, check URLs).\n"
                    "3. When finished, you MUST start your final output with exactly 'STATUS: PASSED', 'STATUS: FAILED', or 'STATUS: BLOCKED'.\n"
                    "4. If the status is FAILED or BLOCKED, your summary MUST include a 'Root Cause / Debug Analysis' explaining exactly what failed, what locators you tried, and what the UI state actually was."
                )
                
                messages = [SystemMessage(content=sys_prompt), HumanMessage(content="Begin executing the current task.")]
                
                task_status = "BLOCKED"
                task_details = ""
                iterations = 0
                MAX_ITERATIONS = 12 # Safety timeout to prevent infinite loops on a single broken step
                
                # Execution loop strictly for the CURRENT task
                while iterations < MAX_ITERATIONS:
                    iterations += 1
                    response = await llm_with_tools.ainvoke(messages)
                    messages.append(response)

                    if response.tool_calls:
                        for tool_call in response.tool_calls:
                            name = tool_call["name"]
                            args = tool_call["args"]
                            tool_call_id = tool_call["id"]
                            
                            console.print(f"[dim yellow]Tool Call ({iterations}/{MAX_ITERATIONS}):[/dim yellow] {name} {json.dumps(args)}")
                            try:
                                result = await session.call_tool(name, args)
                                messages.append(ToolMessage(tool_call_id=tool_call_id, name=name, content=str(result.content)[:10000]))
                            except Exception as e:
                                console.print(f"[bold red]Tool Error:[/bold red] {e}")
                                messages.append(ToolMessage(tool_call_id=tool_call_id, name=name, content=f"Tool Execution Error: {e}. Please debug this failure."))
                    else:
                        # Agent has finished the task
                        final_text = response.content
                        upper_text = final_text.upper()
                        
                        if "STATUS: PASSED" in upper_text:
                            task_status = "PASSED"
                        elif "STATUS: FAILED" in upper_text:
                            task_status = "FAILED"
                        elif "STATUS: BLOCKED" in upper_text:
                            task_status = "BLOCKED"
                        else:
                            # Fallback if AI forgets the strict prefix
                            task_status = "FAILED" 
                            final_text = "STATUS: FAILED (Agent forgot to provide explicit status prefix) - " + final_text
                        
                        # Strip the prefix for cleaner logging
                        task_details = final_text.replace("STATUS: PASSED", "").replace("STATUS: FAILED", "").replace("STATUS: BLOCKED", "").strip()
                        console.print(f"[bold green]Task Concluded:[/bold green] {task_status}")
                        break 
                
                # Safety timeout check
                if iterations >= MAX_ITERATIONS:
                    task_status = "FAILED"
                    task_details = "Agent hit the maximum iteration limit (12 tool calls) and was timed out. It likely got stuck in an infinite loop trying to find a locator."
                    console.print("[bold red]Task timed out to prevent infinite loop.[/bold red]")

                # Record stats
                if task_status == "PASSED": execution_stats["passed"] += 1
                elif task_status == "FAILED": execution_stats["failed"] += 1
                else: execution_stats["blocked"] += 1
                
                all_tasks_log.append({"task": current_task, "status": task_status})

                # Log the result
                log_task_step(current_task, task_status, task_details)
                
                # Update cumulative context so the NEXT iteration knows where it is
                cumulative_context += f"- Phase '{current_task}' finished with status: {task_status}.\n"
                
            # 4. Generate the Final Report
            append_final_qa_report(execution_stats, all_tasks_log)
            console.print(Panel("[bold green]All tasks completed. Final execution summary appended to TESTRESULT.md.[/bold green]"))

def load_doc(filepath="TESTDOC.md"):
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            f.write("1. Open [https://example.com](https://example.com)\n2. Verify the heading contains 'Example'.\n3. Click a button that doesn't exist to test failure.")
    with open(filepath, "r") as f:
        return f.read()



def qa_testing_agent(file_path: str):
    """
    Load a test document from file and run the testing agent.

    Args:
        file_path (str): Path to the test document
    """
    master_prompt = (
        "Test the website based on the TESTDOC.md instructions, executing each step sequentially,"
    )
    test_file_path = (
        os.path.join(file_path, "TESTDOC.md")
        if os.path.isdir(file_path)
        else file_path
    )
    testdoc_content = load_doc(test_file_path)

    asyncio.run(
        run_testing_agent(
            master_prompt,
            testdoc_content
        )
    )

def qa_testing_with_requirements( file_path:str ,requirements: str):
    """
    Run the QA testing agent with a given requirements string.

    Args:
        requirements (str): The user requirements to test against
    """
    master_prompt = (
        f"Test the website based on the Given requirements, executing each step sequentially"
    )
    testdoc_content = f"Testing Requirements :{requirements}"

    asyncio.run(
        run_testing_agent(
            master_prompt,
            testdoc_content
        ))


if __name__ == "__main__":
    qa_testing_agent(
        "D:/Development/new_vibe_code/generated/latest_2026-05-07_10-43-55"
    )