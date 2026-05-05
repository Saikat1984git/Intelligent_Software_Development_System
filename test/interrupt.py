from langchain.tools import tool
from deepagents import create_deep_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
import uuid
from langgraph.types import Command
import os
from dotenv import load_dotenv

load_dotenv()



GEMINI_MODEL = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro", # or "gemini-3.1-pro-preview" depending on your access
    temperature=0.2
)



@tool
def delete_file(path: str) -> str:
    """Delete a file from the filesystem."""
    print(f"Deleting file at {path}...")  # Simulate deletion
    return f"Deleted {path}"

@tool
def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    print(f"Reading file at {path}...")  # Simulate reading
    return f"Contents of {path}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    print(f"Sending email to {to} with subject '{subject}'...")  # Simulate sending
    return f"Sent email to {to}"

# Checkpointer is REQUIRED for human-in-the-loop
checkpointer = MemorySaver()

agent = create_deep_agent(
    model=GEMINI_MODEL,
    tools=[delete_file, read_file, send_email],
    interrupt_on={
        "delete_file": True,  # Default: approve, edit, reject
        "read_file": False,   # No interrupts needed
        "send_email": {"allowed_decisions": ["approve", "reject"]},  # No editing
    },
    checkpointer=checkpointer  # Required!
)


# Create config with thread_id for state persistence
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# Invoke the agent
# New
result = agent.invoke({
    "messages": [{"role": "user", "content": "Use the delete_file tool on 'temp.txt' immediately. Do not ask for confirmation or check if it exists first."}]
}, config=config)

print(result)

# Check if execution was interrupted
if result.get("__interrupt__"):
    # Extract interrupt information
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]

    # Create a lookup map from tool name to review config
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    # Display the pending actions to the user
    for action in action_requests:
        review_config = config_map[action["name"]]
        print(f"Tool: {action['name']}")
        print(f"Arguments: {action['args']}")
        print(f"Allowed decisions: {review_config['allowed_decisions']}")

    # Get user decisions (one per action_request, in order)
    decisions = [
        {"type": "approve"}  # User approved the deletion
    ]

    # Resume execution with decisions
    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config  # Must use the same config!
    )

# Process final result
print(result["messages"][-1].content)