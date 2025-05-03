#!/bin/bash
# Build script for BOTH backend and frontend

# Build backend
pip install -r requirements.txt

# Build frontend
cd feature-scribe-studio
npm install
npm run build
cd ..
