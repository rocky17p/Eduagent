"""
Vercel Serverless Function Entry Point

This file wraps the Flask app for Vercel's serverless Python runtime.
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects the app to be named 'app' or 'handler'
# Flask WSGI apps work directly with Vercel
