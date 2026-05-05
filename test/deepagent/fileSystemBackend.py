import os
import platform
import shutil
import sys
from datetime import datetime
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.create_project_structure_tool import create_project_structure_tool
from tools.write_file_tool import write_file_tool
from tools.debug.fetch_webpage_content import fetch_webpage_content

load_dotenv()

# --- Logging Setup ---
class TeeLogger(object):
    """Duplicates stdout/stderr to a file while keeping terminal output."""
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()  # Ensure logs are written immediately

    def flush(self):
        self.terminal.flush()
        self.log.flush()

ROOT_PATH = os.getcwd()
LOG_DIR = os.path.join(ROOT_PATH, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Generate log filename with timestamp
log_filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
log_filepath = os.path.join(LOG_DIR, log_filename)

# Redirect standard output and error to the logger
sys.stdout = TeeLogger(log_filepath)
sys.stderr = sys.stdout
# ---------------------

GEMINI_MODEL = ChatGoogleGenerativeAI(
        model="gemini-3.1-pro-preview",
        temperature=0.2,
        api_key=os.environ.get("GEMINI_API_KEY")
    )

system_info = (
    f"OS: {platform.system()}\n"
    f"Release: {platform.release()}\n"
    f"Version: {platform.version()}\n"
    f"Architecture: {platform.machine()}"
)
SYSTEM_OS = system_info
SYSTEM_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

SKILLS_DIR = f"{ROOT_PATH}/skills"
BASE_DIR = f"{ROOT_PATH}/generated"

print(f"--- Execution Started: {SYSTEM_TIME} ---")
print(f"Logging to file: {log_filepath}")
print("Operating System: ", SYSTEM_OS)


def get_timestamped_dir():
    # Example: 2026-03-02_10-45-30
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(BASE_DIR, timestamp)

    # Create directory (safe even if exists)
    os.makedirs(path, exist_ok=True)

    return path

def copy_skills_to_target(target_root):
    shutil.copytree(SKILLS_DIR, f"{target_root}/skills/", dirs_exist_ok=False)


def main():
    # 2. Initialize the Local Shell Backend
    system_prompt = f"""You are a precise and highly capable software development assistant.
Your current working directory is empty, and you have access to a shell environment where you can create files, write code, build Docker images, and execute commands.

Context:
- Current Date/Time: {SYSTEM_TIME}
- Operating System: {SYSTEM_OS}

Guidelines:
- Explain your reasoning: Always provide clear, step-by-step explanations of your thought process and the commands you execute.
- OS Compatibility: Ensure all commands are appropriate for the specified operating system.
- Skill Utilization: Before writing code from scratch, evaluate if an existing skill applies to the software task and leverage it. Ensure any skill names used or referenced adhere strictly to the Agent Skills specification (lowercase alphanumeric characters with single hyphens only).

CRITICAL WORKFLOW REQUIREMENT:
For every application, service, or codebase you generate, you MUST strictly adhere to this execution path:
1. Containerize: Write a comprehensive `Dockerfile` tailored to the generated code and its dependencies.
2. Build: Execute the command to build the Docker image (e.g., `docker build -t app-image .`).
3. Run (Background): Run the Docker container in detached mode so it runs in the background and does not block the shell (e.g., `docker run -d -p 8080:8080 --name running-app app-image`). 
4. Verify & Test: Once the container is running, use `curl` to fetch the live content from the exposed port (e.g., `curl -s http://localhost:8080`). Analyze the output to ensure the application matches the expected behavior and requirements.
"""

    TARGET_ROOT = get_timestamped_dir()
    os.chdir(TARGET_ROOT)
    print(f"Agent will operate in isolated directory: {TARGET_ROOT}\n")

    copy_skills_to_target(TARGET_ROOT)
    print(f"Created and initialized: {TARGET_ROOT}")

    system_prompt += f"\n\nThe agent's root directory has been set up at: {TARGET_ROOT}. So create complete project structures, Dockerfiles, and execute builds and runs within this directory. Do not attempt to access or modify files outside of this directory."

    backend = LocalShellBackend(
        root_dir=TARGET_ROOT, 
        virtual_mode=True,
        env={"PATH": os.environ.get("PATH", TARGET_ROOT)}
    )

    # 3. Create the deep agent, explicitly passing the Gemini LLM
    agent = create_deep_agent(
        model=GEMINI_MODEL,
        backend=backend,
        skills=["skills/"],  
        tools=[write_file_tool, create_project_structure_tool, fetch_webpage_content]
    )

    prompt = """
                    Create a scifi calculator app using struts and make the UI very modern and scifi. 
            """
    print("Initializing Agent Workflow...")
    print("Executing code generation, Docker build, and system tests...\n")
    print(f"System Prompt:\n{system_prompt}\n")

    # 5. Invoke the agent
    inputs = {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
    }
    config = {"configurable": {"thread_id": "gemini-docker-test-run"}}

    # Track final messages to calculate tokens later
    final_messages = []

    # 6. Stream the agent's thought process, tool execution, and standard output
    try:
        for chunk in agent.stream(inputs, config, stream_mode="values"):
            final_messages = chunk["messages"] # Update final messages on every chunk
            last_message = final_messages[-1]
            
            # Pretty print the agent's messages, tool calls, and tool outputs
            if hasattr(last_message, "pretty_print"):
                last_message.pretty_print()
            else:
                print(last_message)
                
        # --- Token Calculation Block ---
        total_input_tokens = 0
        total_output_tokens = 0

        for msg in final_messages:
            # Check for standard LangChain usage_metadata (LangChain >= 0.2.x)
            if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                total_input_tokens += msg.usage_metadata.get('input_tokens', 0)
                total_output_tokens += msg.usage_metadata.get('output_tokens', 0)
            
            # Fallback check for older response_metadata mapping just in case
            elif hasattr(msg, 'response_metadata') and msg.response_metadata and 'token_usage' in msg.response_metadata:
                usage = msg.response_metadata['token_usage']
                total_input_tokens += usage.get('prompt_token_count', 0)
                total_output_tokens += usage.get('candidates_token_count', 0)

        total_tokens = total_input_tokens + total_output_tokens

        print("\n" + "="*40)
        print("          TOKEN USAGE SUMMARY           ")
        print("="*40)
        print(f"Total Input Tokens : {total_input_tokens:,}")
        print(f"Total Output Tokens: {total_output_tokens:,}")
        print(f"Total Tokens Used  : {total_tokens:,}")
        print("="*40 + "\n")
        # -------------------------------

    except Exception as e:
        print(f"\n[ERROR] An exception occurred: {e}")
    finally:
        print(f"\n--- Execution Finished ---")

if __name__ == "__main__":
    main()