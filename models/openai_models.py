from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file if it exists


AZURE_ENDPOINT = f"{os.getenv('AZURE_OPENAI_ENDPOINT').rstrip('/')}/openai/v1/"
AZURE_KEY = os.getenv("AZURE_OPENAI_API_KEY")

COMMON_CONFIG = dict(
    base_url=AZURE_ENDPOINT,
    api_key=AZURE_KEY,
    default_headers={"api-key": AZURE_KEY},
    temperature=0,
    max_retries=2
)

# ---------------------------------------------------
# Deployments
# ---------------------------------------------------

GPT_4O_MINI = ChatOpenAI(
    model="gpt-4o-mini",
    **COMMON_CONFIG
)

GPT_5_MINI_TEST = ChatOpenAI(
    model="gpt-5-mini-test",
    **COMMON_CONFIG
)

GPT_51_CODEX_MINI = ChatOpenAI(
    model="gpt-5.1-codex-mini",
    **COMMON_CONFIG
)

GPT_52_CHAT = ChatOpenAI(
    model="gpt-5.2-chat",
    **COMMON_CONFIG
)

MODEL_ROUTER = ChatOpenAI(
    model="model-router",
    **COMMON_CONFIG
)

O4_MINI = ChatOpenAI(
    model="o4-mini",
    **COMMON_CONFIG
)