"""
Refiner Agent - Improves content based on reviewer feedback.

Responsibility:
- Take draft content and reviewer feedback
- Produce improved version addressing the feedback
- Maximum 2 refinement attempts
- Each attempt is logged
"""

import json
import os
import re
from groq import Groq
from pydantic import ValidationError

from models.schemas import GeneratorOutput


class RefinerAgent:
    """
    Agent responsible for refining educational content based on feedback.
    
    Input:
        - Draft content (GeneratorOutput format)
        - Review feedback (list of FeedbackItem)
        - Grade level
        - Topic
    
    Output:
        Refined GeneratorOutput
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the Refiner Agent with Groq API key."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
    
    def refine(self, draft: dict, feedback: list, grade: int, topic: str) -> dict:
        """
        Refine content based on feedback.
        
        Args:
            draft: The original draft content
            feedback: List of feedback items from reviewer
            grade: The target grade level
            topic: The educational topic
            
        Returns:
            Dictionary with refined GeneratorOutput structure
        """
        if not self.client:
            return self._refine_mock_response(draft, feedback, grade, topic)
        
        return self._refine_with_groq(draft, feedback, grade, topic)
    
    def _refine_with_groq(self, draft: dict, feedback: list, grade: int, topic: str) -> dict:
        """Refine content using Groq API."""
        
        print(f"🔧 Calling Groq API to refine content for grade {grade}")
        
        # Format feedback for the prompt
        feedback_text = "\n".join([
            f"- Field: {f.get('field', 'unknown')}, Issue: {f.get('issue', 'unknown')}"
            for f in feedback
        ])
        
        draft_json = json.dumps(draft, indent=2)
        
        prompt = f"""You are an expert educational content refiner. Your task is to improve existing content based on specific feedback.

ORIGINAL CONTENT:
{draft_json}

FEEDBACK TO ADDRESS:
{feedback_text}

REQUIREMENTS:
1. Address EACH feedback item specifically
2. Maintain content for Grade {grade} students (age ~{grade + 5} years)
3. Keep the same overall structure
4. Improve areas mentioned in feedback
5. Ensure all facts remain correct

You MUST respond with ONLY valid JSON in the same format as the original (no markdown, no code blocks):
{{
    "explanation": {{
        "text": "Improved explanation text (single line, no newlines)",
        "grade": {grade}
    }},
    "mcqs": [
        {{
            "question": "Improved question?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 0
        }},
        ... (5 total MCQs)
    ],
    "teacher_notes": {{
        "learning_objective": "Improved learning objective",
        "common_misconceptions": ["Misconception 1", "Misconception 2"]
    }}
}}

Provide the refined content now:"""

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You are an educational content refiner. Always respond with valid JSON only, no markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            print(f"✅ Groq Refiner API responded successfully")
            
            # Handle markdown code blocks
            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
            
            # Clean control characters
            content = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)
            content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            content = re.sub(r' +', ' ', content)
            
            parsed = json.loads(content)
            
            # Validate against schema
            validated = GeneratorOutput(**parsed)
            return validated.model_dump()
            
        except Exception as e:
            print(f"❌ Groq Refiner API Error: {type(e).__name__}: {e}")
            return self._refine_mock_response(draft, feedback, grade, topic)
    
    def _refine_mock_response(self, draft: dict, feedback: list, grade: int, topic: str) -> dict:
        """Generate a mock refined response."""
        
        print(f"📝 Using mock refiner response")
        
        # Start with the draft and make improvements
        refined = draft.copy()
        
        # Improve explanation based on feedback
        explanation = refined.get("explanation", {})
        if isinstance(explanation, dict):
            text = explanation.get("text", "")
            # Add refinement marker and expand content
            refined["explanation"] = {
                "text": f"[REFINED] {text} Additionally, this topic includes important concepts that help students build a strong foundation. Real-world applications make this subject engaging and relevant to everyday life.",
                "grade": grade
            }
        
        # Ensure we have 5 MCQs
        mcqs = refined.get("mcqs", [])
        while len(mcqs) < 5:
            mcqs.append({
                "question": f"What is an important aspect of {topic}?",
                "options": ["It is relevant", "It is not studied", "It is fictional", "It is outdated"],
                "correct_index": 0
            })
        refined["mcqs"] = mcqs[:5]
        
        # Ensure teacher notes exist
        if "teacher_notes" not in refined:
            refined["teacher_notes"] = {
                "learning_objective": f"Students will understand the key concepts of {topic} and apply them to examples.",
                "common_misconceptions": [
                    f"Students may confuse {topic} with similar concepts",
                    f"Some believe {topic} has no practical applications"
                ]
            }
        
        return refined
