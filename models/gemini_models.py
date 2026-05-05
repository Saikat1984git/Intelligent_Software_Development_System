from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file if it exists

API_KEY = os.environ.get("GEMINI_API_KEY")

COMMON_CONFIG = dict(
    temperature=0.2,
    api_key=API_KEY
)

# ----------------------------
# Gemini 3
# ----------------------------


GEMINI_31_PRO = ChatGoogleGenerativeAI(
    model="gemini-3.1-pro-preview",
    **COMMON_CONFIG
)

GEMINI_3_FLASH = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    **COMMON_CONFIG
)

GEMINI_3_FLASH_LITE = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    **COMMON_CONFIG
)
# GEMINI_3_1_FLASH_LITE = ChatGoogleGenerativeAI(
#     model="gemini-3.1-flash-lite",
#     **COMMON_CONFIG
# )

# ----------------------------
# Gemini 2.5
# ----------------------------

GEMINI_25_PRO = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    **COMMON_CONFIG
)

GEMINI_25_FLASH = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    **COMMON_CONFIG
)

GEMINI_25_FLASH_LITE = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    **COMMON_CONFIG
)