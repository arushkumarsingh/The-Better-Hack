#!/bin/bash
# Run script for BOTH backend and frontend

# Start backend (in background)
uvicorn api:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend (in foreground)
cd feature-scribe-studio
npm run dev

# When frontend stops, kill backend
kill $BACKEND_PID
