import os
import base64
import io
from urllib.parse import urlparse
from langchain_core.tools import tool
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

import matplotlib.pyplot as plt
from PIL import Image


def capture_website_screenshot(url: str) -> dict:
    """
    # Tool: Capture Website Screenshot

    ## Overview
    Opens a headless Chromium browser, navigates to the provided URL, waits for the page to render, and captures a full-page screenshot. 

    ## When to Use This Tool
    * When you need visual confirmation of a website's layout or design.
    * When a website heavily relies on JavaScript/Canvas and standard text extraction fails.
    * If the user specifically asks to "take a picture," "screenshot," or "visually capture" a webpage.

    ## Input Parameters
    * `url` (string): The complete, fully qualified HTTP or HTTPS URL of the webpage (e.g., 'https://www.github.com').

    ## Expected Output
    * Returns a dictionary containing a success status, a mime_type ('image/png'), and the Base64-encoded image string data which can be read by Vision AI models.

    ## Limitations & Error Handling
    * **Timeouts:** Enforces a 15-second timeout. If the site is too slow, it will fail gracefully.
    * **Auth:** Cannot bypass CAPTCHAs or log into authenticated portals.
    """
    try:
        with sync_playwright() as p:
            # Launch headless browser
            browser = p.chromium.launch(headless=True)
            
            # Set a standard desktop viewport
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()
            
            # Navigate to the URL (Wait until network is mostly idle to ensure JS loads)
            page.goto(url, timeout=15000, wait_until="networkidle")
            
            # Capture the screenshot directly into memory as bytes (omit 'path' argument)
            screenshot_bytes = page.screenshot(full_page=True)
            
            # Encode the raw bytes into a Base64 string
            base64_encoded_string = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            browser.close()
            
            # Return the structured payload for the AI
            return {
                "status": "success",
                "message": f"Successfully captured full-page screenshot of {url}.",
                "mime_type": "image/png",
                "data": base64_encoded_string
            }

    except PlaywrightTimeoutError:
        return {"status": "error", "message": f"Timeout: The website at {url} took too long to load (15 seconds)."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred while capturing {url}: {str(e)}"}


def main():
    test_url = "https://www.github.com"
    print(f"Capturing screenshot of {test_url}...")

    # The tool now returns a dictionary
    result = capture_website_screenshot.invoke({"url": test_url})

    # Check if the run was successful by checking the status key
    if isinstance(result, dict) and result.get("status") == "success":
        print("Screenshot successfully captured and encoded to Base64!")
        
        # Extract the Base64 data
        base64_data = result["data"]
        
        # --- For local testing: Decode it back to an image to verify it worked ---
        image_bytes = base64.b64decode(base64_data)
        img = Image.open(io.BytesIO(image_bytes))

        plt.figure(figsize=(10, 6))
        plt.imshow(img)
        plt.axis("off")
        plt.title("Website Screenshot (Decoded from Base64)")
        plt.show()
        
    else:
        # If it timed out or failed, extract the error message
        error_msg = result.get("message") if isinstance(result, dict) else str(result)
        print(f"Screenshot process failed: {error_msg}")

if __name__ == "__main__":
    main()