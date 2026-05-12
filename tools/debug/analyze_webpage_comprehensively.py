import json
import base64
from langchain_core.tools import tool
from playwright.sync_api import sync_playwright

@tool
def analyze_webpage_comprehensively(url: str) -> str:
    """
    # Tool: Analyze Webpage Comprehensively

    ## Overview
    Fetches the accessibility tree snapshot, a visual screenshot (base64), and browser logs
    of a webpage in a single browser session. Fully supports Single Page
    Applications (React, Angular, Vue) by waiting for network idle states.
    """
    logs = {
        "console_messages": [],
        "page_errors": []
    }

    try:
        with sync_playwright() as p:
            # Launch browser in headless mode for better compatibility
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # --- 1. Setup Log Listeners ---
            def on_console(msg):
                logs["console_messages"].append({
                    "type": msg.type,
                    "text": msg.text
                })

            def on_page_error(err):
                logs["page_errors"].append(err.message)

            page.on("console", on_console)
            page.on("pageerror", on_page_error)

            # --- 2. Navigate and Wait for SPA to Render ---
            # wait_until="networkidle" is what makes this work for React/Angular
            page.goto(url, wait_until="networkidle", timeout=30000)

            # A hard wait to allow you to see it, and for CSS/JS animations to settle
            page.wait_for_timeout(2000)

            # --- 3. Extract Data ---
            # Extract the accessibility tree using aria_snapshot() (Returns a YAML string)
            accessibility_tree = page.locator("body").aria_snapshot()

            screenshot_bytes = page.screenshot(full_page=True)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            browser.close()

            # --- 4. Construct Final Response ---
            comprehensive_result = {
                "url": url,
                "status": "success",
                "data": {
                    "accessibility_snapshot": accessibility_tree,
                    "screenshot_data": screenshot_b64,
                    "browser_logs": logs
                }
            }

            print(f"[OK] Successfully analyzed webpage: {url}")
            return json.dumps(comprehensive_result)

    except Exception as e:
        error_result = {
            "url": url,
            "status": "error",
            "error_message": str(e)
        }
        print(f"[ERROR] Failed to analyze webpage: {e}")
        return json.dumps(error_result)


def main():
    print("Starting test for 'analyze_webpage_comprehensively'...\n")

    # Testing with a site that relies on JS rendering
    test_url = "https://react.dev/"

    print(f"Invoking tool for URL: {test_url}")
    import time
    start_time = time.time()

    # Invoke the composite tool
    json_response = analyze_webpage_comprehensively.invoke({"url": test_url})

    end_time = time.time()
    print(f"\nTool execution finished in {end_time - start_time:.2f} seconds.")

    # Parse and verify the output
    parsed_response = json.loads(json_response)
    print("--- Test Results ---")

    # Truncate large data so the console output isn't flooded during testing
    if "accessibility_snapshot" in parsed_response.get("data", {}):
        snapshot_len = len(str(parsed_response["data"]["accessibility_snapshot"]))
        parsed_response["data"]["accessibility_snapshot"] = f"...[TRUNCATED SNAPSHOT - {snapshot_len} chars]..."

    if "screenshot_data" in parsed_response.get("data", {}):
        screenshot_len = len(parsed_response["data"]["screenshot_data"])
        parsed_response["data"]["screenshot_data"] = f"...[TRUNCATED BASE64 - {screenshot_len} chars]..."

    print(json.dumps(parsed_response, indent=2))

    assert parsed_response["status"] == "success", "Expected status to be 'success'"
    assert "browser_logs" in parsed_response["data"], "Missing browser logs"

    print("\n✅ All tests passed successfully!")

if __name__ == "__main__":
    main()