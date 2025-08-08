"""
WSGI module for Render's default gunicorn command
This makes 'gunicorn your_application.wsgi' work
"""

import sys
import os

# Add the parent directory to Python path so we can import our app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app import app as application

if __name__ == "__main__":
    application.run()
