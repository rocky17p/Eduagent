"""
AI Educational Content Generator - Flask Application

Main application that orchestrates the Generator, Reviewer, Refiner, and Tagger agents
with a web UI to trigger and display the agent pipeline.

Part 2: Governed, Auditable AI Content Pipeline
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from orchestrator import Orchestrator
from database import ensure_db_initialized, get_history, get_run_artifact

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

# Initialize database 
ensure_db_initialized()

# Initialize orchestrator
api_key = os.getenv("GROQ_API_KEY")
orchestrator = Orchestrator(api_key=api_key)


@app.route('/')
def index():
    """Serve the main UI."""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'has_api_key': bool(api_key),
        'version': '2.0.0'
    })


@app.route('/api/generate', methods=['POST'])
def generate():
    """
    Run the full content generation pipeline.
    
    Request Body:
        {
            "grade": 5,
            "topic": "Fractions as parts of a whole",
            "user_id": "optional-user-id"
        }
    
    Response:
        Complete RunArtifact with audit trail
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        grade = data.get('grade')
        topic = data.get('topic')
        user_id = data.get('user_id')
        
        if not grade or not topic:
            return jsonify({
                'success': False,
                'error': 'Both grade and topic are required'
            }), 400
        
        # Validate grade
        try:
            grade = int(grade)
            if grade < 1 or grade > 12:
                return jsonify({
                    'success': False,
                    'error': 'Grade must be between 1 and 12'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Grade must be a number'
            }), 400
        
        # Run the orchestrator pipeline
        artifact = orchestrator.run(grade, topic, user_id)
        
        # Also return legacy format for UI compatibility
        response = {
            'success': True,
            'run_artifact': artifact,
            # Legacy fields for backward compatibility with Part 1 UI
            'generator_output': artifact['attempts'][0]['draft'] if artifact['attempts'] else None,
            'reviewer_output': artifact['attempts'][0]['review'] if artifact['attempts'] else None,
            'refined_output': None,
            'was_refined': False
        }
        
        # Check if content was refined
        if len(artifact['attempts']) > 1:
            response['was_refined'] = True
            response['refined_output'] = artifact['attempts'][-1]['draft']
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in generate endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history', methods=['GET'])
def api_get_history():
    """
    Retrieve run history.
    
    Query Parameters:
        user_id: Optional user identifier to filter by
        limit: Maximum records to return (default 50)
    
    Response:
        List of RunArtifact summaries
    """
    try:
        user_id = request.args.get('user_id')
        limit = request.args.get('limit', 50, type=int)
        
        artifacts = get_history(user_id, limit)
        
        return jsonify({
            'success': True,
            'count': len(artifacts),
            'artifacts': artifacts
        })
        
    except Exception as e:
        print(f"Error in history endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/run/<run_id>', methods=['GET'])
def get_run(run_id):
    """
    Retrieve a specific run artifact by ID.
    
    Response:
        Complete RunArtifact
    """
    try:
        artifact = get_run_artifact(run_id)
        
        if not artifact:
            return jsonify({
                'success': False,
                'error': 'Run not found'
            }), 404
        
        return jsonify({
            'success': True,
            'artifact': artifact
        })
        
    except Exception as e:
        print(f"Error in get_run endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("AI Educational Content Generator - Part 2")
    print("=" * 60)
    if api_key:
        print("✓ Groq API key detected")
    else:
        print("⚠ No Groq API key - using mock responses")
        print("  Get free API key at: https://console.groq.com/keys")
    print("Starting server at http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, port=5000)
