# AI Resume Screening System

This project is a full-stack AI-powered resume screening and candidate ranking application. It features a React frontend and a FastAPI backend.

## Running the Project Locally

To run the project, you will need to start both the backend server and the frontend development server in separate terminal windows.

### 1. Running the Backend

The backend is a FastAPI service that handles resume parsing and NLP-driven candidate ranking.

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. **Activate the virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```
   *(Note for Windows users: Make sure you use the correct slash and path. The command is `.\venv\Scripts\Activate.ps1`, not `./Scripts/Activate/vemv`)*

3. Install Python dependencies (if you haven't already):
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend API will be accessible at `http://localhost:8000`.

### 2. Running the Frontend

The frontend is built with React and Vite.

1. Open a **new, separate terminal** and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install the Node.js dependencies (only needed the first time or when dependencies change):
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend UI will be accessible at the local URL provided in the terminal (typically `http://localhost:5173`).


