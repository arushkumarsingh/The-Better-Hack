#!/bin/bash
# Build script for BOTH backend and frontend

# Build backend
pip install -r requirements.txt

# Build frontend
cd feature-scribe-studio
npm install
npm run build
cd ..

# Screenity extension installation instructions
# Screenity is a Chrome extension and cannot be installed via CLI.
# Please install it from: https://chrome.google.com/webstore/detail/screenity-screen-recorder/nnjdmcfkmjicephohigpnnfkbebfgdcl
# After installing, pin it in your browser and grant permissions for screen and audio recording.
