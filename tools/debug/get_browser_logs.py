import sys
import json
from langchain_core.tools import tool
from playwright.sync_api import sync_playwright


def get_browser_logs(url: str) -> str:
    """
    Fetches and returns the internal browser logs for a given URL.
    Use this tool when you need to debug a webpage, check for broken network requests, 
    read console messages, or find JavaScript errors on a specific website.
    Input should be a fully qualified URL (e.g., https://example.com).
    """
    logs = {
        "console_messages": [],
        "network_requests": [],
        "page_errors": []
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Event listeners for logs
            page.on("console", lambda msg: logs["console_messages"].append(f"[{msg.type.upper()}] {msg.text}"))
            page.on("request", lambda req: logs["network_requests"].append(f"[{req.method}] {req.url}"))
            page.on("pageerror", lambda err: logs["page_errors"].append(str(err)))

            # Navigate with a timeout so the agent doesn't hang indefinitely
            page.goto(url, wait_until="networkidle", timeout=15000)
            
            browser.close()
            
        # Return as a JSON string so the LLM can easily parse and read it
        return json.dumps(logs, indent=2)
    
    except Exception as e:
        # Return the error as a string so the agent knows what went wrong
        return f"Error fetching logs for {url}: {str(e)}"


# --- Test Executor ---
if __name__ == "__main__":
    # Default URL if none is provided via command line
    test_url = "https://www.google.com/"
    
    # Allow overriding the URL via command line arguments
    if len(sys.argv) > 1:
        test_url = sys.argv[1]

    print(f"Testing LangChain tool: {get_browser_logs.name}")
    print(f"Description: {get_browser_logs.description}")
    print(f"\nFetching logs for: {test_url}")
    print("Waiting for network idle...\n")
    
    # Test the tool using LangChain's .invoke() method
    # This simulates exactly how a LangChain Agent will call the tool
    try:
        result = get_browser_logs.invoke({"url": test_url})
        print("--- Tool Execution Successful ---")
        print("Output:")
        print(result)
    except Exception as e:
        print(f"--- Tool Execution Failed ---")
        print(f"Error: {e}")