"""
AI Educational Content Generator - Flask Application

Main application that orchestrates the Generator and Reviewer agents
with a web UI to trigger and display the agent pipeline.
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from agents import GeneratorAgent, ReviewerAgent

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

# Initialize agents with Groq API key
api_key = os.getenv("GROQ_API_KEY")
generator = GeneratorAgent(api_key=api_key)
reviewer = ReviewerAgent(api_key=api_key)


@app.route('/')
def index():
    """Serve the main UI."""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


@app.route('/api/generate', methods=['POST'])
def generate_content():
    """
    Main API endpoint to trigger the agent pipeline.
    
    Expected Input:
        {
            "grade": 4,
            "topic": "Types of angles"
        }
    
    Output:
        {
            "generator_output": { ... },
            "reviewer_output": { ... },
            "refined_output": { ... } or null,
            "was_refined": true/false
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        grade = data.get('grade')
        topic = data.get('topic')
        
        if not grade or not topic:
            return jsonify({"error": "Both 'grade' and 'topic' are required"}), 400
        
        try:
            grade = int(grade)
        except ValueError:
            return jsonify({"error": "'grade' must be a number"}), 400
        
        if grade < 1 or grade > 12:
            return jsonify({"error": "'grade' must be between 1 and 12"}), 400
        
        # Step 1: Generator Agent produces initial content
        generator_output = generator.generate(grade=grade, topic=topic)
        
        # Step 2: Reviewer Agent evaluates the content
        reviewer_output = reviewer.review(content=generator_output, grade=grade)
        
        # Step 3: Refinement logic (if reviewer returns fail)
        refined_output = None
        was_refined = False
        
        if reviewer_output.get('status') == 'fail':
            # Re-run generator with feedback (limit to one refinement pass)
            feedback = reviewer_output.get('feedback', [])
            refined_output = generator.generate(
                grade=grade, 
                topic=topic, 
                feedback=feedback
            )
            was_refined = True
        
        return jsonify({
            "success": True,
            "grade": grade,
            "topic": topic,
            "generator_output": generator_output,
            "reviewer_output": reviewer_output,
            "refined_output": refined_output,
            "was_refined": was_refined
        })
        
    except Exception as e:
        print(f"Error in generate_content: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "has_api_key": bool(api_key)
    })


if __name__ == '__main__':
    print("=" * 60)
    print("AI Educational Content Generator")
    print("=" * 60)
    if api_key:
        print("✓ Groq API key detected")
    else:
        print("⚠ No Groq API key - using mock responses")
        print("  Get free API key at: https://console.groq.com/keys")
    print("Starting server at http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, port=5000)
