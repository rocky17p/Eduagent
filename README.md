# EduAgent - Educational Content Generator

An AI-powered educational content generation system with a governed, auditable pipeline featuring schema validation, quantitative review, and complete audit trails.

**Live Demo:** [https://eduagent.rishipatwa.me](https://eduagent.rishipatwa.me)

## 🎯 Features

- **Schema-Validated Outputs**: All agent outputs validated via Pydantic
- **Quantitative Review**: Scores (1-5) for age appropriateness, correctness, clarity, coverage
- **Bounded Refinement**: Maximum 2 refinement attempts before rejection
- **Complete Audit Trail**: Every run produces a RunArtifact with full lifecycle
- **PostgreSQL Persistence**: All runs stored in Neon PostgreSQL
- **Testable Architecture**: 3 mandatory tests included

## 🔄 Agent Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Generator   │────▶│   Reviewer   │────▶│   Refiner    │────▶│    Tagger    │
│   Agent      │     │    Agent     │     │    Agent     │     │    Agent     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            │ fail               │ max 2 attempts
                            ▼                    │
                     ┌──────────────┐            │
                     │   REJECTED   │◀───────────┘ (still failing)
                     └──────────────┘
```

## 🤖 Agent Definitions

### 1. Generator Agent
**Responsibility**: Generate draft educational content with schema validation.

**Output Schema**:
```json
{
  "explanation": {"text": "...", "grade": 5},
  "mcqs": [{"question": "...", "options": [...], "correct_index": 1}],
  "teacher_notes": {
    "learning_objective": "...",
    "common_misconceptions": ["..."]
  }
}
```

### 2. Reviewer Agent
**Responsibility**: Quantitatively evaluate quality and decide pass/fail.

**Output Schema**:
```json
{
  "scores": {
    "age_appropriateness": 4,
    "correctness": 5,
    "clarity": 4,
    "coverage": 3
  },
  "passed": true,
  "feedback": [{"field": "explanation.text", "issue": "..."}]
}
```

**Pass Threshold**: All scores must be ≥ 3

### 3. Refiner Agent
**Responsibility**: Improve content using reviewer feedback.

- Maximum 2 refinement attempts
- Each attempt is logged in the audit trail
- If still failing after max attempts → rejected

### 4. Tagger Agent
**Responsibility**: Classify approved content only.

**Output Schema**:
```json
{
  "subject": "Mathematics",
  "topic": "Fractions",
  "difficulty": "Medium",
  "content_type": ["Explanation", "Quiz"],
  "blooms_level": "Understanding"
}
```

## 📊 RunArtifact (Audit Trail)

Every pipeline run produces a complete audit trail:

```json
{
  "run_id": "uuid",
  "input": {"grade": 5, "topic": "Fractions"},
  "attempts": [
    {"attempt": 1, "draft": {...}, "review": {...}}
  ],
  "final": {
    "status": "approved | rejected",
    "content": {...},
    "tags": {...}
  },
  "timestamps": {
    "started_at": "2026-01-25T15:00:00Z",
    "finished_at": "2026-01-25T15:01:30Z"
  }
}
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL database (Neon, Supabase, or Vercel Postgres)
- Groq API key

### Installation

```bash
# Clone the repository
git clone https://github.com/rocky17p/Eduagent.git
cd Eduagent

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your GROQ_API_KEY and DATABASE_URL

# Run the application
python app.py
```

## 📁 Project Structure

```
eduagent/
├── app.py              # Flask application & API routes
├── orchestrator.py     # Pipeline orchestration logic
├── database.py         # PostgreSQL persistence
├── agents/
│   ├── generator.py    # Content generation agent
│   ├── reviewer.py     # Quality review agent
│   ├── refiner.py      # Content refinement agent
│   └── tagger.py       # Content classification agent
├── models/
│   └── schemas.py      # Pydantic validation schemas
├── static/             # Frontend UI files
├── tests/              # Test suite
├── vercel.json         # Vercel deployment config
└── requirements.txt    # Python dependencies
```

## 📚 API Reference

### POST /api/generate
Run the full pipeline and generate educational content.

**Request:**
```json
{"grade": 5, "topic": "Fractions", "user_id": "optional"}
```

**Response:** Complete RunArtifact with audit trail

### GET /api/history
Retrieve run history from the database.

**Query Params:** `user_id`, `limit`

### GET /api/run/{run_id}
Retrieve a specific run artifact by ID.

## 🧪 Running Tests

```bash
pytest tests/ -v
```

**Tests include:**
1. Schema validation failure handling
2. Fail → refine → pass orchestration
3. Fail → refine → fail → reject orchestration

## ⚖️ Trade-offs

1. **PostgreSQL only**: Simpler deployment, consistent behavior locally and on Vercel
2. **Max 2 refinements**: Prevents infinite loops while allowing improvement
3. **Field-level feedback**: More actionable than general comments

## 🚀 Vercel Deployment

The application is deployed on Vercel with PostgreSQL (Neon).

### Environment Variables Required

In Vercel dashboard, add:
- `GROQ_API_KEY` - Your Groq API key
- `DATABASE_URL` - PostgreSQL connection string

### Deploy Your Own

```bash
npm i -g vercel
vercel
```

## 📄 License
MIT License

This project was developed by Rishi.
