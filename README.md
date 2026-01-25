# EduGen AI - Educational Content Generator

An AI-powered educational content generation system using a multi-agent pipeline (Generator + Reviewer) with a modern web interface.

## 🎯 Features

- **Generator Agent**: Creates grade-appropriate educational content with detailed explanations and 5 MCQs
- **Reviewer Agent**: Evaluates content for age appropriateness, correctness, and clarity
- **Automatic Refinement**: Re-generates content if reviewer feedback indicates issues
- **Modern UI**: Dark theme with glassmorphism design, showing the complete agent pipeline flow

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Groq API key (free at https://console.groq.com/keys)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Groq API key in .env file
# Edit .env and add: GROQ_API_KEY=your_key_here

# Run the application
python app.py
```

Open http://localhost:5000 in your browser.

## 📁 Project Structure

```
eklavya/
├── app.py                 # Flask API server
├── requirements.txt       # Python dependencies
├── .env                   # API key configuration
├── agents/
│   ├── __init__.py
│   ├── generator.py       # Generator Agent (Groq API)
│   └── reviewer.py        # Reviewer Agent (Groq API)
└── static/
    ├── index.html         # Web UI
    ├── styles.css         # Styling
    └── script.js          # Frontend logic
```

## 🔄 Agent Pipeline

1. **User Input** → Grade + Topic submitted via UI
2. **Generator Agent** → Produces initial content (explanation + 5 MCQs)
3. **Reviewer Agent** → Evaluates content against criteria
4. **Refinement** → If review fails, Generator re-runs with feedback (1 pass max)
5. **Final Output** → All stages displayed in UI

## 📚 API Reference

### POST /api/generate

Generate educational content.

**Request:**
```json
{
  "grade": 4,
  "topic": "Types of angles"
}
```

**Response:**
```json
{
  "success": true,
  "generator_output": { ... },
  "reviewer_output": { ... },
  "refined_output": { ... },
  "was_refined": true
}
```

## 🛠 Technology Stack

- **Backend**: Python, Flask
- **AI**: Groq API with LLaMA 3.3 70B model
- **Frontend**: HTML, CSS (dark theme), JavaScript

## 🔑 Getting Your API Key

1. Go to https://console.groq.com/keys
2. Create a free account (if you don't have one)
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

**Free tier includes:**
- 14,400 requests per day
- 10 requests per minute
- Access to LLaMA 3.3 70B model

## 📄 License

MIT License
