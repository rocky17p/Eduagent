# EduGen AI - Educational Content Generator (Part 2)

An AI-powered educational content generation system with a governed, auditable pipeline featuring schema validation, quantitative review, and complete audit trails.

## 🎯 Features

- **Schema-Validated Outputs**: All agent outputs validated via Pydantic
- **Quantitative Review**: Scores (1-5) for age appropriateness, correctness, clarity, coverage
- **Bounded Refinement**: Maximum 2 refinement attempts before rejection
- **Complete Audit Trail**: Every run produces a RunArtifact with full lifecycle
- **SQLite Persistence**: All runs stored with inputs, attempts, and final decisions
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

**Pass Criteria**: All scores must be >= 3

### 3. Refiner Agent
**Responsibility**: Improve content using reviewer feedback (max 2 attempts).

### 4. Tagger Agent
**Responsibility**: Classify approved content only.

**Output Schema**:
```json
{
  "subject": "Mathematics",
  "topic": "Fractions",
  "grade": 5,
  "difficulty": "Medium",
  "content_type": ["Explanation", "Quiz"],
  "blooms_level": "Understanding"
}
```

## 📊 RunArtifact (Audit Trail)

Every run produces:
```json
{
  "run_id": "uuid",
  "input": {"grade": 5, "topic": "Fractions"},
  "attempts": [
    {"attempt": 1, "draft": {...}, "review": {...}},
    {"attempt": 2, "draft": {...}, "review": {...}}
  ],
  "final": {
    "status": "approved|rejected",
    "content": {...},
    "tags": {...}
  },
  "timestamps": {"started_at": "...", "finished_at": "..."}
}
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API key (free at https://console.groq.com/keys)

### Installation

```bash
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run the application
python app.py
```

Open http://localhost:5000

## 📁 Project Structure

```
eklavya/
├── app.py                 # Flask API server
├── orchestrator.py        # Pipeline orchestration
├── database.py            # SQLite persistence
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── models/
│   └── schemas.py         # Pydantic schemas
├── agents/
│   ├── generator.py       # Generator Agent
│   ├── reviewer.py        # Reviewer Agent
│   ├── refiner.py         # Refiner Agent
│   └── tagger.py          # Tagger Agent
├── tests/
│   └── test_pipeline.py   # 3 mandatory tests
└── static/                # Web UI
```

## 📚 API Reference

### POST /generate
Run the full pipeline.

**Request:**
```json
{"grade": 5, "topic": "Fractions", "user_id": "optional"}
```

**Response:** Complete RunArtifact

### GET /history
Retrieve run history.

**Query Params:** `user_id`, `limit`

### GET /run/{run_id}
Retrieve specific run artifact.

## 🧪 Running Tests

```bash
pytest tests/ -v
```

**Tests include:**
1. Schema validation failure handling
2. Fail → refine → pass orchestration
3. Fail → refine → fail → reject orchestration

## ⚖️ Trade-offs

1. **Flask over FastAPI**: Kept Flask for consistency with Part 1
2. **SQLite + PostgreSQL**: SQLite for local dev, PostgreSQL for production
3. **Max 2 refinements**: Prevents infinite loops while allowing improvement
4. **Field-level feedback**: More actionable than general comments

## 🚀 Vercel Deployment

### Step 1: Get a Free PostgreSQL Database

Choose one of these free options:

- **Neon** (recommended): https://neon.tech - Free tier with 512MB
- **Supabase**: https://supabase.com - Free tier with 500MB
- **Vercel Postgres**: https://vercel.com/docs/storage/vercel-postgres

### Step 2: Set Environment Variables

In Vercel dashboard, add these environment variables:

```
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgres://user:password@host:5432/database
```

### Step 3: Deploy

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow prompts to link your project
```

### Step 4: Connect Database (if using Vercel Postgres)

```bash
vercel env pull .env.local
```

## 📄 License

MIT License
