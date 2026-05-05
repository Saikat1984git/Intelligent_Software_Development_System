import os
from urllib.parse import urlparse
from langchain_core.tools import tool
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

@tool
def capture_website_screenshot(url: str) -> str:
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
    * Returns a string confirming success and providing the absolute file path where the `.png` screenshot was saved on the local machine.

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
            
            # Generate a safe, readable filename based on the URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            safe_name = "".join([c for c in domain if c.isalpha() or c.isdigit() or c=='-']).rstrip()
            filename = f"screenshot_{safe_name}.png"
            
            # Define where to save it (current working directory)
            save_path = os.path.abspath(os.path.join(os.getcwd(), filename))
            
            # Capture the screenshot (full_page=True stitches the whole site together)
            page.screenshot(path=save_path, full_page=True)
            
            browser.close()
            
            return f"Success! Full-page screenshot of {url} captured and saved to: {save_path}"

    except PlaywrightTimeoutError:
        return f"Error: The website at {url} took too long to load (Timeout after 15 seconds)."
    except Exception as e:
        return f"An unexpected error occurred while trying to screenshot {url}: {str(e)}"