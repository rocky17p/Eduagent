"""
Reviewer Agent - Evaluates the Generator's output.

Responsibility:
- Evaluate educational content for quality and appropriateness
- Check age appropriateness, conceptual correctness, and clarity
- Provide structured feedback on issues found
"""

import json
import os
from groq import Groq


class ReviewerAgent:
    """
    Agent responsible for reviewing educational content.
    
    Input:
        Content JSON from Generator Agent + grade level
    
    Output:
        {
            "status": "pass" | "fail",
            "feedback": [
                "Sentence 2 is too complex for Grade 4",
                "Question 3 tests a concept not introduced"
            ]
        }
    
    Evaluation Criteria:
        - Age appropriateness
        - Conceptual correctness
        - Clarity
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
            content: The generated content with 'explanation' and 'mcqs'
            grade: The target grade level
            
        Returns:
            Dictionary with 'status' (pass/fail) and 'feedback' list
        """
        if not self.client:
            # Return mock response if no API key
            return self._review_mock_response(content, grade)
        
        return self._review_with_groq(content, grade)
    
    def _review_with_groq(self, content: dict, grade: int) -> dict:
        """Review content using Groq API."""
        
        print(f"🔍 Calling Groq API to review content for grade {grade}")
        
        content_json = json.dumps(content, indent=2)
        
        prompt = f"""You are an expert educational content reviewer. Your task is to evaluate educational content created for Grade {grade} students (approximately {grade + 5} years old).

CONTENT TO REVIEW:
{content_json}

EVALUATION CRITERIA:
1. **Age Appropriateness**: 
   - Vocabulary should match Grade {grade} level
   - Sentence complexity should be appropriate
   - Concepts should be understandable for this age group

2. **Conceptual Correctness**:
   - All facts must be accurate
   - No misconceptions or errors
   - MCQ answers must be correct

3. **Clarity**:
   - Explanation should be clear and well-structured
   - Questions should be unambiguous
   - Options should be distinct and fair

REVIEW INSTRUCTIONS:
- Be strict but fair
- If there are significant issues, status should be "fail"
- If content is acceptable (even if minor improvements possible), status should be "pass"
- Provide specific, actionable feedback

You MUST respond with ONLY valid JSON in this exact format (no markdown, no code blocks, just raw JSON):
{{
    "status": "pass" or "fail",
    "feedback": [
        "Specific feedback point 1",
        "Specific feedback point 2"
    ]
}}

If the content passes, you can include positive feedback or minor suggestions.
If the content fails, clearly explain what needs to be fixed.

Review the content now:"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an educational content reviewer. Always respond with valid JSON only, no markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
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
            
            return json.loads(result)
            
        except Exception as e:
            print(f"❌ Groq Reviewer API Error: {type(e).__name__}: {e}")
            return self._review_mock_response(content, grade)
    
    def _review_mock_response(self, content: dict, grade: int) -> dict:
        """Generate a mock review response for testing without API key."""
        
        feedback = []
        has_issues = False
        
        # Check explanation length
        explanation = content.get("explanation", "")
        word_count = len(explanation.split())
        
        if word_count < 50:
            feedback.append("Explanation is too short. Consider adding more details.")
            has_issues = True
        
        # Check if explanation matches grade level (simple heuristic)
        avg_word_length = sum(len(word) for word in explanation.split()) / max(word_count, 1)
        
        if grade <= 4 and avg_word_length > 6:
            feedback.append(f"Some words may be too complex for Grade {grade}. Consider using simpler vocabulary.")
            has_issues = True
        
        # Check MCQs
        mcqs = content.get("mcqs", [])
        
        if len(mcqs) < 3:
            feedback.append("Content should include at least 3 MCQs.")
            has_issues = True
        
        for i, mcq in enumerate(mcqs, 1):
            if len(mcq.get("options", [])) != 4:
                feedback.append(f"Question {i} should have exactly 4 options.")
                has_issues = True
            
            answer = mcq.get("answer", "")
            if answer not in ["A", "B", "C", "D"]:
                feedback.append(f"Question {i} has an invalid answer format. Should be A, B, C, or D.")
                has_issues = True
        
        # Add positive feedback if no major issues
        if not has_issues:
            feedback = [
                f"Content is appropriate for Grade {grade} level.",
                "Explanation is clear and well-structured.",
                "MCQs are well-formed and test relevant concepts."
            ]
        
        # Randomly fail first attempt for demo purposes (to show refinement)
        import random
        if not has_issues and random.random() < 0.3:  # 30% chance to fail for demo
            has_issues = True
            feedback = [
                f"Some vocabulary might be slightly advanced for Grade {grade}.",
                "Consider adding a real-world example to make the concept more relatable."
            ]
        
        return {
            "status": "fail" if has_issues else "pass",
            "feedback": feedback
        }
