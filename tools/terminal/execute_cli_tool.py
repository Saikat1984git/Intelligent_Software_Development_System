import subprocess
import threading
import queue
import time
import os
import signal
import re
from datetime import datetime
from langchain.tools import tool

try:
    # LangGraph live streaming support
    from langgraph.config import get_stream_writer
except ImportError:
    get_stream_writer = None


@tool
def execute_cli(
    command: str,
    timeout: int = 300,
    stream_logs: bool = True,
    max_log_lines: int = 100
) -> str:
    """
    Advanced CLI executor with REAL live logs.

    Features:
    - Real-time stdout/stderr streaming
    - LangGraph stream support
    - Non-blocking execution
    - Smart Docker auto-detaching
    - Timeout handling
    - Full log retention
    - Live terminal printing
    - Process group cleanup

    Args:
        command: Shell command
        timeout: Timeout in seconds
        stream_logs: Print logs live
        max_log_lines: Max stored log lines

    Returns:
        Complete execution report
    """

    start_time = datetime.now()
    start_timestamp = time.time()

    logs = []
    log_queue = queue.Queue()

    writer = None

    # LangGraph live stream writer
    if get_stream_writer:
        try:
            writer = get_stream_writer()
        except Exception:
            writer = None

    # Auto-fix blocking docker commands using Regex to catch variations
    # 1. Handle docker-compose / docker compose up
    if re.search(r'docker[\s-]compose.*?\bup\b', command) and not re.search(r'\b(-d|--detach)\b', command):
        command = re.sub(r'(\bup\b)', r'\1 -d', command)
        
    # 2. Handle docker run (prevent blocking foreground workers)
    elif re.search(r'\bdocker\s+run\b', command) and not re.search(r'\b(-d|--detach|--rm|--it|-it)\b', command):
        command = re.sub(r'(\bdocker\s+run\b)', r'\1 -d', command)

    def push_log(source: str, line: str):
        """Handle log everywhere: memory, console, LangGraph stream"""
        formatted = f"[{source}] {line.rstrip()}"
        logs.append(formatted)

        # Prevent infinite memory growth
        if len(logs) > max_log_lines:
            logs.pop(0)

        # Live terminal output
        if stream_logs:
            print(formatted, flush=True)

        # LangGraph live stream
        if writer:
            try:
                writer({
                    "type": "log",
                    "source": source,
                    "content": line.rstrip()
                })
            except Exception:
                pass

    def enqueue_output(pipe, pipe_name):
        """Continuously read pipe output in a background thread"""
        try:
            for line in iter(pipe.readline, ''):
                if not line:
                    break
                log_queue.put((pipe_name, line))
        except Exception as e:
            # Only log errors if the pipe didn't close naturally
            if not pipe.closed:
                log_queue.put(("SYSTEM", f"Reader error: {str(e)}"))
        finally:
            try:
                pipe.close()
            except Exception:
                pass

    try:
        # Windows/Linux compatible process handling
        creationflags = 0
        preexec_fn = None

        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            preexec_fn = os.setsid

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            universal_newlines=True,
            bufsize=1,
            creationflags=creationflags,
            preexec_fn=preexec_fn
        )

        push_log("SYSTEM", f"Started process PID={process.pid}")
        push_log("SYSTEM", f"Executing: {command}")

        # Start stdout/stderr readers (daemon threads die with main thread)
        stdout_thread = threading.Thread(
            target=enqueue_output,
            args=(process.stdout, "STDOUT"),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=enqueue_output,
            args=(process.stderr, "STDERR"),
            daemon=True
        )

        stdout_thread.start()
        stderr_thread.start()

        # Main monitoring loop
        while True:
            # Drain all available logs currently in the queue
            while not log_queue.empty():
                try:
                    source, line = log_queue.get_nowait()
                    push_log(source, line)
                except queue.Empty:
                    break

            # Check if process has completed
            if process.poll() is not None:
                # Final flush to catch trailing logs
                time.sleep(0.2)
                while not log_queue.empty():
                    try:
                        source, line = log_queue.get_nowait()
                        push_log(source, line)
                    except queue.Empty:
                        break
                break

            # Timeout check
            elapsed = time.time() - start_timestamp
            if elapsed > timeout:
                push_log("SYSTEM", f"Timeout reached ({timeout}s). Killing process...")
                try:
                    # Kill full process tree
                    if os.name == "nt":
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                        time.sleep(1)
                        if process.poll() is None:
                            process.kill()
                    else:
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except Exception as kill_error:
                    push_log("SYSTEM", f"Kill error: {str(kill_error)}")

                return (
                    f"STATUS: TIMEOUT\n"
                    f"COMMAND: {command}\n"
                    f"TIMEOUT: {timeout}s\n"
                    f"STARTED: {start_time}\n"
                    f"EXIT CODE: KILLED\n\n"
                    f"FULL LOGS:\n"
                    + "\n".join(logs)
                )

            # Prevent CPU pegging
            time.sleep(0.05)

        end_time = datetime.now()
        duration = round((end_time - start_time).total_seconds(), 2)
        exit_code = process.returncode

        push_log("SYSTEM", f"Process finished with exit code {exit_code}")

        return (
            f"STATUS: COMPLETED\n"
            f"COMMAND: {command}\n"
            f"STARTED: {start_time}\n"
            f"ENDED: {end_time}\n"
            f"DURATION: {duration}s\n"
            f"EXIT CODE: {exit_code}\n\n"
            f"FULL LOGS:\n"
            + "\n".join(logs)
        )

    except Exception as e:
        push_log("SYSTEM", f"Fatal error: {str(e)}")
        return (
            f"STATUS: ERROR\n"
            f"COMMAND: {command}\n"
            f"ERROR: {str(e)}\n\n"
            f"PARTIAL LOGS:\n"
            + "\n".join(logs)
        )