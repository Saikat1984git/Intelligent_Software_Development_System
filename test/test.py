import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent
from daytona import Daytona
from langchain_daytona import DaytonaSandbox

# 1. Load the environment variables from the .env file
load_dotenv()

# 2. Initialize the Gemini model
# It will automatically find 'GOOGLE_API_KEY' in your loaded environment
GEMINI_MODEL = ChatGoogleGenerativeAI(
    model="gemini-3.0-pro", # or "gemini-3.1-pro-preview" depending on your access
    temperature=0.7
)

# 3. Initialize your Sandbox (e.g., Daytona)
sandbox = Daytona().create()
backend = DaytonaSandbox(sandbox=sandbox)

try:
    # 4. Create the agent with Gemini as the engine
    agent = create_deep_agent(
        model=GEMINI_MODEL,
        system_prompt="You are an autonomous AI software engineer with sandbox access.",
        backend=backend,
    )

    # 5. Run your prompt
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Write a python script that prints 'Hello Gemini' and execute it."}]
    })
    
    print(result["messages"][-1].content)

finally:
    sandbox.stop()