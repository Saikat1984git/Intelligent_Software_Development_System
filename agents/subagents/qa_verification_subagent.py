import asyncio
import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

# Assuming your composite tool and models are imported here
from models.gemini_models import GEMINI_25_PRO, GEMINI_3_FLASH, GEMINI_3_FLASH_LITE
from models.openai_models import GPT_51_CODEX_MINI, GPT_4O_MINI, GPT_52_CHAT , GPT_5_MINI_TEST

from tools.debug.analyze_webpage_comprehensively import analyze_webpage_comprehensively 


QA_SUBAGENT_MODEL = GEMINI_25_PRO # Swap with your preferred model for the QA subagent``

# ------------------------------------------------------------------
# 1. Define Output & Input Schemas
# ------------------------------------------------------------------
class VerificationResult(BaseModel):
    """Schema for the QA Subagent's response back to the main agent."""
    is_ok: bool = Field(
        description="True ONLY if the webpage meets the requirements fully and has no severe errors. False if requirements are missing or if critical timeouts/errors occurred."
    )
    website_structure: str = Field(
        description="Detailed elaboration of the website's layout, UI elements, and overall structure inferred from the HTML text and visual context. Explain what components are present and where."
    )
    analysis_details: str = Field(
        description="Comprehensive explanation of what is working, what is broken, and why. If a timeout occurred, explain how it impacts the requirements and suggest next steps for the developer agent."
    )
    important_logs: str = Field(
        description="Specific snippets of console logs, network errors, or page errors (including Playwright timeouts). write 'None' if none."
    )

class QASubagentInput(BaseModel):
    """Input arguments for the QA Verification Tool."""
    requirements: str = Field(..., description="The developer's software requirements to test against.")
    url: str = Field(..., description="The URL of the live webpage to test.")

# ------------------------------------------------------------------
# 2. The QA Subagent Tool
# ------------------------------------------------------------------
@tool("qa_verification_subagent", args_schema=QASubagentInput)
async def qa_verification_subagent(requirements: str, url: str) -> VerificationResult:
    """
    Acts as the primary Quality Assurance (QA) and visual verification subagent. 
    
    USE THIS TOOL WHEN:
    - You have written or deployed code and need to verify if the live web page actually matches the requested software requirements.
    - You need to inspect a webpage for JavaScript console errors, failing network requests, or infinite loading loops.
    - You need a detailed breakdown of a webpage's DOM structure and UI layout to figure out why a component isn't rendering correctly.

    HOW IT WORKS:
    It navigates to the provided URL and captures a comprehensive snapshot of the webpage. This includes the HTML structure, visible text, visual context, and critical browser telemetry (logs and timeouts). It then rigorously compares this live data against the provided `requirements` string to determine if the deployment was successful.

    RETURNS:
    A structured VerificationResult that gives the developer agent a clear pass/fail status (`is_ok`), a map of the UI (`website_structure`), actionable debugging advice (`analysis_details`), and specific error traces (`important_logs`) required to fix any broken code.
    """
    print(f"🤖 [QA Subagent] Initiating analysis for: {url}")
    
    # Step 1: Execute the composite tool to grab text, screenshots, and logs
    print("🤖 [QA Subagent] Fetching webpage data, screenshot, and logs...")
    try:
        tool_json_response = await analyze_webpage_comprehensively.ainvoke({"url": url})
    except Exception as e:
        # Graceful degradation: Capture the crash but format it so the LLM can still read it
        print(f"⚠️ [QA Subagent] Tool execution encountered an issue: {e}")
        tool_json_response = json.dumps({
            "status": "partial_or_failed", 
            "error_message": str(e),
            "note_to_llm": "The scraping tool threw an exception. Evaluate any partial data if present, or advise the main agent on how to handle this crash."
        })

    # Step 2: Initialize the LLM and bind the structured output schema
    llm = QA_SUBAGENT_MODEL  # Swap with your preferred model
    evaluator_llm = llm.with_structured_output(VerificationResult)
    
    # Step 3: Create the evaluation prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Software QA Subagent. 
        Your job is to compare a developer's software requirements against the actual 
        data scraped from the live webpage (text content, visual context, and browser logs).
        
        CRITICAL ERROR HANDLING INSTRUCTIONS:
        1. If the scraped data indicates a timeout (e.g., "Timeout 15000ms exceeded") or a partial load:
           - DO NOT just discard the data. Evaluate whatever HTML text or structure was successfully scraped before the timeout.
           - Clearly state in `analysis_details` that a timeout occurred. Advise the main developer agent on what this means (e.g., "The DOM loaded, but network requests timed out. The developer agent should check for heavy assets or infinite loading loops.").
        2. Ensure the exact error string (like the Playwright timeout) is passed into the `important_logs` field.
        
        Evaluate if the webpage successfully meets the requirements based on the available data.
        Map out the UI comprehensively in the `website_structure` field so the next agent understands the visual state.
        """),
        
        ("user", """
        # Original Requirements
        {requirements}
        
        # Webpage URL
        {url}
        
        # Scraped Webpage Data & Logs
        {tool_data}
        
        Analyze the data thoroughly and provide your verification result.
        """)
    ])
    
    # Step 4: Chain and invoke
    print("🤖 [QA Subagent] Evaluating data against requirements...")
    chain = prompt | evaluator_llm
    
    # This invokes the LLM inside the tool and returns the parsed Pydantic object
    result: VerificationResult = await chain.ainvoke({
        "requirements": requirements,
        "url": url,
        "tool_data": tool_json_response
    })
    
    return result

# ------------------------------------------------------------------
# 3. Test the Tool
# ------------------------------------------------------------------
async def main():
    test_requirements = """
        check of the website is showing a scientific calculator with a display and buttons for digits 0-9, basic operations (+, -, *, /), and a clear button. and theme toogle button and history of calculations. 
    """
    test_url = "http://localhost:8080/" # Replace with your local test URL
    
    print("Starting QA Subagent tool test...\n")
    
    final_report = await qa_verification_subagent.ainvoke({
        "requirements": test_requirements, 
        "url": test_url
    })
    
    print("\n--- Final Report to Main Agent ---")
    print(f"Is OK?: {final_report.is_ok}")
    print(f"\nWebsite Structure:\n{final_report.website_structure}")
    print(f"\nAnalysis Details:\n{final_report.analysis_details}")
    print(f"\nImportant Logs to Fix:\n{final_report.important_logs}")

if __name__ == "__main__":
    asyncio.run(main())