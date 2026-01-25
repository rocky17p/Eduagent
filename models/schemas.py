"""
Pydantic Schema Models for the AI Educational Content Generator.

These schemas ensure strict validation of all agent inputs and outputs.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class BloomsLevel(str, Enum):
    REMEMBERING = "Remembering"
    UNDERSTANDING = "Understanding"
    APPLYING = "Applying"
    ANALYZING = "Analyzing"
    EVALUATING = "Evaluating"
    CREATING = "Creating"


# ==================== Generator Schemas ====================

class GeneratorInput(BaseModel):
    """Input schema for the Generator Agent."""
    grade: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    topic: str = Field(..., min_length=2, max_length=200, description="Educational topic")


class Explanation(BaseModel):
    """Explanation section of the generated content."""
    text: str = Field(..., min_length=50, description="Detailed explanation text")
    grade: int = Field(..., ge=1, le=12, description="Target grade level")


class MCQ(BaseModel):
    """Multiple Choice Question schema."""
    question: str = Field(..., min_length=10, description="Question text")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 options")
    correct_index: int = Field(..., ge=0, le=3, description="Index of correct answer (0-3)")
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v):
        if len(v) != 4:
            raise ValueError('Must have exactly 4 options')
        return v


class TeacherNotes(BaseModel):
    """Teacher notes section."""
    learning_objective: str = Field(..., min_length=10, description="Learning objective")
    common_misconceptions: List[str] = Field(..., min_length=1, description="Common misconceptions")


class GeneratorOutput(BaseModel):
    """Output schema for the Generator Agent."""
    explanation: Explanation
    mcqs: List[MCQ] = Field(..., min_length=3, description="At least 3 MCQs")
    teacher_notes: TeacherNotes


# ==================== Reviewer Schemas ====================

class ReviewScores(BaseModel):
    """Quantitative review scores (1-5 scale)."""
    age_appropriateness: int = Field(..., ge=1, le=5, description="Age appropriateness score")
    correctness: int = Field(..., ge=1, le=5, description="Factual correctness score")
    clarity: int = Field(..., ge=1, le=5, description="Clarity and structure score")
    coverage: int = Field(..., ge=1, le=5, description="Topic coverage score")


class FeedbackItem(BaseModel):
    """Individual feedback item with field reference."""
    field: str = Field(..., description="JSON path to the field with issue")
    issue: str = Field(..., description="Description of the issue")


class ReviewerOutput(BaseModel):
    """Output schema for the Reviewer Agent."""
    scores: ReviewScores
    passed: bool = Field(..., description="Whether content passed review")
    feedback: List[FeedbackItem] = Field(default_factory=list, description="List of feedback items")
    
    @property
    def total_score(self) -> int:
        """Calculate total score out of 20."""
        return (
            self.scores.age_appropriateness +
            self.scores.correctness +
            self.scores.clarity +
            self.scores.coverage
        )


# ==================== Tagger Schemas ====================

class TaggerOutput(BaseModel):
    """Output schema for the Tagger Agent."""
    subject: str = Field(..., description="Subject area (e.g., Mathematics)")
    topic: str = Field(..., description="Specific topic")
    grade: int = Field(..., ge=1, le=12, description="Grade level")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    content_type: List[str] = Field(..., description="Types of content")
    blooms_level: BloomsLevel = Field(..., description="Bloom's taxonomy level")


# ==================== Run Artifact Schemas ====================

class AttemptRecord(BaseModel):
    """Record of a single generation/refinement attempt."""
    attempt: int = Field(..., ge=1, description="Attempt number")
    draft: Optional[dict] = Field(None, description="Generated/refined content")
    review: Optional[dict] = Field(None, description="Review output")
    validation_error: Optional[str] = Field(None, description="Schema validation error if any")


class FinalResult(BaseModel):
    """Final result of the pipeline."""
    status: Literal["approved", "rejected"] = Field(..., description="Final status")
    content: Optional[dict] = Field(None, description="Approved content (if any)")
    tags: Optional[dict] = Field(None, description="Tags (if approved)")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection (if rejected)")


class Timestamps(BaseModel):
    """Timestamps for the run."""
    started_at: datetime = Field(..., description="When the run started")
    finished_at: Optional[datetime] = Field(None, description="When the run finished")


class RunArtifact(BaseModel):
    """Complete audit trail for a single run."""
    run_id: str = Field(..., description="Unique run identifier")
    input: GeneratorInput = Field(..., description="Original input")
    attempts: List[AttemptRecord] = Field(default_factory=list, description="All attempts")
    final: Optional[FinalResult] = Field(None, description="Final result")
    timestamps: Timestamps = Field(..., description="Run timestamps")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
