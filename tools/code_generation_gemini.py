import os
import json
import sys
import base64
import re
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# New SDK imports
from google import genai
from google.genai import types

try:
    from tools.file_editor import apply_file_edits
except ImportError:
    def apply_file_edits(**kwargs): return "Utils module not found. Edits skipped."

load_dotenv()

# ---------- Structured Output Schemas ----------

class FileContent(BaseModel):
    """Individual file with its rewritten content."""
    file_path: str = Field(description="The relative file path")
    content: str = Field(description="The rewritten code content")

class RewrittenFiles(BaseModel):
    """Collection of rewritten files with their new code."""
    files: List[FileContent] = Field(description="List of files with rewritten content")

# ---------- Core Tool ----------

class CodeRewriteToolGemini:
    """AI tool to rewrite code files using the new Google Gen AI SDK (v1.0+)."""

    def __init__(self, model_id: str = "gemini-2.0-flash-exp"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Initialize the Client
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

        self.system_instruction = (
            "You are an expert code refactoring assistant.\n"
            "You will receive a JSON structure containing multiple code files and a rewriting instruction.\n"
            "Your task:\n"
            "1. Analyze each file's code.\n"
            "2. Apply the requested changes according to the prompt.\n"
            "3. Return the rewritten code for each provided file.\n"
            "4. Identify and generate any new files that are necessary to fully implement the changes or improve the architecture, even if they are not present in the current project.\n"
            "5. Ensure that the rewritten code is functional, maintainable, and adheres to best practices.\n"
            "6. Asset Generation: If you need to create new image files, generate only SVG files. For all other images or media types, use external URLs instead of creating local files.\n"
            "Maintain code quality, follow best practices, and preserve functionality unless instructed otherwise."
        )

    def read_files(self, file_paths: List[str], root_path: str) -> Dict[str, str]:
        """Read content from all specified files."""
        file_contents: Dict[str, str] = {}
        for rel_path in file_paths:
            full_path = Path(root_path) / rel_path
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {full_path}")
            with open(full_path, "r", encoding="utf-8") as f:
                file_contents[rel_path] = f.read()
        return file_contents

    def structure_files_as_json(self, file_contents: Dict[str, str]) -> str:
        """Convert file contents dictionary to a JSON string."""
        structured = {
            "files": [{"file_path": p, "content": c} for p, c in file_contents.items()]
        }
        return json.dumps(structured, indent=2)

    def _process_image_input(self, b64_string: str) -> types.Part:
        """
        Converts base64 strings to a types.Part object using from_bytes.
        """
        mime_type = "image/jpeg" # Default

        # Check for Data URL format
        match = re.match(r'data:(image/[a-zA-Z]+);base64,(.+)', b64_string)
        if match:
            mime_type = match.group(1)
            b64_data = match.group(2)
        else:
            b64_data = b64_string

        try:
            image_bytes = base64.b64decode(b64_data)
            # Use the new SDK's helper to create the Part
            return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        except Exception as e:
            print(f"Error decoding base64 image: {e}")
            return None

    def _build_user_input(self,  files_json: str, prompt: str, project_content:str ) -> str:
        return (
            "Here is the current codebase structure and content in JSON format:\n\n"
            f"{project_content}\n\n"
            "Here are the files to rewrite:\n\n"
            f"{files_json}\n\n"
            "Rewriting instructions:\n"
            f"{prompt}\n\n"
            "Please rewrite the code for each file according to the instructions above.\n"
        )

    def rewrite_code(
        self,
        file_paths: List[str],
        project_content: str,
        root_path: str,
        prompt: str,
        edit_prompt_images: List[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, str]:
        """
        Main execution method using client.models.generate_content
        """

        # 1. Prepare Content
        file_contents = self.read_files(file_paths, root_path)
        files_json = self.structure_files_as_json(file_contents)
        text_prompt = self._build_user_input(files_json, prompt, project_content)

        # Build contents list (Text + Images)
        contents = [text_prompt ]


        if edit_prompt_images:
            for b64 in edit_prompt_images:
                if not b64: continue
                img_part = self._process_image_input(b64)
                if img_part:
                    contents.append(img_part)


        import json
        print("\n=== Contents to be processed ===")
        try:
            print(json.dumps(contents, indent=2, ensure_ascii=False, default=str))
        except TypeError:
            # Fallback if some objects aren't JSON-serializable
            from pprint import pprint
            pprint(contents, width=120, sort_dicts=False)
        print("=== End contents ===\n")

        print(f"Sending request to {self.model_id}...")

        # 2. Configure the Generation
        # The new SDK puts configuration in a dedicated Config object
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=self.system_instruction,
            response_mime_type="application/json",
            response_schema=RewrittenFiles, # Pass Pydantic class directly
        )

        # 3. Call the API (Streaming)
        # Note: 'contents' acts as the user message
        response_stream = self.client.models.generate_content_stream(
            model=self.model_id,
            contents=contents,
            config=config,
        )

        # 4. Stream Output
        collected_text = ""
        usage_metadata = None  # <--- Initialize a variable to hold the metadata

        print("Processing stream...")

        for chunk in response_stream:
            # Check for usage metadata (usually arrives in the final chunk)
            if chunk.usage_metadata:
                usage_metadata = chunk.usage_metadata

            # Access text
            if chunk.text:
                collected_text += chunk.text
                sys.stdout.write(chunk.text)
                sys.stdout.flush()
                print(collected_text)

        print("\n\nDone streaming.")

        # --- Print Token Usage ---
        if usage_metadata:
            print(f"Total Input Tokens: {usage_metadata.prompt_token_count}")
            print(f"Total Output Tokens: {usage_metadata.candidates_token_count}")
            print(f"Total Tokens: {usage_metadata.total_token_count}")
        else:
            print("Token usage data not available in response.")
        # -------------------------

        # 5. Parse Results
        try:
            # Clean up markdown if present (defensive coding)
            cleaned_text = collected_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            data = json.loads(cleaned_text)

            # Extract files list
            if "files" in data and isinstance(data["files"], list):
                return {f["file_path"]: f["content"] for f in data["files"]}
            else:
                raise ValueError("Output missing 'files' list.")
        except Exception as e:
            # Added basic error handling for the JSON parse
            print(f"Error parsing JSON: {e}")
            return {}


# ---------- Example usage ----------

if __name__ == "__main__":
    # Ensure GEMINI_API_KEY is set in .env
    # Recommended model for code tasks
    tool = CodeRewriteToolGemini(model_id="gemini-3-pro-preview")

    file_paths = ['src/components/PokemonCard.jsx', 'src/index.css']
    root_path = "D:/Development/vibe_edit/pokedex-react-router"

    prompt = "change the background color of cards in the main dashboard to light blue"

    if os.path.exists(root_path):
        try:
            rewritten = tool.rewrite_code(
                file_paths=file_paths,
                root_path=root_path,
                prompt=prompt,
                temperature=0.1,
            )
            print("\n=== Rewritten Files ===", rewritten.keys())

        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Skipping: Root path '{root_path}' not found.")