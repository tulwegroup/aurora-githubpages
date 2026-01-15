#!/bin/bash
set -e

echo "=== Installing Python dependencies with pip ==="
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt

echo "=== Python dependencies installed successfully ==="
