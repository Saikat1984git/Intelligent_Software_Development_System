from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")

COMMON_CONFIG = dict(
    temperature=0.2,
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
    # default_headers={
    #     "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "http://localhost"),
    #     "X-Title": os.environ.get("OPENROUTER_SITE_NAME", "My App"),
    # },
)

# ----------------------------
# "Gemini 3" Equivalent
# ----------------------------

GEMINI_31_PRO = ChatOpenAI(
    model="google/gemini-3.1-pro-preview",   # High reasoning
    **COMMON_CONFIG
)

GEMINI_3_FLASH = ChatOpenAI(
    model="google/gemini-3-flash-preview",   # Fast + cheap
    **COMMON_CONFIG
)

GEMINI_3_FLASH_LITE = ChatOpenAI(
    model="google/gemini-3.1-flash-lite-preview",  # Ultra cheap
    **COMMON_CONFIG
)

# ----------------------------
# "Gemini 2.5" Equivalent
# ----------------------------

GEMINI_25_PRO = ChatOpenAI(
    model="google/gemini-2.5-pro",   # Stable + strong reasoning
    **COMMON_CONFIG
)

GEMINI_25_FLASH = ChatOpenAI(
     model="google/gemini-2.5-flash",   # Stable + fast
    **COMMON_CONFIG
)

GEMINI_25_FLASH_LITE = ChatOpenAI(
    model="google/gemini-2.5-flash-lite-preview-09-2025",  # Cheapest
    **COMMON_CONFIG
)