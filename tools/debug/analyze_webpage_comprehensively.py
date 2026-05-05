import asyncio
import json
from langchain_core.tools import tool

# Import your base tools (adjust import paths as needed)
from .fetch_webpage_content import fetch_webpage_content
from .capture_website_screenshot import capture_website_screenshot
from .get_browser_logs import get_browser_logs  # Your new Playwright tool

@tool
async def analyze_webpage_comprehensively(url: str) -> str:
    """
    # Tool: Analyze Webpage Comprehensively
    
    ## Overview
    Fetches the clean text content, a visual screenshot, and browser logs 
    of a webpage concurrently. Use this tool when you need a complete understanding 
    of a webpage, combining what it says (text), how it looks (visual layout), 
    and how it is functioning under the hood (JS errors, network requests, logs).
    
    ## Input Parameters
    * `url` (string): The complete, fully qualified HTTP or HTTPS URL of the webpage.
    
    ## Expected Output
    * Returns a JSON formatted string containing the URL, text content, screenshot data, 
      and a structured dictionary of browser logs.
    """
    try:
        # 1. Run the synchronous functions concurrently in separate threads
        text_task = asyncio.to_thread(fetch_webpage_content, url)
        screenshot_task = asyncio.to_thread(capture_website_screenshot, url)
        logs_task = asyncio.to_thread(get_browser_logs, url)
        
        # 2. Await all tasks to finish simultaneously
        text_result, screenshot_result, logs_result_str = await asyncio.gather(
            text_task, screenshot_task, logs_task
        )
        
        # 3. Parse the JSON string from get_browser_logs back into a dict
        # This prevents escaped JSON strings ("{\"console_messages\": []}") in the final output.
        try:
            logs_data = json.loads(logs_result_str)
        except json.JSONDecodeError:
            # Fallback in case your tool caught an exception and returned a plain error string
            logs_data = {"error": logs_result_str}
        
        # 4. Construct the comprehensive JSON reply
        comprehensive_result = {
            "url": url,
            "status": "success",
            "data": {
                "text_content": text_result,
                "screenshot_data": screenshot_result,
                "browser_logs": logs_data
            }
        }
        
        return json.dumps(comprehensive_result)
        
    except Exception as e:
        # Graceful error handling
        error_result = {
            "url": url,
            "status": "error",
            "error_message": str(e)
        }
        return json.dumps(error_result)


async def main():
    print("Starting test for 'analyze_webpage_comprehensively'...\n")
    test_url = "https://www.google.com/"
    
    print("Invoking composite tool...")
    start_time = asyncio.get_event_loop().time()
    
    # Invoke the composite tool
    json_response = await analyze_webpage_comprehensively.ainvoke({"url": test_url})
    
    end_time = asyncio.get_event_loop().time()
    
    print(f"\nTool execution finished in {end_time - start_time:.2f} seconds.")
    
    # Parse and verify the output
    parsed_response = json.loads(json_response)
    print("--- Test Results ---")
    
    # We truncate text and screenshot data so the console output isn't flooded during testing
    if "text_content" in parsed_response.get("data", {}):
        parsed_response["data"]["text_content"] = "...[TRUNCATED]..."
    if "screenshot_data" in parsed_response.get("data", {}):
        parsed_response["data"]["screenshot_data"] = "...[TRUNCATED BASE64]..."
        
    print(json.dumps(parsed_response, indent=2))
    
    # Assertions
    assert parsed_response["status"] == "success", "Expected status to be 'success'"
    assert "browser_logs" in parsed_response["data"], "Missing browser logs"
    
    print("\n✅ All tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())