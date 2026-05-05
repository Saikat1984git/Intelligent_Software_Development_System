from pydantic import BaseModel, Field
from models.gemini_models import GEMINI_3_FLASH_LITE

# 1. Define the exact output structure we want using Pydantic
class DebugDecision(BaseModel):
    continue_debugging: bool = Field(
        description="True if the user indicates they want to start or continue the debugging process. False if they want to stop, skip, no, or exit."
    )

async def should_continue_debugging(user_input: str) -> bool:
    """Uses LangChain structured output to determine if the user wants to continue."""
    
    # 2. Bind the Pydantic schema to the Gemini model
    structured_llm = GEMINI_3_FLASH_LITE.with_structured_output(DebugDecision)
    
    # Notice the prompt is simpler now; we don't have to threaten the model 
    # to "ONLY output True or False" because Pydantic enforces it under the hood.
    prompt = f"""
    The user was asked if they want to start the debugging process. 
    User replied: "{user_input}"
    
    Analyze the user's intent. Do they want to proceed with debugging?
    """
    
    # 3. Use ainvoke(). The response is automatically parsed into our DebugDecision object!
    response: DebugDecision = await structured_llm.ainvoke(prompt)
    # print(f"DEBUGGING DECISION: {response}")
    
    # 4. Return the strictly typed boolean
    return response.continue_debugging