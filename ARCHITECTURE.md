# System Architecture Specification: iSDS (Intelligent Software Development System)

## 1. System Overview

This specification details the architecture of **iSDS (Intelligent Software Development System)**, a LangChain-orchestrated autonomous multi-agent workflow designed for end-to-end software development, deployment, and testing. The system implements a distributed cognitive architecture, routing specific execution tasks to specialized Large Language Models (Gemini 3.1 Pro for structural reasoning; GPT-5 Codex/Mini variants for syntax generation and execution).

The core operational paradigm relies on isolated agents mutating a shared state, driven by an autonomous feedback loop of code generation, localized container execution, error interception, and automated browser-based quality assurance.

---

## 2. Agent Modules & Execution Paths

The system is compartmentalized into four specialized agents, each restricted to specific read/write privileges and execution boundaries.

### 2.1. Code Generation Agent
Functions as the initial compiler of raw requirements into a structured, containerized repository. It utilizes a Directed Acyclic Graph (DAG) generation sequence to ensure dependency constraints are met.

* **Requirement Parsing (GPT-5 Mini):** Analyzes the prompt to define system scope, constraints, and operational logic.
* **Context Injection (GPT-5 Mini):** Dynamically loads framework-specific skill files based on parsed requirements.
* **Architecture Scaffolding (Gemini 3.1 Pro):**
    * Constructs the full repository file tree.
    * Defines inter-module dependencies and public interfaces.
    * Initializes the `PROJECT_METADATA.md` state file.
* **Topological Sorting (Gemini 3.1 Pro):** Segments the architecture into hierarchical dependency levels (e.g., database schemas before data access layers).
* **Parallel Synthesis (GPT-5 Codex Mini):** Executes asynchronous code generation across the parsed dependency levels.
* **Artifact Generation:** Outputs the source code, `Dockerfile`, `docker-compose.yml`, and testing protocol mapped to `TESTDOC.md`.

### 2.2. Run & Debug Agent
Operates as the localized runtime environment and primary error handler. It manages container lifecycles and acts as the immediate feedback mechanism for compilation and runtime faults.

* **Container Execution (GPT-5 Mini):** Mounts the generated repository and initializes the Docker orchestration.
* **Error Interception:** Actively monitors container standard output (stdout) and standard error (stderr).
* **Direct Delegation:** Upon detecting a compilation or runtime failure, it extracts the stack trace/error logs and passes them directly to the **Code Modification Agent** with instructions to implement a fix.
* **State Loop:** Continuously rebuilds and re-executes the container environment until a zero-error state is confirmed.
* **Network Output:** Yields a stable `localhost` URL upon successful deployment.

### 2.3. QA Testing Agent
Executes behavioral and end-to-end (E2E) validations against the compiled application utilizing automated browser control.

* **Protocol Synthesis (Gemini 3.1 Pro):** Translates the requirements into step-by-step Quality Assurance workflows.
* **Automated Execution (GPT-5 Mini):** Interfaces with Playwright via the Model Context Protocol (MCP) to initialize a headless Chromium instance.
* **Validation:** Reads `TESTDOC.md` and simulates defined user flows on the active `localhost` port.
* **Telemetry & Reporting:** Writes assertion results, execution logs, and UI failure states to `TESTRESULT.md`.

### 2.4. Code Modification Agent
The central mutation engine responsible for all codebase alterations post-initial generation. It acts on external user prompts or internal system error events.

* **State Retrieval (Gemini 3.1 Pro):** Reads `PROJECT_METADATA.md` to map the current system state and dependency graph.
* **Context Isolation:** Selects only the specific candidate files required to address the input (bug fix, feature addition, or UI change), optimizing the context window.
* **Code Mutation:** Alters existing source code or scaffolds new dependency files based on the error logs provided by the Run & Debug Agent or feedback from the QA Testing Agent.
* **State Synchronization:** Commits structural changes to `PROJECT_METADATA.md` to maintain global architectural consistency.

---

## 3. Orchestration & Execution Loop

iSDS utilizes LangChain to orchestrate state transitions and ensure application stability through a continuous integration and testing loop.

1.  **Deployment Initialization:** The Run & Debug Agent attempts to build and start the Docker environment.
2.  **Runtime Resolution Loop:** * If the container fails, the Run & Debug Agent passes the exact error trace to the Code Modification Agent.
    * The Code Modification Agent patches the codebase.
    * This cycle repeats autonomously until the container achieves a healthy runtime state.
3.  **QA Handoff:** Once healthy, the Run & Debug Agent passes the `localhost` URL to the QA Testing Agent.
4.  **E2E Validation:** The QA Testing Agent executes Playwright scripts against the running application.
5.  **Test Resolution Loop:** * Failed assertions are logged to `TESTRESULT.md`.
    * The Run & Debug Agent reads these failures and delegates them to the Code Modification Agent for logical or UI fixes.
6.  **Termination:** The loop terminates when both the runtime environment is stable and all QA protocols pass successfully.

---

## 4. Persistent Memory & State Management

The system maintains context across the multi-agent graph utilizing localized markdown files as persistent data stores.

| Artifact | Purpose | Access Control |
| :--- | :--- | :--- |
| **`PROJECT_METADATA.md`** | Global source of truth defining file structures, module dependencies, and system architecture. | R/W by Code Gen & Code Mod. Read by all. |
| **`TESTDOC.md`** | Defines QA test steps, expected UI states, and simulated user flows. | Written by Code Gen. Read by QA Testing. |
| **`TESTRESULT.md`** | Telemetry output containing Playwright execution logs and failure stack traces. | Written by QA Testing. Read by Run & Debug. |

---

## 5. Technology Stack

* **Agent Orchestration:** LangChain
* **LLM Integration:** Gemini 3.1 Pro, GPT-5 Mini, GPT-5 Codex Mini
* **Containerization:** Docker, Docker Compose
* **Testing Infrastructure:** Playwright, Model Context Protocol (MCP), Chromium Headless