from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from agents.states.CodebaseState import CodebaseState
from models.gemini_models import GEMINI_3_FLASH
from utils.extract_text_from_response import extract_text_from_response
# Assuming you have your LLM initialized somewhere above, e.g.:
# from langchain_openai import ChatOpenAI




def summarize_codebase_node(state: CodebaseState):
    # 1. Extract the variables from the state
    requirements = state.get("requirements", "No requirements provided.")
    raw_log = state.get("execution_log")
    
    # 2. Safely format the execution log (handling None or empty lists)
    if raw_log:
        execution_log_text = "\n".join(raw_log)
    else:
        execution_log_text = "No execution logs available."

    # 3. Construct the prompt
    prompt = f"""
    You are an AI assistant summarizing a codebase generation task.
    Please provide a concise summary of what was accomplished based on the original requirements and the system's execution log.
    Highlight any successful file generations, script executions, or errors encountered.

    Original Requirements:
    {requirements}

    Execution Log:
    {execution_log_text}
    """

    base_llm= GEMINI_3_FLASH
    # llm = base_llm.with_structured_output()

    # 4. Invoke the LLM
    response = base_llm.invoke(prompt)

    expected_summary = extract_text_from_response(response)

    print(f"LLM Summary Response:\n{expected_summary}")

    return {
        "agent_summary": f"Summary of Codebase Generation:\n{expected_summary}",
        "skills_text": None,
        "skills": None,
        "project_structure": None,
        "file_paths": None,
        "metadata_file": None,
        "status": "Succeded",
        "error": None,
        "execution_log": None
    }
    