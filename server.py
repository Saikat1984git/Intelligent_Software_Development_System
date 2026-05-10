import asyncio
import sys
import io
import json
import os
import zipfile
import shutil
import uuid
import tempfile
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage, AIMessage
import uvicorn
from typing import AsyncGenerator

# Import the orchestrator function
from orchestrator.orchestrator import orchestrator
from agents.codegen_agent import build_codebase_graph

app = FastAPI(title="iSDS Orchestrator API")

# Configure CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversation history per session (in-memory for demo)
session_histories = {}

# Base directory for generated code and job storage
BASE_DIR = os.path.join(os.getcwd(), "generated")
os.makedirs(BASE_DIR, exist_ok=True)

# Store job metadata for downloads
JOBS = {}

def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text for clean display in browser."""
    import re
    # Comprehensive ANSI escape code patterns
    # CSI (Control Sequence Introducer) sequences: ESC [ ... letters
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    # OSC (Operating System Command) sequences: ESC ] ... BEL
    ansi_escape2 = re.compile(r'\x1b\][^\x07]*\x07')
    # DCS (Device Control String): ESC P ... ST
    ansi_escape3 = re.compile(r'\x1bP[^\x07]*\x07')
    # PM (Privacy Message): ESC ^ ... ST
    ansi_escape4 = re.compile(r'\x1b\^[^\x07]*\x07')
    # APC (Application Program Command): ESC _ ... ST
    ansi_escape5 = re.compile(r'\x1b_[^\x07]*\x07')
    # SGR (Select Graphic Rendition) sequences
    ansi_escape6 = re.compile(r'\[([0-9;]+)?m')
    # Other escape sequences
    ansi_escape7 = re.compile(r'\[.*?[@-~]')

    for pattern in [ansi_escape, ansi_escape2, ansi_escape3, ansi_escape4, ansi_escape5, ansi_escape6, ansi_escape7]:
        text = pattern.sub('', text)

    # Remove remaining escape characters
    text = text.replace('\x1b', '')

    return text.strip()

@app.get("/")
async def root():
    return {"message": "iSDS Orchestrator API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# --- Code Generation with LangGraph Streaming ---
async def run_langgraph_workflow(requirements: str, job_id: str):
    """Run LangGraph code generation workflow and yield streaming JSON updates."""
    # Create timestamped directory for this job
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    job_dir = os.path.join(BASE_DIR, f"{job_id}_{timestamp}")
    os.makedirs(job_dir, exist_ok=True)

    # Change to the job directory
    original_cwd = os.getcwd()
    os.chdir(job_dir)

    try:
        yield json.dumps({
            'event': 'started',
            'job_id': job_id,
            'comprehensive_status': 'Initializing code generation workflow...',
            'progress': 0,
            'response_type': 'codegen'
        }) + '\n'

        # Build the LangGraph app
        app = build_codebase_graph()

        initial_state = {
            "requirements": requirements,
            "skills": "./skills"
        }

        files_done = []
        total_files = 0
        generated_files = []

        # Stream from LangGraph
        async for event in app.astream(initial_state, stream_mode="updates"):
            for node_name, output in event.items():
                # Extract relevant information from the node output
                status_msg = f"Completed node: {node_name}"

                if node_name == "load_skills":
                    status_msg = "Skills loaded successfully"
                    yield json.dumps({
                        'event': 'update',
                        'job_id': job_id,
                        'comprehensive_status': status_msg,
                        'progress': 10,
                        'files_done': files_done,
                        'response_type': 'codegen'
                    }) + '\n'

                elif node_name == "generate_structure":
                    # Structure generation complete
                    status_msg = "Project structure generated"
                    yield json.dumps({
                        'event': 'update',
                        'job_id': job_id,
                        'comprehensive_status': status_msg,
                        'progress': 25,
                        'files_done': files_done,
                        'response_type': 'codegen'
                    }) + '\n'

                elif node_name == "generate_files":
                    # File generation is happening
                    if output:
                        # Check for generated_files in output
                        if output.get("generated_files"):
                            generated_files = output.get("generated_files", [])
                            files_done = generated_files
                            total_files = len(generated_files)
                            progress = min(90, 25 + (len(generated_files) / max(total_files, 1) * 60))
                            status_msg = f"Generated {len(generated_files)} files"
                            yield json.dumps({
                                'event': 'update',
                                'job_id': job_id,
                                'comprehensive_status': status_msg,
                                'progress': progress,
                                'files_done': files_done,
                                'response_type': 'codegen'
                            }) + '\n'
                        # Also check for execution_log messages
                        elif output.get("execution_log"):
                            log_msgs = output.get("execution_log", [])
                            if log_msgs:
                                status_msg = strip_ansi(log_msgs[-1] if isinstance(log_msgs[-1], str) else str(log_msgs[-1]))
                                yield json.dumps({
                                    'event': 'update',
                                    'job_id': job_id,
                                    'comprehensive_status': status_msg,
                                    'progress': 50,
                                    'files_done': files_done,
                                    'response_type': 'codegen'
                                }) + '\n'

                elif node_name == "execute_skill_scripts":
                    status_msg = "Executing skill scripts..."
                    yield json.dumps({
                        'event': 'update',
                        'job_id': job_id,
                        'comprehensive_status': status_msg,
                        'progress': 85,
                        'files_done': files_done,
                        'response_type': 'codegen'
                    }) + '\n'

                elif node_name == "summarize":
                    if output:
                        summary = output.get("agent_summary", "Code generation complete")
                        yield json.dumps({
                            'event': 'update',
                            'job_id': job_id,
                            'comprehensive_status': strip_ansi(str(summary)),
                            'progress': 95,
                            'files_done': files_done,
                            'response_type': 'codegen'
                        }) + '\n'

        # Scan directory for any generated files if none captured
        if not files_done:
            all_files = []
            for root, dirs, files in os.walk(job_dir):
                for f in files:
                    if not f.startswith('.') and not f.endswith('.pyc') and '__pycache__' not in root:
                        rel_path = os.path.relpath(os.path.join(root, f), job_dir)
                        all_files.append(rel_path)
            files_done = all_files
            total_files = len(all_files)

        # Create ZIP file
        yield json.dumps({
            'event': 'update',
            'job_id': job_id,
            'comprehensive_status': 'Creating artifact bundle...',
            'progress': 98,
            'files_done': files_done,
            'response_type': 'codegen'
        }) + '\n'

        zip_path = shutil.make_archive(job_dir, 'zip', job_dir)

        # Store job metadata
        JOBS[job_id] = {
            'zip_path': zip_path,
            'job_dir': job_dir,
            'total_files': total_files,
            'files_done': files_done
        }

        yield json.dumps({
            'event': 'completed',
            'job_id': job_id,
            'comprehensive_status': 'Codebase generation complete. Artifact bundle ready.',
            'progress': 100,
            'files_done': files_done,
            'total_files': total_files,
            'response_type': 'codegen'
        }) + '\n'

    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}"
        yield json.dumps({
            'event': 'error',
            'job_id': job_id,
            'comprehensive_status': error_msg
        }) + '\n'

    finally:
        os.chdir(original_cwd)


# --- REST Streaming Endpoint (Server-Sent Events) ---
async def generate_stream(user_input: str, session_id: str = "default") -> AsyncGenerator[str, None]:
    """Generate streaming response using Server-Sent Events (SSE)."""
    history = session_histories.get(session_id, [])

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    try:
        # Send initial status - strip ANSI codes for clean display
        clean_status = strip_ansi("Orchestrator is analyzing and routing...")
        yield json.dumps({'event': 'started', 'job_id': job_id, 'comprehensive_status': clean_status, 'progress': 0, 'response_type': 'chat'}) + '\n'

        # Capture terminal output during execution
        log_capture = io.StringIO()

        # We need to capture rich console output differently
        # Create a custom handler to capture console prints
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        class CaptureHandler:
            def __init__(self):
                self.lines = []

            def write(self, text):
                if text.strip():
                    self.lines.append(text)

            def flush(self):
                pass

        capture = CaptureHandler()
        sys.stdout = capture
        sys.stderr = capture

        try:
            # Check if this looks like a code generation request
            is_codegen = any(keyword in user_input.lower() for keyword in [
                'create', 'build', 'generate', 'make', 'develop', 'new project',
                'web app', 'website', 'application', 'app'
            ])

            if is_codegen:
                # Use LangGraph workflow for code generation
                async for payload in run_langgraph_workflow(user_input, job_id):
                    yield payload

                # Update conversation history
                history.append(HumanMessage(content=user_input))
                history.append(AIMessage(content="Code generation completed successfully."))
                session_histories[session_id] = history
            else:
                # Use regular orchestrator for other requests
                response = await orchestrator(text=user_input, history=history)

                # Update Conversation History
                history.append(HumanMessage(content=user_input))
                history.append(AIMessage(content=response))
                session_histories[session_id] = history

                # Send captured terminal output
                for line in capture.lines:
                    clean_line = strip_ansi(line.strip())
                    if clean_line:
                        yield json.dumps({'event': 'update', 'job_id': job_id, 'comprehensive_status': clean_line, 'progress': 50, 'response_type': 'chat'}) + '\n'

                # Send the final response (stripped of ANSI codes)
                clean_response = strip_ansi(response)
                yield json.dumps({'event': 'update', 'job_id': job_id, 'comprehensive_status': clean_response, 'progress': 90, 'response_type': 'chat'}) + '\n'

                # Send completion event
                yield json.dumps({'event': 'completed', 'job_id': job_id, 'comprehensive_status': 'Response complete', 'progress': 100, 'response_type': 'chat'}) + '\n'

        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    except Exception as e:
        yield json.dumps({'event': 'error', 'job_id': job_id, 'comprehensive_status': f'System Error: {str(e)}', 'response_type': 'chat'}) + '\n'


@app.post("/run")
async def run_orchestrator(request: Request):
    """REST endpoint for code generation with streaming response."""
    body = await request.json()
    user_input = body.get("requirements", "")
    session_id = body.get("session_id", "default")

    if not user_input.strip():
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            generate_stream(""),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"}
        )

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        generate_stream(user_input, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/download/{job_id}")
async def download_artifact(job_id: str):
    """Download generated code as a ZIP file."""
    # First check if we have it in our jobs storage
    job = JOBS.get(job_id)

    if job:
        zip_path = job.get('zip_path')
        if zip_path and os.path.exists(zip_path):
            return FileResponse(
                zip_path,
                media_type='application/zip',
                filename=f'generated_code_{job_id}.zip',
                headers={
                    "Content-Disposition": f"attachment; filename=generated_code_{job_id}.zip"
                }
            )

    # Fallback: look for directories matching the job_id pattern
    job_dir = None
    zip_path = None

    if os.path.exists(BASE_DIR):
        for item in os.listdir(BASE_DIR):
            item_path = os.path.join(BASE_DIR, item)
            # Check for directory with job_id in name
            if os.path.isdir(item_path) and job_id in item:
                job_dir = item_path
                # Look for existing zip
                potential_zip = item_path + '.zip'
                if os.path.exists(potential_zip):
                    zip_path = potential_zip
                    break

    if not zip_path and job_dir:
        # Create zip if it doesn't exist
        try:
            zip_path = shutil.make_archive(job_dir, 'zip', job_dir)
        except Exception as e:
            return {"error": f"Failed to create zip: {str(e)}"}, 500

    if not zip_path or not os.path.exists(zip_path):
        return {"error": "Job not found or no files generated"}, 404

    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=f'generated_code_{job_id}.zip',
        headers={
            "Content-Disposition": f"attachment; filename=generated_code_{job_id}.zip"
        }
    )


# --- WebSocket Endpoint ---
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
    # Run the server with: python server.py
    # Note: This runs on port 8000 by default
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)