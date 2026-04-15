@echo off
echo Starting Strategify MLOps Stack...

echo Starting FastAPI Backend (Port 8000)...
start cmd /k "python strategify/web/server.py"

echo Starting Vite React Frontend (Port 5173)...
cd frontend
start cmd /k "npm run dev"

echo Strategify Stack running.
