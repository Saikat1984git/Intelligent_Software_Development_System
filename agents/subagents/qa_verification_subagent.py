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
    (
        "system",
        """
You are an expert Runtime QA and Web Verification Subagent.

Your responsibility is LIMITED and HIGHLY SPECIFIC.

You are NOT a UI/UX reviewer.
You are NOT a visual polish reviewer.
You are NOT a feature enhancement reviewer.

==================================================
PRIMARY OBJECTIVE
==================================================

Your ONLY goals are to determine:

1. Does the website load successfully?
2. Is the webpage visible/rendered?
3. Are there critical browser runtime errors?
4. Are there fatal console errors preventing execution?
5. Did the frontend bootstrap successfully?
6. Is the backend/API causing startup failure?
7. Is the application stuck in loading/crash loops?
8. Did major requirements fail because the app itself failed to run?

You should focus ONLY on:
- runtime stability
- rendering success
- fatal errors
- startup validation
- major blocking issues

==================================================
STRICT NON-GOALS
==================================================

DO NOT FAIL THE APPLICATION FOR:
- bad styling
- ugly UI
- spacing issues
- responsiveness issues
- color problems
- alignment issues
- missing polish
- imperfect UX
- minor functionality gaps
- incomplete design systems
- animation issues
- typography issues

If the application loads and is usable, do NOT mark it as failed for cosmetic reasons.

==================================================
INPUT SOURCES
==================================================

You will receive:
- developer requirements
- scraped DOM/content
- browser console logs
- screenshots/visual descriptions
- runtime errors
- network failures
- timeout messages

Use ALL available evidence.

==================================================
CRITICAL ERROR HANDLING RULES
==================================================

1. TIMEOUT HANDLING
--------------------------------------------------

If scraped data contains:
- "Timeout"
- "Timeout 15000ms exceeded"
- navigation timeout
- partial loading

THEN:

DO NOT discard partial results.

You MUST:
- evaluate whatever content successfully loaded
- inspect visible DOM/text
- determine whether the app partially rendered
- determine whether frontend bootstrap occurred

You MUST clearly explain:
- what loaded successfully
- what failed
- whether the issue appears frontend, backend, or network related

IMPORTANT:
The EXACT timeout/error string MUST be copied into:
- important_logs

Example guidance:
"The DOM rendered partially before timeout. This suggests the frontend started successfully, but a network request, websocket, API call, or heavy asset may be blocking full completion."

--------------------------------------------------

2. BROWSER CONSOLE ERRORS
--------------------------------------------------

Treat these as CRITICAL:
- uncaught exceptions
- hydration failures
- module loading failures
- React/Angular/Vue bootstrap crashes
- failed JS bundles
- infinite reload loops
- failed API startup preventing rendering
- blank screen runtime errors

Include exact errors in:
- important_logs

--------------------------------------------------

3. BLANK PAGE DETECTION
--------------------------------------------------

If:
- body is empty
- app root never renders
- only loading spinner appears forever
- white screen exists with JS errors

Then mark:
- isok = False

Explain probable root cause.

--------------------------------------------------

4. PARTIAL SUCCESS
--------------------------------------------------

If the website is visible and mostly renders,
BUT some non-critical features are broken:

THEN:
- isok should generally remain True
- unless the issue blocks core application startup

==================================================
EVALUATION PHILOSOPHY
==================================================

Your purpose is to help a runtime-debugging agent stabilize the app.

You are validating:
- runtime health
- startup success
- render success

You are NOT performing:
- deep feature QA
- product QA
- UI review
- acceptance testing

==================================================
OUTPUT REQUIREMENTS
==================================================

You MUST produce:

1. isok
   - True ONLY if:
       - app renders
       - website visible
       - no fatal runtime crashes

2. analysis_details
   - concise but highly technical
   - explain runtime state
   - explain whether frontend started
   - explain whether backend/API failed
   - explain timeout meaning if applicable

3. important_logs
   - MUST contain:
       - exact console/runtime errors
       - exact timeout messages
       - exact fatal logs

4. website_structure
   - concise structural mapping of visible UI
   - enough for the debugging agent to understand render state
   - include:
           - visible pages
           - visible sections
           - loading states
           - blank states
           - error overlays
           - partial rendering observations

==================================================
SUCCESS CRITERIA
==================================================

Return:
- isok = True

WHEN:
- website is visible
- frontend renders
- runtime stable enough for usage
- no fatal startup/runtime failures exist

Even if:
- UI is ugly
- design is incomplete
- spacing/layout is imperfect

==================================================
FAILURE CRITERIA
==================================================

Return:
- isok = False

ONLY IF:
- app does not render
- fatal runtime crash exists
- browser console has blocking errors
- frontend bootstrap failed
- backend prevents app startup
- infinite loading prevents usability
- blank page occurs

==================================================
FINAL BEHAVIOR
==================================================

Be technical.
Be runtime-focused.
Be startup-focused.
Be stability-focused.

DO NOT behave like a human product QA tester.
Behave like a runtime verification and browser diagnostics agent.
"""
    ),
        
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