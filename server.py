import asyncio
import sys
import io
import json
import os
import zipfile
import shutil
import uuid
import tempfile
import warnings
from datetime import datetime, timedelta
from contextlib import redirect_stdout, redirect_stderr

# Suppress LangChain deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from werkzeug.utils import secure_filename
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
import bcrypt
import uvicorn
from typing import AsyncGenerator, Optional
from langchain_core.messages import HumanMessage, AIMessage

# Import the orchestrator function
from orchestrator.orchestrator import orchestrator
from agents.codegen_agent import build_codebase_graph

# ==================== APP DEFINITION ====================
app = FastAPI(title="iSDS Orchestrator API")

# Configure CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== AUTH CONFIGURATION ====================
SECRET_KEY = "isds-secret-key-change-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# ==================== AUTH MODELS ====================
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None

# ==================== DATABASE FUNCTIONS ====================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

os.makedirs(DATA_DIR, exist_ok=True)

def load_json(file_path, default=None):
    if default is None:
        default = []
    if not os.path.exists(file_path):
        return default
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    users = load_json(USERS_FILE, [])
    for user in users:
        if user["id"] == user_id:
            return UserResponse(id=user["id"], username=user["username"], email=user["email"])
    raise credentials_exception

# ==================== AUTH ENDPOINTS ====================
@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    users = load_json(USERS_FILE, [])

    # Check if username or email already exists
    for user in users:
        if user["username"] == user_data.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        if user["email"] == user_data.email:
            raise HTTPException(status_code=400, detail="Email already exists")

    new_user = {
        "id": str(uuid.uuid4()),
        "username": user_data.username,
        "email": user_data.email,
        "password": get_password_hash(user_data.password),
        "created_at": datetime.now().isoformat()
    }
    users.append(new_user)
    save_json(USERS_FILE, users)

    access_token = create_access_token(
        data={"sub": new_user["id"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=new_user["id"], username=new_user["username"], email=new_user["email"])
    )

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return JWT token"""
    users = load_json(USERS_FILE, [])
    user = None
    for u in users:
        if u["username"] == form_data.username:
            user = u
            break

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_response = UserResponse(id=user["id"], username=user["username"], email=user["email"])
    access_token = create_access_token(
        data={"sub": user["id"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@app.post("/api/auth/logout")
async def logout():
    """Logout user"""
    return {"message": "Successfully logged out"}

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
            'comprehensive_status': 'Codebase generation complete.',
            'progress': 100,
            'files_done': files_done,
            'total_files': total_files,
            'response_type': 'codegen',
            'ask_debugging': True  # Flag to ask user if they want to debug
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


# --- Debugging Workflow ---
MAX_DEBUG_ITERATIONS = 5  # Maximum number of debugging iterations

async def run_debugging_workflow(requirements: str, job_id: str, job_dir: str):
    """Run the debugging workflow with granular progress events and iterate until bug-free.

    Note: The debug agent handles iteration internally, so we run it once and let it
    iterate until success or max iterations reached internally.
    """
    original_cwd = os.getcwd()
    iteration = 0
    bugs_detected = 0
    bugs_fixed = 0
    error_count = 0
    max_iterations = MAX_DEBUG_ITERATIONS

    try:
        # Change to the job directory
        os.chdir(job_dir)

        # Yield initial debug started event
        yield json.dumps({
            'event': 'debug_start',
            'job_id': job_id,
            'comprehensive_status': 'Starting debugging process...',
            'progress': 0,
            'bugs_detected': bugs_detected,
            'bugs_fixed': bugs_fixed,
            'iteration': iteration,
            'response_type': 'debug'
        }) + '\n'

        # Import the debugging agent
        from agents.debug_agent import run_debugging_agent

        # Yield detect_bugs stage - start of debugging
        yield json.dumps({
            'event': 'detect_bugs',
            'job_id': job_id,
            'comprehensive_status': 'Detecting bugs and analyzing application...',
            'progress': 10,
            'bugs_detected': bugs_detected,
            'bugs_fixed': bugs_fixed,
            'iteration': 1,
            'error_count': error_count,
            'response_type': 'debug'
        }) + '\n'

        # Run the debugging agent - it handles iteration internally
        # The debug agent will:
        # 1. Build and run the Docker application
        # 2. Analyze any errors
        # 3. Fix them using code_fixing_agent
        # 4. Rebuild and verify
        # 5. Run QA validation
        # 6. Iterate until success or max iterations
        try:
            result = await run_debugging_agent(
                requirement=requirements,
                previous_output="Code generation completed",
                root_path=job_dir
            )

            # Extract information from the result
            if result:
                result_lower = result.lower()
                current_errors = result_lower.count('error') + result_lower.count('failed') + result_lower.count('exception')

                if current_errors > 0:
                    bugs_detected = max(bugs_detected, current_errors)
                    error_count = current_errors
                    # Assume successful fixes if the agent completed
                    bugs_fixed = bugs_detected

                    yield json.dumps({
                        'event': 'analyze_errors',
                        'job_id': job_id,
                        'comprehensive_status': f'Analyzed {current_errors} issue(s)',
                        'progress': 40,
                        'bugs_detected': bugs_detected,
                        'bugs_fixed': bugs_fixed,
                        'iteration': 1,
                        'error_count': error_count,
                        'response_type': 'debug'
                    }) + '\n'
                else:
                    # No errors - debugging was successful
                    bugs_fixed = bugs_detected

        except Exception as agent_error:
            # If the agent itself fails, log but continue
            error_count += 1
            yield json.dumps({
                'event': 'debug_error',
                'job_id': job_id,
                'comprehensive_status': f'Debugging agent error: {str(agent_error)}',
                'progress': 50,
                'bugs_detected': bugs_detected,
                'bugs_fixed': bugs_fixed,
                'iteration': 1,
                'error_count': error_count,
                'response_type': 'debug'
            }) + '\n'

            # Continue to repackage even if there was an error

        # Yield apply_fixes/rebuild stage
        yield json.dumps({
            'event': 'apply_fixes',
            'job_id': job_id,
            'comprehensive_status': 'Applying fixes and rebuilding...',
            'progress': 60,
            'bugs_detected': bugs_detected,
            'bugs_fixed': bugs_fixed,
            'iteration': 1,
            'error_count': error_count,
            'response_type': 'debug'
        }) + '\n'

        # Yield QA validation stage
        yield json.dumps({
            'event': 'validate_qa',
            'job_id': job_id,
            'comprehensive_status': 'Running QA validation...',
            'progress': 75,
            'bugs_detected': bugs_detected,
            'bugs_fixed': bugs_fixed,
            'iteration': 1,
            'error_count': error_count,
            'response_type': 'debug'
        }) + '\n'

        # Final stages - repackage
        yield json.dumps({
            'event': 'repackage',
            'job_id': job_id,
            'comprehensive_status': 'Repackaging debugged code...',
            'progress': 90,
            'bugs_detected': bugs_detected,
            'bugs_fixed': bugs_fixed,
            'iteration': 1,
            'error_count': error_count,
            'response_type': 'debug'
        }) + '\n'

        # Remove old zip and create new one
        old_zip = f"{job_dir}.zip"
        if os.path.exists(old_zip):
            os.remove(old_zip)

        zip_path = shutil.make_archive(job_dir, 'zip', job_dir)

        # Update job metadata
        files_done = []
        for root, dirs, files in os.walk(job_dir):
            for f in files:
                if not f.startswith('.') and not f.endswith('.pyc'):
                    rel_path = os.path.relpath(os.path.join(root, f), job_dir)
                    files_done.append(rel_path)

        JOBS[job_id] = {
            'zip_path': zip_path,
            'job_dir': job_dir,
            'total_files': len(files_done),
            'files_done': files_done,
            'debugged': True,
            'bugs_detected': bugs_detected,
            'bugs_fixed': bugs_fixed,
            'iterations': 1
        }

        # Final completion event
        completion_message = 'Debugging complete! All issues have been fixed.' if bugs_detected == bugs_fixed and bugs_detected > 0 else 'Debugging completed. Review the results for any remaining issues.'

        yield json.dumps({
            'event': 'debug_completed',
            'job_id': job_id,
            'comprehensive_status': completion_message,
            'progress': 100,
            'files_done': files_done,
            'total_files': len(files_done),
            'bugs_detected': bugs_detected,
            'bugs_fixed': bugs_fixed,
            'iteration': 1,
            'error_count': error_count,
            'response_type': 'debug'
        }) + '\n'

    except Exception as e:
        import traceback
        error_msg = f"Debugging Error: {str(e)}"
        yield json.dumps({
            'event': 'debug_error',
            'job_id': job_id,
            'comprehensive_status': error_msg,
            'bugs_detected': bugs_detected,
            'bugs_fixed': bugs_fixed,
            'iteration': iteration,
            'error_count': error_count,
            'response_type': 'debug'
        }) + '\n'

    finally:
        os.chdir(original_cwd)


# --- REST Streaming Endpoint (Server-Sent Events) ---
async def generate_stream(user_input: str, session_id: str = "default") -> AsyncGenerator[str, None]:
    """Generate streaming response using Server-Sent Events (SSE).

    This implementation follows the EXACT same flow as chat.py:
    1. Get user input
    2. Process via orchestrator (same as terminal)
    3. Update conversation history
    4. Stream response back to client
    """
    history = session_histories.get(session_id, [])

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Log for debugging
    print(f"[DEBUG] Starting generate_stream for job_id={job_id}, session_id={session_id}")
    print(f"[DEBUG] User input: {user_input[:100]}...")

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
            print(f"[DEBUG] Calling orchestrator with history length: {len(history)}")

            # EXACT SAME AS chat.py: Call orchestrator for ALL requests
            # The orchestrator internally decides which tool to invoke
            response = await orchestrator(text=user_input, history=history)

            print(f"[DEBUG] Orchestrator returned response length: {len(response)}")

            # EXACT SAME AS chat.py: Update conversation history
            history.append(HumanMessage(content=user_input))
            history.append(AIMessage(content=response))
            session_histories[session_id] = history

            print(f"[DEBUG] History updated, sending response to client")

            # Send captured terminal output
            for line in capture.lines:
                clean_line = strip_ansi(line.strip())
                if clean_line:
                    yield json.dumps({'event': 'update', 'job_id': job_id, 'comprehensive_status': clean_line, 'progress': 30, 'response_type': 'chat'}) + '\n'

            # Send the final response (stripped of ANSI codes)
            clean_response = strip_ansi(response)

            # Check if this was a code generation request by checking response content
            if 'code generation completed' in clean_response.lower() or 'artifact bundle ready' in clean_response.lower():
                # For code generation, create ZIP and provide download
                yield json.dumps({'event': 'update', 'job_id': job_id, 'comprehensive_status': clean_response, 'progress': 70, 'response_type': 'chat'}) + '\n'

                print(f"[DEBUG] Code generation detected, creating ZIP file")

                # Find the latest generated directory and create ZIP
                generated_dir = None
                if os.path.exists(BASE_DIR):
                    dirs = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
                    if dirs:
                        # Get the most recent directory
                        dirs.sort(key=lambda x: os.path.getmtime(os.path.join(BASE_DIR, x)), reverse=True)
                        generated_dir = os.path.join(BASE_DIR, dirs[0])
                        print(f"[DEBUG] Found generated directory: {generated_dir}")

                if generated_dir and os.path.exists(generated_dir):
                    try:
                        # Create ZIP file
                        zip_path = shutil.make_archive(generated_dir, 'zip', generated_dir)
                        print(f"[DEBUG] Created ZIP at: {zip_path}")

                        # Get list of files
                        files_done = []
                        for root, dirs, files in os.walk(generated_dir):
                            for f in files:
                                if not f.startswith('.') and not f.endswith('.pyc'):
                                    rel_path = os.path.relpath(os.path.join(root, f), generated_dir)
                                    files_done.append(rel_path)

                        # Store job metadata for download
                        JOBS[job_id] = {
                            'zip_path': zip_path,
                            'job_dir': generated_dir,
                            'total_files': len(files_done),
                            'files_done': files_done
                        }

                        yield json.dumps({
                            'event': 'update',
                            'job_id': job_id,
                            'comprehensive_status': f'Artifact bundle ready. {len(files_done)} files generated.',
                            'progress': 90,
                            'response_type': 'chat'
                        }) + '\n'

                    except Exception as zip_error:
                        print(f"[ERROR] Failed to create ZIP: {zip_error}")
                        yield json.dumps({
                            'event': 'update',
                            'job_id': job_id,
                            'comprehensive_status': clean_response,
                            'progress': 90,
                            'response_type': 'chat'
                        }) + '\n'

                yield json.dumps({'event': 'completed', 'job_id': job_id, 'comprehensive_status': clean_response, 'progress': 100, 'response_type': 'chat'}) + '\n'
            else:
                # Send completion event for non-code-generation requests
                yield json.dumps({'event': 'update', 'job_id': job_id, 'comprehensive_status': clean_response, 'progress': 90, 'response_type': 'chat'}) + '\n'
                yield json.dumps({'event': 'completed', 'job_id': job_id, 'comprehensive_status': 'Response complete', 'progress': 100, 'response_type': 'chat'}) + '\n'

        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            print(f"[DEBUG] Finished generate_stream for job_id={job_id}")

    except Exception as e:
        import traceback
        print(f"[ERROR] generate_stream failed: {str(e)}")
        print(traceback.format_exc())
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

    # Check if this is a code generation request
    code_keywords = ['generate', 'create', 'build', 'make', 'implement', 'develop', 'app', 'project', 'website', 'api', 'code']
    is_code_gen = any(keyword in user_input.lower() for keyword in code_keywords)

    # For code generation, use LangGraph streaming for real-time updates
    if is_code_gen:
        job_id = str(uuid.uuid4())
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            run_langgraph_workflow(user_input, job_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # For chat/other requests, use the orchestrator
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


@app.post("/run-debug")
async def run_debug(request: Request):
    """Run debugging on a previously generated project."""
    body = await request.json()
    job_id = body.get("job_id", "")
    requirements = body.get("requirements", "")

    if not job_id:
        return {"error": "job_id is required"}

    # Get the job directory
    job = JOBS.get(job_id)
    if not job:
        return {"error": "Job not found. Please generate a project first."}

    job_dir = job.get('job_dir')
    if not job_dir or not os.path.exists(job_dir):
        return {"error": "Project directory not found"}

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        run_debugging_workflow(requirements, job_id, job_dir),
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
    print(f"[DEBUG] Download requested for job_id: {job_id}")

    # First check if we have it in our jobs storage
    job = JOBS.get(job_id)
    print(f"[DEBUG] Job found in memory: {job is not None}")

    if job:
        zip_path = job.get('zip_path')
        print(f"[DEBUG] Checking zip path: {zip_path}")
        if zip_path and os.path.exists(zip_path):
            print(f"[DEBUG] Serving zip from memory: {zip_path}")
            return FileResponse(
                zip_path,
                media_type='application/zip',
                filename=f'generated_code_{job_id}.zip',
                headers={
                    "Content-Disposition": f"attachment; filename=generated_code_{job_id}.zip"
                }
            )

    # Fallback: look for directories/zips in BASE_DIR
    job_dir = None
    zip_path = None

    print(f"[DEBUG] BASE_DIR exists: {os.path.exists(BASE_DIR)}")
    if os.path.exists(BASE_DIR):
        items = os.listdir(BASE_DIR)
        print(f"[DEBUG] Items in BASE_DIR: {items}")

        # First, look for any zip files
        for item in items:
            if item.endswith('.zip'):
                zip_path = os.path.join(BASE_DIR, item)
                print(f"[DEBUG] Found zip file: {zip_path}")
                break

        # If no zip, look for directories
        if not zip_path:
            for item in items:
                item_path = os.path.join(BASE_DIR, item)
                # Check for directory with job_id in name
                if os.path.isdir(item_path) and job_id in item:
                    job_dir = item_path
                    # Look for existing zip
                    potential_zip = item_path + '.zip'
                    if os.path.exists(potential_zip):
                        zip_path = potential_zip
                        print(f"[DEBUG] Found zip in directory: {zip_path}")
                        break

    if not zip_path and job_dir:
        # Create zip if it doesn't exist
        try:
            zip_path = shutil.make_archive(job_dir, 'zip', job_dir)
            print(f"[DEBUG] Created new zip: {zip_path}")
        except Exception as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"error": f"Failed to create zip: {str(e)}"})

    if not zip_path or not os.path.exists(zip_path):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Job not found or no files generated"})

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


# --- Code Editing / Rewrite Endpoint ---
import tempfile
import threading
import queue

async def run_code_editing_workflow(project_path: str, prompt: str, images: list = None):
    """Generator that runs code editing and yields SSE messages."""
    log_queue = queue.Queue()
    images = images or []

    def run_task():
        try:
            from agents.code_editing_agent import code_editing_agent
            log_queue.put(f"Starting code editing for project: {project_path}")
            log_queue.put(f"Edit prompt: {prompt}")

            if images:
                log_queue.put(f"Received {len(images)} image(s) for visual reference")

            # Run the code editing agent
            result = code_editing_agent(
                edit_prompt=prompt,
                project_folder_path=project_path,
                images=images
            )

            log_queue.put(f"Code editing complete: {result}")
        except Exception as e:
            import traceback
            log_queue.put(f"Error: {str(e)}")
            log_queue.put(traceback.format_exc())
        finally:
            log_queue.put(None)  # Sentinel value to signal completion

    # Start the task in a background thread
    thread = threading.Thread(target=run_task)
    thread.start()

    # Yield messages from the queue as SSE
    while True:
        message = log_queue.get()
        if message is None:
            yield "data: [DONE]\n\n"
            break
        # Replace newlines to ensure SSE format isn't broken
        clean_msg = message.replace('\n', ' ')
        yield f"data: {clean_msg}\n\n"


@app.post("/rewrite")
async def rewrite_code(request: Request):
    """Endpoint for code modification/rewrite with streaming response.

    Accepts form data:
    - project_path: Absolute path to the project directory
    - prompt: Description of the desired changes
    - images: Optional image files for visual reference
    """
    try:
        # Parse form data
        form = await request.form()
        project_path = form.get("project_path", "").strip()
        prompt = form.get("prompt", "").strip()

        # Extract uploaded images
        images = []
        if "images" in form:
            # Handle multiple images
            image_files = form.getlist("images")
            for img in image_files:
                if hasattr(img, 'read') and hasattr(img, 'content_type'):
                    # It's a file upload
                    content = await img.read()
                    images.append({
                        "filename": img.filename,
                        "content_type": img.content_type,
                        "data": content
                    })

        if not project_path:
            return {"error": "project_path is required"}
        if not prompt:
            return {"error": "prompt is required"}

        if not os.path.exists(project_path):
            return {"error": f"Project path does not exist: {project_path}"}

        # Return streaming response
        return StreamingResponse(
            run_code_editing_workflow(project_path, prompt, images),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


if __name__ == "__main__":
    # Run the server with: python server.py
    # Note: This runs on port 8000 by default
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)