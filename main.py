import asyncio
import os
import platform
import shutil
import sys
from datetime import datetime
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.create_project_structure_tool import create_project_structure_tool
from tools.write_file_tool import write_file_tool
from tools.debug.fetch_webpage_content import fetch_webpage_content
from tools.debug.capture_website_screenshot import capture_website_screenshot

from models.openai_models import GPT_51_CODEX_MINI, GPT_4O_MINI, GPT_52_CHAT , GPT_5_MINI_TEST
from models.gemini_models import GEMINI_31_PRO, GEMINI_25_PRO, GEMINI_3_FLASH, GEMINI_25_FLASH, GEMINI_25_FLASH_LITE


from agents.codegen_agent import run_codegeneration_agent
from agents.debug_agent import run_debugging_agent
from utils import should_continue_debugging


load_dotenv()


# --- Constants for Workspace Setup ---
ROOT_PATH = os.getcwd()
SKILLS_DIR = os.path.join(ROOT_PATH, "skills")
BASE_DIR = os.path.join(ROOT_PATH, "generated")

def get_timestamped_dir():
    """Generates and creates a timestamped directory for isolated execution."""
    # Example: 2026-03-08_10-45-30
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(BASE_DIR, f"latest_{timestamp}")

    # Create directory (safe even if exists)
    os.makedirs(path, exist_ok=True)

    return path


async def main():
    user_requirements = (
      """
 Create a full-stack enterprise-style vehicle management web application inspired by classic dealership/internal ERP desktop-style systems.

## Tech Stack
### Frontend
- Angular (latest stable version)
- Angular Material + custom CSS for classic enterprise UI styling
- Reactive Forms
- Routing enabled
- Modular architecture

### Backend
- Java Spring Boot
- REST API architecture
- Spring Data JPA
- MySQL database
- DTO + Service + Repository layered architecture

---

# Application Goal

Build a vehicle enquiry and registration management application.

The application should:
1. Allow users to enter vehicle-related information in a large enterprise-style form
2. Save the data into MySQL
3. Submit the form
4. Navigate to another screen/page
5. Display submitted records in a searchable table/grid
6. Allow viewing details of a selected record

---

# UI/UX Requirements

Design the UI similar to old-school enterprise dealership systems:
- Light gray background
- Compact form fields
- Multi-panel layout
- Dense data-oriented interface
- Thin borders
- Small fonts
- Left-aligned labels
- Section/group containers
- Toolbar/menu at top
- Action buttons on right side
- Professional ERP/DMS appearance

The layout should resemble:
- Vehicle Enquiry screen
- Dealer Management System
- Inventory/Order management software
- Classic desktop-business software adapted for web

---

# Frontend Features

## Main Vehicle Entry Screen

Create sections such as:

### Vehicle Details
Fields:
- Stock Number
- VIN
- Model Code
- Model Description
- Colour
- Trim
- Registration Number
- Engine Number
- Location
- Status
- Key Number
- Dealer Comment

### Dealer Details
Fields:
- Request Number
- Dealer Name
- Delivery Point
- Dealer Status

### Shipping Details
Fields:
- Ship Name
- Voyage
- Car Number
- Wharf
- Bond Number
- Days In
- Order Number

### Delivery Details
Fields:
- Dealer ID
- Order Number
- Slip Order
- Delivery Type
- Finance Company
- Release Number

### Sale Details
Fields:
- Registration Status
- Dealer Code
- Registration Date
- Reservation Status

---

# Functional Requirements

## Form Features
- Angular Reactive Forms
- Form validation
- Required field validation
- Date pickers
- Dropdowns
- Submit button
- Reset button

## Backend API
Create REST APIs:

### POST
`/api/vehicles`
- Save vehicle data

### GET
`/api/vehicles`
- Get all vehicle records

### GET BY ID
`/api/vehicles/{id}`
- Get vehicle details

---

# Database Design

Use MySQL.

Create a `vehicles` table with appropriate columns for all fields.

Use:
- Auto increment primary key
- Proper datatypes
- Timestamp fields

---

# Second Screen

Create another Angular page:
`/vehicle-list`

Features:
- Data table/grid
- Pagination
- Search/filter
- Sort columns
- View details button

When clicking a row:
- Navigate to detail page
- Show all stored information in read-only format

---

# Backend Architecture

Use clean layered architecture:

- Controller
- Service
- Repository
- Entity
- DTO

Implement:
- Exception handling
- Validation
- CORS configuration
- API response structure

---

# Angular Architecture

Use:
- Feature modules
- Shared components
- Services for API calls
- Environment configuration
- Angular routing
- Loading indicators

---

# Additional Requirements

- Generate complete project structure
- Include MySQL configuration
- Include API integration
- Include Angular service classes
- Include entity models
- Include DTOs
- Include sample SQL schema
- Include complete CRUD-ready foundation
- Use enterprise coding standards
- Keep the UI responsive but desktop-oriented
- Use reusable components
- Add mock sample data

---

# Styling Instructions

The design should imitate:
- Classic enterprise desktop systems
- ERP software
- Vehicle dealership management systems
- Dense information dashboards

Visual characteristics:
- Gray panels
- Small rectangular inputs
- Blue action buttons
- Compact spacing
- Multi-column layout
- Thin separators
- Minimal animations
- High information density

---


The final result should look like a real-world dealership management enterprise application.

"""
    )
    print("🚀 Starting the AI Software Architect...")
    
    # 1. --- SETUP ISOLATED WORKSPACE ---
    TARGET_ROOT = get_timestamped_dir()
    target_skills_dir = os.path.join(TARGET_ROOT, "skills")
    
    # Copy all skills into the target path before changing directories
    if os.path.exists(SKILLS_DIR):
        print(f"📁 Copying skills to isolated environment...")
        shutil.copytree(SKILLS_DIR, target_skills_dir, dirs_exist_ok=True)
    else:
        print(f"⚠️  WARNING: Source skills directory '{SKILLS_DIR}' not found.")
        print("Creating an empty 'skills' directory in the target path to prevent agent errors.")
        os.makedirs(target_skills_dir, exist_ok=True)

    # Move the Python execution context into the new isolated folder
    os.chdir(TARGET_ROOT)
    print(f"🔒 Agent will operate in isolated directory: {TARGET_ROOT}\n")
    
    print("⚙️  Running code generation...")
    execution_agent_summary = await run_codegeneration_agent(
        user_requirements=user_requirements,
    )
    print("✅ Code generation complete!\n")

    # --- THE INTERACTIVE LANGCHAIN DECISION GATE ---
    user_response = input("🤔 Do you want to start the debugging process now? ")
    
    print("🤖 Analyzing response...")
    wants_to_debug = await should_continue_debugging(user_response)
    
    if not wants_to_debug:
        print("🛑 User opted to skip debugging. Exiting process...")
        return  # Safely exit the function
    # -----------------------------------------------

    print("\n🐞 Starting the debugging process...")
    # 2. Starting the debugging process
    debugging_agent_summary = await run_debugging_agent(
        requirement=user_requirements,
        previous_output=execution_agent_summary,
        root_path=TARGET_ROOT
    )
    print("🐞🔫 Debugging process complete!\n")
    
    print("✅ All tasks finished!")
     

if __name__ == "__main__":
    asyncio.run(main())