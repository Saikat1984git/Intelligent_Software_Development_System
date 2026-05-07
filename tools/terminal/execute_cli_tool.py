import subprocess
import threading
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
    - Real-time stdout/stderr streaming (Zero-latency thread push)
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
    logs = []
    log_lock = threading.Lock()

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
        """Handle log everywhere INSTANTLY: memory, console, LangGraph stream"""
        if not line:
            return
            
        formatted = f"[{source}] {line.rstrip()}"
        
        # Lock ensures stdout and stderr don't print on top of each other
        with log_lock:
            logs.append(formatted)

            # Prevent infinite memory growth
            if len(logs) > max_log_lines:
                logs.pop(0)

            # Live terminal output (Instant)
            if stream_logs:
                print(formatted, flush=True)

            # LangGraph live stream (Instant)
            if writer:
                try:
                    writer({
                        "type": "log",
                        "source": source,
                        "content": line.rstrip()
                    })
                except Exception:
                    pass

    def read_stream(pipe, source_name):
        """Read directly from the pipe and push immediately."""
        try:
            # iter() reads continuously until EOF. Since the subprocess is
            # line-buffered (bufsize=1), this yields instantly per line.
            for line in iter(pipe.readline, ''):
                push_log(source_name, line)
        except Exception as e:
            if not pipe.closed:
                push_log("SYSTEM", f"Reader error ({source_name}): {str(e)}")
        finally:
            try:
                pipe.close()
            except Exception:
                pass

    try:
        # Windows/Linux compatible process handling
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        preexec_fn = os.setsid if os.name != "nt" else None

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            universal_newlines=True,
            bufsize=1,  # Line buffered for immediate flushing
            creationflags=creationflags,
            preexec_fn=preexec_fn
        )

        push_log("SYSTEM", f"Started process PID={process.pid}")
        push_log("SYSTEM", f"Executing: {command}")

        # Start direct-push threads (daemon threads die with main thread)
        stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, "STDOUT"), daemon=True)
        stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, "STDERR"), daemon=True)

        stdout_thread.start()
        stderr_thread.start()

        # Efficiently wait for the process instead of polling with sleep()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            push_log("SYSTEM", f"Timeout reached ({timeout}s). Killing process...")
            try:
                # Kill full process tree
                if os.name == "nt":
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        process.kill()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except Exception as kill_error:
                push_log("SYSTEM", f"Kill error: {str(kill_error)}")

            # Wait briefly to catch final logs produced during kill
            stdout_thread.join(timeout=1.0)
            stderr_thread.join(timeout=1.0)

            return (
                f"STATUS: TIMEOUT\n"
                f"COMMAND: {command}\n"
                f"TIMEOUT: {timeout}s\n"
                f"STARTED: {start_time}\n"
                f"EXIT CODE: KILLED\n\n"
                f"FULL LOGS:\n"
                + "\n".join(logs)
            )

        # Ensure threads finish reading trailing output
        stdout_thread.join(timeout=1.0)
        stderr_thread.join(timeout=1.0)

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