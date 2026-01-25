"""
Vercel Serverless Function Entry Point

This file wraps the Flask app for Vercel's serverless Python runtime.
"""

import sys
import os

# Add parent directory to path so we can import our modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set environment to indicate we're on Vercel
os.environ['VERCEL'] = '1'

try:
    from app import app
except Exception as e:
    # If import fails, create a minimal error app
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def error_handler(path):
        return jsonify({
            'error': 'Application failed to initialize',
            'message': str(e),
            'type': type(e).__name__
        }), 500

# Vercel expects the app to be named 'app' or 'handler'
handler = app
