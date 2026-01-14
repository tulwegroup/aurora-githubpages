#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Building frontend..."
npm run build

echo "Build complete!"
