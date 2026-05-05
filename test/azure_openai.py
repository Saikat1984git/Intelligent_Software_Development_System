from langchain_openai import ChatOpenAI

import os
from dotenv import load_dotenv

load_dotenv()

GPT_51_CODEX_MINI = ChatOpenAI(
    # The model name here must match your Azure 'Deployment Name'
    model="gpt-5.1-codex-mini", 
    # Azure V1 API requires the specific /openai/v1/ suffix
    base_url=f"{os.getenv('AZURE_OPENAI_ENDPOINT').rstrip('/')}/openai/v1/",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"), 
    # Azure requires the api-key in the headers for this specific route
    default_headers={
        "api-key": os.getenv("AZURE_OPENAI_API_KEY")
    },
    
    temperature=0,
    max_retries=2
)

# # Quick Test
# response = llm.invoke("Write a FastAPI route for document validation.")
# print(response.content)