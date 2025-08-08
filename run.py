#!/usr/bin/env python3
"""
Startup script for the Psychology Today Scraper
Ensures proper initialization and error handling
"""

import os
import sys
import traceback

def start_app():
    try:
        # Ensure we're in the right directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        sys.path.insert(0, script_dir)
        
        # Import and start the Flask app
        from app import app
        
        # Get port from environment or default to 5000
        port = int(os.environ.get('PORT', 5000))
        
        print(f"Starting Psychology Today Scraper on port {port}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Python path: {sys.path[:3]}")
        
        return app
        
    except Exception as e:
        print(f"Error starting app: {e}")
        traceback.print_exc()
        raise

# For Gunicorn
application = start_app()

if __name__ == '__main__':
    app = start_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
