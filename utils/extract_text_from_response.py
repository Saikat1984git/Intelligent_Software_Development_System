def extract_text_from_response(response):
    """
    Extracts the actual raw text from almost any LLM response structure 
    (LangChain objects, OpenAI objects, API dictionaries, or lists of blocks).
    """
    # 1. LangChain BaseMessage objects (like AIMessage)
    if hasattr(response, "content"):
        return extract_text_from_response(response.content)
        
    # 2. OpenAI Object (ChatCompletion)
    if hasattr(response, "choices") and len(response.choices) > 0:
        return extract_text_from_response(response.choices[0].message.content)

    # 3. Base case: Plain string
    if isinstance(response, str):
        return response.strip()

    # 4. API Dictionaries (JSON responses)
    if isinstance(response, dict):
        # OpenAI style dictionary
        if "choices" in response and isinstance(response["choices"], list) and len(response["choices"]) > 0:
            msg = response["choices"][0].get("message", {})
            return extract_text_from_response(msg.get("content", ""))
            
        # Dictionary with a direct 'content' key
        if "content" in response:
            return extract_text_from_response(response["content"])
            
        # Specific block dictionary (like Anthropic/Gemini)
        if response.get("type") == "text" and "text" in response:
            return response.get("text", "").strip()
            
        # Fallback for dicts that just have a 'text' key
        if "text" in response:
            return extract_text_from_response(response["text"])

    # 5. Lists (Content blocks or nested arrays)
    if isinstance(response, list):
        # First, try to find a specific 'text' block to avoid dumping hidden reasoning tokens
        for block in response:
            if isinstance(block, dict) and block.get("type") == "text":
                return block.get("text", "").strip()
        
        # If no explicit text block is found, extract and join everything recursively
        parts = [extract_text_from_response(item) for item in response]
        return "\n".join(filter(None, parts)).strip()

    # 6. Fallback for completely unknown or unexpected types
    return str(response)