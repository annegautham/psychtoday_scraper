"""
your_application.wsgi - Compatibility module for default Render configuration
This allows the default 'gunicorn your_application.wsgi' command to work
"""

from app import app as application

if __name__ == "__main__":
    application.run()
