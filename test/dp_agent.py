# pip install -qU deepagents
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent
import os
from dotenv import load_dotenv

load_dotenv()

# 2. Initialize the Gemini model
# It will automatically find 'GOOGLE_API_KEY' in your loaded environment
GEMINI_MODEL = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview", # or "gemini-3.1-pro-preview" depending on your access
    temperature=0.7
)



def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"




agent = create_deep_agent(
    model=GEMINI_MODEL,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
result=agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

print(result["messages"][-1].content)