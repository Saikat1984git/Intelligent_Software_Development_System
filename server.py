import asyncio
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage
import uvicorn

# Import the orchestrator function
from orchestrator.orchestrator import orchestrator

app = FastAPI(title="iSDS Orchestrator API")

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Store conversation history per session
    history = []
    
    # Send Welcome Banner as an initial log
    await websocket.send_json({
        "type": "log",
        "content": "🤖 Welcome to the iSDS Orchestrator API\nConnection established."
    })

    try:
        while True:
            
            # 1. Wait for User Input from the frontend
            user_input = await websocket.receive_text()
            
            # Skip empty inputs
            if not user_input.strip():
                continue
                
            # 2. Send immediate status update (replacing the rich spinner)
            await websocket.send_json({
                "type": "log",
                "content": "Orchestrator is analyzing and routing..."
            })

            # 3. Capture terminal output (stdout/stderr) during execution
            log_capture = io.StringIO()
            with redirect_stdout(log_capture), redirect_stderr(log_capture):
                try:
                    # Process Input via Orchestrator
                    response = await orchestrator(text=user_input, history=history)
                    
                    # Update Conversation History
                    history.append(HumanMessage(content=user_input))
                    history.append(AIMessage(content=response))
                    
                    # Grab any terminal logs captured during execution
                    captured_logs = log_capture.getvalue()
                    if captured_logs:
                        await websocket.send_json({
                            "type": "terminal_log",
                            "content": captured_logs.strip()
                        })
                        
                    # 4. Send the final Orchestrator response
                    await websocket.send_json({
                        "type": "response",
                        "content": response
                    })

                except Exception as e:
                    # Catch and stream execution errors
                    await websocket.send_json({
                        "type": "error",
                        "content": f"System Error: {str(e)}"
                    })
                    
    except WebSocketDisconnect:
        print("Client disconnected from WebSocket.")

if __name__ == "__main__":
    # Run the server with: python main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)