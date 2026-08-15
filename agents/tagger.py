"""
Tagger Agent - Classifies approved educational content.

Responsibility:
- Classify APPROVED content only
- Add metadata: subject, difficulty, Bloom's level, content type
"""

import json
import os
import re
from groq import Groq
from pydantic import ValidationError

from models.schemas import TaggerOutput, DifficultyLevel, BloomsLevel


class TaggerAgent:
    """
    Agent responsible for tagging/classifying approved educational content.
    
    Input:
        Approved content (GeneratorOutput format) + grade + topic
    
    Output:
        TaggerOutput: {
            "subject": "Mathematics",
            "topic": "Fractions",
            "grade": 5,
            "difficulty": "Medium",
            "content_type": ["Explanation", "Quiz"],
            "blooms_level": "Understanding"
        }
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the Tagger Agent with Groq API key."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
    
    def tag(self, content: dict, grade: int, topic: str) -> dict:
        """
        Tag and classify educational content.
        
        Args:
            content: The approved content
            grade: The target grade level
            topic: The educational topic
            
        Returns:
            Dictionary with TaggerOutput structure
        """
        if not self.client:
            return self._tag_mock_response(content, grade, topic)
        
        return self._tag_with_groq(content, grade, topic)
    
    def _tag_with_groq(self, content: dict, grade: int, topic: str) -> dict:
        """Tag content using Groq API."""
        
        print(f"🏷️ Calling Groq API to tag content for topic: {topic}")
        
        content_json = json.dumps(content, indent=2)
        
        prompt = f"""You are an expert educational content classifier. Classify the following content.

CONTENT:
{content_json}

ORIGINAL TOPIC: {topic}
GRADE LEVEL: {grade}

Classify this content by:

1. **subject**: The main subject area (e.g., "Mathematics", "Science", "English", "History", "Geography", "Physics", "Chemistry", "Biology")

2. **topic**: The specific topic (use the original topic or refine it)

3. **grade**: The grade level (use {grade})

4. **difficulty**: Based on complexity for this grade level
   - "Easy" - Below grade level
   - "Medium" - At grade level
   - "Hard" - Challenging for grade level

5. **content_type**: List of content types present
   - "Explanation" if there's explanatory text
   - "Quiz" if there are MCQs
   - "Teacher Guide" if there are teacher notes

6. **blooms_level**: Primary Bloom's taxonomy level
   - "Remembering" - Recall facts
   - "Understanding" - Explain concepts
   - "Applying" - Use information
   - "Analyzing" - Break down information
   - "Evaluating" - Make judgments
   - "Creating" - Produce new work

You MUST respond with ONLY valid JSON (no markdown):
{{
    "subject": "Subject Name",
    "topic": "{topic}",
    "grade": {grade},
    "difficulty": "Easy|Medium|Hard",
    "content_type": ["Explanation", "Quiz"],
    "blooms_level": "Understanding"
}}

Classify the content now:"""

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You are an educational content classifier. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ Groq Tagger API responded successfully")
            
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
            
            parsed = json.loads(result)
            
            # Validate against schema
            validated = TaggerOutput(**parsed)
            return validated.model_dump()
            
        except Exception as e:
            print(f"❌ Groq Tagger API Error: {type(e).__name__}: {e}")
            return self._tag_mock_response(content, grade, topic)
    
    def _tag_mock_response(self, content: dict, grade: int, topic: str) -> dict:
        """Generate a mock tagging response."""
        
        print(f"📝 Using mock tagger response")
        
        # Infer subject from topic
        topic_lower = topic.lower()
        if any(word in topic_lower for word in ["math", "number", "fraction", "angle", "geometry", "algebra", "equation"]):
            subject = "Mathematics"
        elif any(word in topic_lower for word in ["science", "plant", "animal", "cell", "body", "biology"]):
            subject = "Science"
        elif any(word in topic_lower for word in ["physics", "force", "energy", "motion", "gravity"]):
            subject = "Physics"
        elif any(word in topic_lower for word in ["chemistry", "atom", "molecule", "element", "reaction"]):
            subject = "Chemistry"
        elif any(word in topic_lower for word in ["history", "war", "revolution", "empire", "ancient"]):
            subject = "History"
        elif any(word in topic_lower for word in ["geography", "country", "continent", "river", "mountain", "climate"]):
            subject = "Geography"
        elif any(word in topic_lower for word in ["english", "grammar", "writing", "literature", "poem"]):
            subject = "English"
        else:
            subject = "General Studies"
        
        # Determine difficulty based on grade
        if grade <= 4:
            difficulty = DifficultyLevel.EASY
        elif grade <= 8:
            difficulty = DifficultyLevel.MEDIUM
        else:
            difficulty = DifficultyLevel.HARD
        
        # Content types based on what's present
        content_types = []
        if content.get("explanation"):
            content_types.append("Explanation")
        if content.get("mcqs"):
            content_types.append("Quiz")
        if content.get("teacher_notes"):
            content_types.append("Teacher Guide")
        if not content_types:
            content_types = ["Explanation", "Quiz"]
        
        return {
            "subject": subject,
            "topic": topic,
            "grade": grade,
            "difficulty": difficulty.value,
            "content_type": content_types,
            "blooms_level": BloomsLevel.UNDERSTANDING.value
        }
