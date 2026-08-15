"""
Reviewer Agent - Evaluates the Generator's output.

Responsibility:
- Quantitatively evaluate educational content
- Provide scores (1-5) for age appropriateness, correctness, clarity, coverage
- Return field-level feedback with specific issues
- Decide pass/fail based on threshold (all scores >= 3)
"""

import json
import os
import re
from groq import Groq
from pydantic import ValidationError

from models.schemas import ReviewerOutput, ReviewScores, FeedbackItem

# Pass threshold: all scores must be >= 3
PASS_THRESHOLD = 3


class ReviewerAgent:
    """
    Agent responsible for reviewing educational content.
    
    Input:
        Content dict from Generator Agent + grade level
    
    Output:
        ReviewerOutput: {
            "scores": {"age_appropriateness": 4, "correctness": 5, "clarity": 4, "coverage": 3},
            "passed": true,
            "feedback": [{"field": "explanation.text", "issue": "..."}]
        }
    
    Pass Criteria:
        All scores must be >= 3
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the Reviewer Agent with Groq API key."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
    
    def review(self, content: dict, grade: int) -> dict:
        """
        Review educational content for quality and appropriateness.
        
        Args:
            content: The generated content (GeneratorOutput format)
            grade: The target grade level
            
        Returns:
            Dictionary with ReviewerOutput structure
        """
        if not self.client:
            return self._review_mock_response(content, grade)
        
        return self._review_with_groq(content, grade)
    
    def _review_with_groq(self, content: dict, grade: int) -> dict:
        """Review content using Groq API."""
        
        print(f"🔍 Calling Groq API to review content for grade {grade}")
        
        content_json = json.dumps(content, indent=2)
        
        prompt = f"""You are an expert educational content reviewer. Your task is to quantitatively evaluate educational content created for Grade {grade} students (approximately {grade + 5} years old).

CONTENT TO REVIEW:
{content_json}

EVALUATION CRITERIA (Score 1-5 for each):

1. **age_appropriateness** (1-5):
   - 5: Perfect for Grade {grade}, vocabulary and complexity ideal
   - 4: Good, minor adjustments needed
   - 3: Acceptable, some content may be slightly off-target
   - 2: Significant issues with age appropriateness
   - 1: Completely inappropriate for this grade level

2. **correctness** (1-5):
   - 5: All facts accurate, no errors
   - 4: Minor inaccuracies
   - 3: Some factual issues that should be addressed
   - 2: Significant factual errors
   - 1: Major misconceptions or wrong information

3. **clarity** (1-5):
   - 5: Crystal clear, well-structured
   - 4: Clear with minor improvements possible
   - 3: Understandable but could be clearer
   - 2: Confusing in places
   - 1: Very difficult to understand

4. **coverage** (1-5):
   - 5: Comprehensive coverage of the topic
   - 4: Good coverage, minor gaps
   - 3: Adequate coverage
   - 2: Significant gaps
   - 1: Very incomplete

PASS THRESHOLD: All scores must be >= {PASS_THRESHOLD}

For feedback, reference specific fields using JSON paths like:
- "explanation.text" for explanation issues
- "mcqs[0].question" for question issues
- "mcqs[2].correct_index" for answer issues
- "teacher_notes.learning_objective" for teacher notes issues

You MUST respond with ONLY valid JSON (no markdown, no code blocks):
{{
    "scores": {{
        "age_appropriateness": <1-5>,
        "correctness": <1-5>,
        "clarity": <1-5>,
        "coverage": <1-5>
    }},
    "passed": <true if all scores >= {PASS_THRESHOLD}, else false>,
    "feedback": [
        {{"field": "json.path.to.field", "issue": "Description of the issue"}}
    ]
}}

Review the content now:"""

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You are an educational content reviewer. Always respond with valid JSON only, no markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ Groq Reviewer API responded successfully")
            
            # Handle markdown code blocks
            if result.startswith("```"):
                parts = result.split("```")
                if len(parts) >= 2:
                    result = parts[1]
                    if result.startswith("json"):
                        result = result[4:]
                    result = result.strip()
            
            # Clean control characters
            result = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', result)
            result = result.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            result = re.sub(r' +', ' ', result)
            
            parsed = json.loads(result)
            
            # Validate and correct pass status based on threshold
            scores = parsed.get("scores", {})
            all_pass = all(
                scores.get(k, 0) >= PASS_THRESHOLD 
                for k in ["age_appropriateness", "correctness", "clarity", "coverage"]
            )
            parsed["passed"] = all_pass
            
            # Validate against schema
            validated = ReviewerOutput(**parsed)
            return validated.model_dump()
            
        except Exception as e:
            print(f"❌ Groq Reviewer API Error: {type(e).__name__}: {e}")
            return self._review_mock_response(content, grade)
    
    def _review_mock_response(self, content: dict, grade: int) -> dict:
        """Generate a mock review response for testing without API key."""
        
        print(f"📝 Using mock review response")
        
        feedback = []
        scores = {
            "age_appropriateness": 4,
            "correctness": 5,
            "clarity": 4,
            "coverage": 4
        }
        
        # Check explanation length
        explanation = content.get("explanation", {})
        explanation_text = explanation.get("text", "") if isinstance(explanation, dict) else str(explanation)
        word_count = len(explanation_text.split())
        
        if word_count < 100:
            scores["coverage"] = 2
            feedback.append({
                "field": "explanation.text",
                "issue": "Explanation is too short. Consider adding more details and examples."
            })
        
        # Check grade appropriateness
        avg_word_length = sum(len(word) for word in explanation_text.split()) / max(word_count, 1)
        if grade <= 4 and avg_word_length > 6:
            scores["age_appropriateness"] = 2
            feedback.append({
                "field": "explanation.text",
                "issue": f"Some words may be too complex for Grade {grade}. Consider using simpler vocabulary."
            })
        
        # Check MCQs
        mcqs = content.get("mcqs", [])
        if len(mcqs) < 5:
            scores["coverage"] = min(scores["coverage"], 3)
            feedback.append({
                "field": "mcqs",
                "issue": "Content should include at least 5 MCQs."
            })
        
        for i, mcq in enumerate(mcqs):
            if len(mcq.get("options", [])) != 4:
                scores["correctness"] = min(scores["correctness"], 3)
                feedback.append({
                    "field": f"mcqs[{i}].options",
                    "issue": f"Question {i+1} should have exactly 4 options."
                })
        
        # Check teacher notes
        teacher_notes = content.get("teacher_notes", {})
        if not teacher_notes.get("learning_objective"):
            scores["coverage"] = min(scores["coverage"], 3)
            feedback.append({
                "field": "teacher_notes.learning_objective",
                "issue": "Learning objective is missing."
            })
        
        # Determine pass/fail
        all_pass = all(s >= PASS_THRESHOLD for s in scores.values())
        
        # Add positive feedback if passing
        if all_pass and not feedback:
            feedback = [
                {"field": "explanation.text", "issue": "Content is well-structured and appropriate."},
                {"field": "mcqs", "issue": "MCQs effectively test the concepts covered."}
            ]
        
        return {
            "scores": scores,
            "passed": all_pass,
            "feedback": feedback
        }
