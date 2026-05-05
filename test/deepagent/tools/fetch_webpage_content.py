import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

@tool
def fetch_webpage_content(url: str) -> str:
    """
    # Tool: Fetch Webpage Content

    ## Overview
    Fetches, cleans, and extracts the primary text content from a provided webpage URL. 
    This tool acts as a headless GET request, retrieving the raw HTML of a page and meticulously stripping away non-essential elements (such as `<script>`, `<style>`, navigation bars, headers, and footers) to return only the clean, human-readable text. It is highly optimized to save token space.

    ## Input Parameters
    * `url` (string): The complete, fully qualified HTTP or HTTPS URL of the webpage you want to read. You MUST include the protocol (e.g., 'https://en.wikipedia.org/wiki/Python', NOT just 'en.wikipedia.org/wiki/Python').

    ## Expected Output
    * Returns a `string` containing the cleaned text of the webpage, with whitespace compressed and HTML tags removed.

    ## Error Handling & Self-Correction Context
    * **403 Forbidden / 401 Unauthorized:** If the tool returns this, the website actively blocks automated scrapers or bots. Do not retry; inform the user that the site cannot be accessed autonomously.
    * **Timeout:** The tool enforces a strict 10-second timeout. If it times out, the server is likely down or blocking your specific IP region.
    * **Empty Return:** If the tool returns a blank string or a message about enabling JavaScript, the site relies on Client-Side Rendering (CSR). You will not be able to read it with this tool.
    """
    try:
        # Standard user-agent to prevent basic anti-bot 403 Forbidden errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch the webpage with a timeout so the agent doesn't hang indefinitely
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strip out script and style elements as they are useless to the LLM
        for script_or_style in soup(['script', 'style', 'noscript', 'header', 'footer']):
            script_or_style.decompose()
            
        # Extract text and clean up excessive whitespace
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Truncate if insanely long (optional, but good for context limits)
        # return clean_text[:8000] + "... [Content Truncated]" if len(clean_text) > 8000 else clean_text
        
        return clean_text

    except requests.exceptions.Timeout:
        return f"Error: The request to {url} timed out."
    except requests.exceptions.RequestException as e:
        return f"Error fetching webpage: {str(e)}. The site might be down or blocking scrapers."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"