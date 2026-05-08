import sys
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage
import uvicorn

# Import the orchestrator function
from orchestrator.orchestrator import orchestrator

app = FastAPI(title="iSDS Orchestrator API")

class LiveLogStream:
    """
    A custom stream that intercepts print() statements and 
    sends them to an asyncio Queue in a thread-safe manner.
    """
    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self.queue = queue
        self.loop = loop

    def write(self, text):
        # We only send non-empty strings to avoid spamming blank lines
        if text.strip():
            # call_soon_threadsafe ensures this works even if the 
            # orchestrator is running synchronous sub-agents in threads
            self.loop.call_soon_threadsafe(self.queue.put_nowait, text)

    def flush(self):
        # Required to emulate standard sys.stdout
        pass

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    history = []
    
    await websocket.send_json({
        "type": "log",
        "content": "🤖 Connected to Orchestrator API. Live streaming active."
    })

    try:
        while True:
            # 1. Wait for User Input
            user_input = await websocket.receive_text()
            if not user_input.strip():
                continue

            await websocket.send_json({
                "type": "log",
                "content": "Executing task..."
            })

            # 2. Setup Live Streaming Queue for this execution
            log_queue = asyncio.Queue()
            loop = asyncio.get_running_loop()
            
            # 3. Create the background task that continuously reads the queue and sends to WebSocket
            async def stream_logs_to_client():
                while True:
                    msg = await log_queue.get()
                    try:
                        await websocket.send_json({
                            "type": "terminal_log",
                            "content": msg
                        })
                    except Exception:
                        break

            log_task = asyncio.create_task(stream_logs_to_client())

            # 4. Redirect stdout and stderr to our custom stream
            custom_stdout = LiveLogStream(log_queue, loop)
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = custom_stdout
            sys.stderr = custom_stdout

            try:
                # 5. Process Input via Orchestrator
                response = await orchestrator(text=user_input, history=history)
                
                # Update Conversation History
                history.append(HumanMessage(content=user_input))
                history.append(AIMessage(content=response))
                
                # 6. Send the final markdown response
                await websocket.send_json({
                    "type": "response",
                    "content": response
                })

            except Exception as e:
                # Stream any critical execution errors to the terminal panel
                await websocket.send_json({
                    "type": "error",
                    "content": f"System Error: {str(e)}"
                })
            finally:
                # 7. CRITICAL: Always restore the original terminal outputs
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                
                # Allow a tiny delay for the queue to flush the last messages, then cancel the background task
                await asyncio.sleep(0.2)
                log_task.cancel()

    except WebSocketDisconnect:
        print("Client disconnected from WebSocket.")

if __name__ == "__main__":
    # Remove --reload if running directly from script
    uvicorn.run("main:app", host="0.0.0.0", port=8000)