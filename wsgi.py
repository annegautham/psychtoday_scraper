#!/usr/bin/env python3

"""
WSGI entry point for the Psychology Today Scraper Flask application.
This file is used by Gunicorn and other WSGI servers.
"""

from app import app

if __name__ == "__main__":
    app.run()
