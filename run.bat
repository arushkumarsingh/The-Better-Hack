@echo off
REM Run script for BOTH backend and frontend

REM Start backend
start cmd /k ".venv\Scripts\activate && uvicorn api:app --reload --host 0.0.0.0 --port 8000"

REM Start frontend
cd feature-scribe-studio
npm run dev

REM Note: You'll need to manually close the backend window when done./r