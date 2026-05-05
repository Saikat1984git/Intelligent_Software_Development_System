# Intelligent Software Development System (ISDS)

A Python-based project designed to run in an isolated virtual environment for clean dependency management.

---

## 🚀 Getting Started

Follow the steps below to set up and run the project on a new system.

---

## 📦 Prerequisites

Make sure you have the following installed:

* Python 3.8 or higher
* pip (Python package manager)

Check your installation:

```bash
python --version
pip --version
```

---

## 🧱 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

---

### 2. Create Virtual Environment

#### Windows:

```bash
python -m venv venv
```

#### macOS / Linux:

```bash
python3 -m venv venv
```

---

### 3. Activate Virtual Environment

#### Windows (PowerShell):

```bash
venv\Scripts\Activate
```

#### Windows (CMD):

```bash
venv\Scripts\activate.bat
```

#### macOS / Linux:

```bash
source venv/bin/activate
```

---

### 4. Install Dependencies

If you have a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Project

Run the main Python file:

```bash
python main.py
```

---

## 🧹 Deactivating Virtual Environment

When you're done:

```bash
deactivate
```

---

## 📁 Project Structure

```
your-repo/
│
├── venv/                # Virtual environment (ignored in git)
├── main.py              # Entry point of the application
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

---

## ⚠️ Notes

* Do NOT upload the `venv/` folder to GitHub (add it to `.gitignore`)
* Always activate the virtual environment before running the project
* Use `pip freeze > requirements.txt` to update dependencies

---

## 💡 Tips

* If activation fails on Windows, try:

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📌 License

This project is open-source and available under the MIT License.
