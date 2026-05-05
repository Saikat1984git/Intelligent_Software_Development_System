import os
import json
from typing import Dict, Any

from rich.console import Console
from agents.states.CodebaseState import CodebaseState
from models.gemini_models import GEMINI_31_PRO, GEMINI_3_FLASH
from utils.extract_text_from_response import extract_text_from_response

# Import your terminal tools
from tools.terminal.execute_cli_tool import execute_cli
from tools.terminal.read_file_tool import read_file
from tools.terminal.write_file_tool import write_file

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from utils.generate_tree import generate_tree

console = Console()

def execute_skill_scripts_node(state: CodebaseState) -> Dict[str, Any]:
    """
    LangGraph Node: Executes initialization scripts, CLI commands, and boilerplate 
    setup step-by-step to ensure atomic retries on failure.
    """
    print("INFO: STARTING: Execute Skill Scripts Node")

    # 1. Extract inputs from State
    requirements = state.get("requirements", "")
    project_structure = state.get("project_structure", {})
    skills_raw = state.get("skills_text", [])
    history = state.get("execution_log", [])

    execution_logs = []
    execution_logs.append(" STARTING: `Execute Skill Scripts` agent Node")
    
    skills_context = ""
    if isinstance(skills_raw, dict):
        skills_context = "\n\n".join([f"--- SKILL FILE: {k} ---\n{v}" for k, v in skills_raw.items()])
    elif isinstance(skills_raw, list):
        skills_context = "\n\n".join(skills_raw)

    llm = GEMINI_31_PRO
    small_llm = GEMINI_3_FLASH

    current_tree=generate_tree(".")
    print(f"Current Project Directory Tree:\n{current_tree}")
    execution_logs.append(f"Current project structure:\n{current_tree}")

    # 2. System Prompt: Enforce ONE step at a time
    system_prompt = f"""You are an expert technical lead orchestrating a project workspace.

### PROJECT REQUIREMENTS
{requirements}

### SKILL FILES / GUIDELINES
{skills_context if skills_context else "No specific skills provided."}

### PROJECT STRUCTURE
{current_tree}

### STATUS: READ-ONLY STRUCTURE
The project directory structure and all necessary source files have **already been created**. 
- Your sole focus is to execute scripts given in the skills or any standard setup commands needed to initialize the project.
- You do  not need to run the project 
### INSTRUCTIONS
You operate in a strict step-by-step loop. 
1. Output EXACTLY ONE execution step (e.g., running a scrip). Do NOT output a list of steps.
2. I will execute it and return the result or error.
3. If it SUCCEEDS, output the NEXT logical execution step.
4. If it FAILS, analyze the error and output a FIX for that specific execution step. 
5. When all needed execution steps are finished, or if no further action is needed, output the "DONE" tool.

### OUTPUT FORMAT
Return a JSON array containing ONLY ONE execution step.
Tools available: "execute_cli", "read_file", "write_file" and  "DONE". 
Example to run an existing setup script:
[ {{"tool": "execute_cli", "command": "bash scripts/setup.sh"}} ]

Example to signal completion:
[ {{"tool": "DONE"}} ]
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Start the setup process. Provide the very FIRST step as a JSON array. If nothing is needed, output the DONE tool.")
    ]
    
    if history:
        messages.insert(1, AIMessage(content=f"Previous Context:\n{chr(10).join(history)}"))

    # Increased iterations since we are doing 1 step per loop
    MAX_ITERATIONS = 15 
    iteration = 0

    # 3. The Step-by-Step Loop
    while iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"\n--- Iteration {iteration}/{MAX_ITERATIONS} ---")
        
        try:
            response = small_llm.invoke(messages)
            raw_text = extract_text_from_response(response).strip()

            if raw_text.startswith("```"):
                start_idx = raw_text.find("[")
                end_idx = raw_text.rfind("]")
                if start_idx != -1 and end_idx != -1:
                    raw_text = raw_text[start_idx:end_idx+1]

            execution_plan = json.loads(raw_text)
            messages.append(AIMessage(content=raw_text))

            if not execution_plan:
                break

            # Grab only the first step to enforce one-at-a-time execution
            step = execution_plan[0] 
            tool_name = step.get("tool")
            step_result_log = ""

            execution_logs.append(f"Iteration {iteration}: Executed tool: {tool_name}")
            
            # 4. Execute the Single Step
            if tool_name == "DONE":
                print("INFO: LLM signaled all setup is complete.")
                break
            
            elif tool_name == "execute_cli":
                command = step.get("command")
                print(f"EXECUTE: {command}")
                result = execute_cli.invoke({"command": command}) 
                step_result_log = f"Command: {command}\nResult/Output:\n{result}"
                print(step_result_log)  
                execution_logs.append(step_result_log)
                
            elif tool_name == "write_file":
                filepath = step.get("path")
                content = step.get("content")
                print(f"EXECUTE: Writing -> {filepath}")
                result = write_file.invoke({"file_path": filepath, "content": content})
                step_result_log = f"Write File: {filepath}\nResult:\n{result}"
                print(step_result_log) 
                execution_logs.append(step_result_log)
                
            elif tool_name == "read_file":
                filepath = step.get("path")
                print(f"EXECUTE: Reading -> {filepath}")
                result = read_file.invoke({"file_path": filepath})
                step_result_log = f"Read File: {filepath}\nResult:\n{result}"
                print(step_result_log) 
                execution_logs.append(step_result_log)
                
            else:
                step_result_log = f"WARNING: Unknown tool: {tool_name}"
                print(step_result_log)

            # 5. Feed the exact result of this single step back to the LLM
            feedback_content = f"Result of your step:\n{step_result_log}\n\nIf this was an error, retry with a fix. If successful, provide the NEXT step or DONE."
            execution_logs.append(step_result_log)
            messages.append(HumanMessage(content=feedback_content))

        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON. Retrying...")
            messages.append(AIMessage(content=raw_text))
            messages.append(HumanMessage(content=f"JSON Parse Error: {e}. Ensure you output a valid JSON array containing exactly ONE object."))
            
        except Exception as e:
            error_msg = f"System error executing tool: {str(e)}"
            print(f"ERROR: {error_msg}")
            messages.append(HumanMessage(content=f"Error encountered: {error_msg}. Please fix the step and try again."))

    status = "setup_scripts_executed_successfully" if iteration < MAX_ITERATIONS else "execution_timeout"
    
    return {
        "execution_logs": history+execution_logs,
        "status": status
    }