#!/bin/bash
echo "Starting Psychology Today Scraper..."
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Files in directory: $(ls -la)"

# Start the Flask app
exec python app.py
