# Intelligent Software Development System (iSDS)

An AI-powered software development system that combines a React frontend with a FastAPI backend to orchestrate intelligent software development workflows.

## Tech Stack

### Frontend
- React 19
- Vite 7
- React Router DOM
- TailwindCSS 4

### Backend
- FastAPI
- Uvicorn
- Python 3.10+

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Node.js | 18+ |
| Python | 3.10+ |
| pip | Latest |

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Intelligent_Software_Development_System
```

### 2. Set up the backend

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set up the frontend

```bash
cd frontend
npm install
```

## Running the Application

### Option 1: Running Both Services

You need to run both the backend and frontend in separate terminals.

#### Step 1: Start the Backend

Open a terminal in the project root directory:

```bash
python server.py
```

The backend server will start at **http://localhost:8000**

To verify the backend is running, open your browser and navigate to:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### Step 2: Start the Frontend

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
npm run dev
```

The frontend will be available at **http://localhost:5173**

### Option 2: Running Services on Custom Ports

If the default ports are already in use:

```bash
# Backend on port 8001
python server.py --port 8001

# Frontend on port 5174
cd frontend
npm run dev -- --port 5174
```

## Project Structure

```
Intelligent_Software_Development_System/
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── contexts/      # React contexts
│   │   └── App.jsx        # Main app component
│   ├── package.json
│   └── vite.config.js
├── orchestrator/          # Code orchestration logic
│   └── orchestrator.py
├── server.py              # FastAPI backend server
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── README.md
```

## Environment Variables

The project includes a `.env` file with configuration. Key variables:

```env
SECRET_KEY=isds-secret-key-change-in-production-2024
```

For production, update the SECRET_KEY and add API keys:

```env
# Backend
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./isds.db

# API Keys (if required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

## Quick Start Commands Summary

```bash
# Terminal 1 - Backend
python server.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

## Troubleshooting

### Port already in use

If port 8000 or 5173 is already in use:

```bash
# Find and kill the process using the port
# Windows
netstat -ano | findstr ":8000"
taskkill /PID <PID> /F
```

### Module not found errors

Reinstall dependencies:

```bash
# Python
pip install -r requirements.txt

# Node.js
cd frontend && npm install
```

### Backend not starting

Check for missing dependencies:
```bash
pip install -r requirements.txt
```

### Frontend not building

Clear node_modules and reinstall:
```bash
cd frontend
rm -rf node_modules
npm install
```

## Available Scripts

### Frontend

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## License

MIT