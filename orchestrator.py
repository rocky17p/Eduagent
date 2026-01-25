"""
Orchestrator - Manages the complete content generation pipeline.

Responsibility:
- Coordinate all agents (Generator, Reviewer, Refiner, Tagger)
- Produce RunArtifact with complete audit trail
- Handle bounded retries (max 2 refinements)
- Deterministic flow with explainable decisions
"""

import uuid
from datetime import datetime
from typing import Optional

from agents import GeneratorAgent, ReviewerAgent, RefinerAgent, TaggerAgent
from models.schemas import RunArtifact, AttemptRecord, FinalResult, Timestamps, GeneratorInput
import database


# Maximum refinement attempts
MAX_REFINEMENT_ATTEMPTS = 2


class Orchestrator:
    """
    Orchestrates the complete content generation pipeline.
    
    Flow:
        1. Generate initial draft
        2. Review draft
        3. If fail → Refine (up to MAX_REFINEMENT_ATTEMPTS times)
        4. If still fail → Reject
        5. If pass → Tag content
        6. Save and return RunArtifact
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the orchestrator with all agents."""
        self.generator = GeneratorAgent(api_key=api_key)
        self.reviewer = ReviewerAgent(api_key=api_key)
        self.refiner = RefinerAgent(api_key=api_key)
        self.tagger = TaggerAgent(api_key=api_key)
    
    def run(self, grade: int, topic: str, user_id: str = None) -> dict:
        """
        Run the complete content generation pipeline.
        
        Args:
            grade: Target grade level (1-12)
            topic: Educational topic
            user_id: Optional user identifier for history
            
        Returns:
            Complete RunArtifact with audit trail
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow().isoformat()
        attempts = []
        
        print(f"\n{'='*60}")
        print(f"🎯 Starting pipeline run: {run_id}")
        print(f"   Grade: {grade}, Topic: {topic}")
        print(f"{'='*60}\n")
        
        # Attempt 1: Initial generation
        attempt_num = 1
        current_draft = None
        current_review = None
        validation_error = None
        
        try:
            print(f"📝 Attempt {attempt_num}: Generating initial draft...")
            current_draft = self.generator.generate(grade, topic)
            
            print(f"🔍 Attempt {attempt_num}: Reviewing draft...")
            current_review = self.reviewer.review(current_draft, grade)
            
        except ValueError as e:
            validation_error = str(e)
            print(f"❌ Attempt {attempt_num}: Validation error - {e}")
        except Exception as e:
            validation_error = str(e)
            print(f"❌ Attempt {attempt_num}: Error - {e}")
        
        attempts.append({
            "attempt": attempt_num,
            "draft": current_draft,
            "review": current_review,
            "validation_error": validation_error
        })
        
        # Refinement loop (up to MAX_REFINEMENT_ATTEMPTS)
        refinement_count = 0
        while (
            current_review and 
            not current_review.get("passed", False) and 
            refinement_count < MAX_REFINEMENT_ATTEMPTS and
            current_draft is not None
        ):
            refinement_count += 1
            attempt_num += 1
            
            print(f"\n🔧 Attempt {attempt_num}: Refining based on feedback...")
            
            feedback = current_review.get("feedback", [])
            validation_error = None
            
            try:
                # Refine the content
                current_draft = self.refiner.refine(
                    current_draft, 
                    feedback, 
                    grade, 
                    topic
                )
                
                # Review again
                print(f"🔍 Attempt {attempt_num}: Re-reviewing refined content...")
                current_review = self.reviewer.review(current_draft, grade)
                
            except ValueError as e:
                validation_error = str(e)
                print(f"❌ Attempt {attempt_num}: Validation error - {e}")
            except Exception as e:
                validation_error = str(e)
                print(f"❌ Attempt {attempt_num}: Error - {e}")
            
            attempts.append({
                "attempt": attempt_num,
                "draft": current_draft,
                "review": current_review,
                "validation_error": validation_error
            })
        
        # Determine final status
        final_content = None
        final_tags = None
        final_status = None
        rejection_reason = None
        
        if current_review and current_review.get("passed", False):
            final_status = "approved"
            final_content = current_draft
            
            # Tag approved content
            print(f"\n🏷️ Content approved! Tagging...")
            final_tags = self.tagger.tag(current_draft, grade, topic)
            print(f"✅ Pipeline complete: APPROVED")
            
        else:
            final_status = "rejected"
            if validation_error:
                rejection_reason = f"Schema validation failed: {validation_error}"
            elif current_review:
                scores = current_review.get("scores", {})
                low_scores = [k for k, v in scores.items() if v < 3]
                rejection_reason = f"Failed review after {MAX_REFINEMENT_ATTEMPTS} refinement attempts. Low scores: {low_scores}"
            else:
                rejection_reason = "Generation failed completely"
            print(f"❌ Pipeline complete: REJECTED - {rejection_reason}")
        
        finished_at = datetime.utcnow().isoformat()
        
        # Build RunArtifact
        artifact = {
            "run_id": run_id,
            "input": {
                "grade": grade,
                "topic": topic
            },
            "attempts": attempts,
            "final": {
                "status": final_status,
                "content": final_content,
                "tags": final_tags,
                "rejection_reason": rejection_reason
            },
            "timestamps": {
                "started_at": started_at,
                "finished_at": finished_at
            }
        }
        
        # Save to database
        database.save_run_artifact(artifact, user_id)
        
        print(f"\n{'='*60}")
        print(f"📊 Run {run_id} completed")
        print(f"   Status: {final_status}")
        print(f"   Attempts: {len(attempts)}")
        print(f"   Duration: {started_at} → {finished_at}")
        print(f"{'='*60}\n")
        
        return artifact
