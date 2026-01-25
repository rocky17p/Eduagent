"""
Generator Agent - Generates educational content for a given grade and topic.

Responsibility:
- Generate draft educational content tailored to the specified grade level
- Produce structured output with explanation, MCQs, and teacher notes
- Schema-validated output with retry on failure
"""

import json
import os
import re
from groq import Groq
from pydantic import ValidationError

from models.schemas import GeneratorOutput, GeneratorInput


class GeneratorAgent:
    """
    Agent responsible for generating educational content.
    
    Input:
        GeneratorInput: {"grade": 4, "topic": "Types of angles"}
    
    Output:
        GeneratorOutput: {
            "explanation": {"text": "...", "grade": 4},
            "mcqs": [...],
            "teacher_notes": {...}
        }
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the Generator Agent with Groq API key."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
    
    def generate(self, grade: int, topic: str, feedback: list = None, max_retries: int = 2) -> dict:
        """
        Generate educational content for the given grade and topic.
        
        Args:
            grade: The grade level (1-12)
            topic: The educational topic to cover
            feedback: Optional list of feedback for refinement
            max_retries: Maximum retries on validation failure
            
        Returns:
            Dictionary with validated GeneratorOutput structure
        """
        # Validate input
        input_data = GeneratorInput(grade=grade, topic=topic)
        
        for attempt in range(max_retries):
            try:
                if self.client:
                    raw_output = self._generate_with_groq(grade, topic, feedback)
                else:
                    raw_output = self._generate_mock_response(grade, topic, feedback)
                
                # Validate against schema
                validated = GeneratorOutput(**raw_output)
                return validated.model_dump()
                
            except ValidationError as e:
                print(f"⚠️ Schema validation failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print("🔄 Retrying generation...")
                    feedback = (feedback or []) + [f"Previous output had schema errors: {str(e)}"]
                else:
                    raise ValueError(f"Schema validation failed after {max_retries} attempts: {e}")
            except Exception as e:
                print(f"❌ Generation error: {e}")
                if attempt < max_retries - 1:
                    continue
                raise
    
    def _generate_with_groq(self, grade: int, topic: str, feedback: list = None) -> dict:
        """Generate content using Groq API."""
        
        print(f"🚀 Calling Groq API for grade {grade}, topic: {topic}")
        
        feedback_section = ""
        if feedback:
            feedback_section = f"""
IMPORTANT - Previous Feedback to Address:
{chr(10).join(f'- {f}' for f in feedback)}

Please ensure you address ALL the feedback points above in this refined version.
"""
        
        prompt = f"""You are an expert educational content creator. Generate detailed educational content for Grade {grade} students on the topic: "{topic}"

{feedback_section}

Requirements:
1. Language MUST be appropriate for Grade {grade} students (age ~{grade + 5} years)
2. Use simple vocabulary and short sentences for lower grades
3. Concepts must be factually correct
4. Create a DETAILED and engaging explanation (4-6 paragraphs with key facts and examples)
5. Generate exactly 5 multiple choice questions (MCQs) that TEST CONCEPTS FROM YOUR EXPLANATION
6. Include teacher notes with learning objectives and common misconceptions

You MUST respond with ONLY valid JSON in this exact format (no markdown, no code blocks, just raw JSON):
{{
    "explanation": {{
        "text": "A detailed, age-appropriate explanation of the topic with examples and key facts (4-6 paragraphs, no newlines inside string)",
        "grade": {grade}
    }},
    "mcqs": [
        {{
            "question": "Question testing a concept from the explanation?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 0
        }},
        {{
            "question": "Second question?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 1
        }},
        {{
            "question": "Third question?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 2
        }},
        {{
            "question": "Fourth question?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 3
        }},
        {{
            "question": "Fifth question?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 0
        }}
    ],
    "teacher_notes": {{
        "learning_objective": "By the end of this lesson, students will be able to...",
        "common_misconceptions": [
            "First common misconception about this topic",
            "Second common misconception"
        ]
    }}
}}

Generate the content now:"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an educational content generator. Always respond with valid JSON only, no markdown. Ensure all string values are on a single line with no newline characters inside strings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            print(f"✅ Groq API responded successfully")
            
            # Handle markdown code blocks
            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
            
            # Clean up control characters
            content = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)
            content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            content = re.sub(r' +', ' ', content)
            
            return json.loads(content)
            
        except Exception as e:
            print(f"❌ Groq API Error: {type(e).__name__}: {e}")
            return self._generate_mock_response(grade, topic, feedback)
    
    def _generate_mock_response(self, grade: int, topic: str, feedback: list = None) -> dict:
        """Generate a mock response for testing without API key."""
        
        print(f"📝 Using mock response for topic: {topic}")
        
        # Adjust language complexity based on grade
        if grade <= 3:
            explanation_text = f"Let's learn about {topic}! {topic} is something really interesting to learn about. It's fun to explore and discover new things! When we learn about {topic}, we can understand our world better. Scientists and teachers have studied {topic} for a long time. There are many cool facts about {topic}. Let's learn some of them together! Remember, learning is an adventure!"

        elif grade <= 6:
            explanation_text = f"Welcome to our lesson on {topic}! {topic} is an important subject that helps us understand the world around us. In this lesson, we'll explore the key concepts and ideas. Here are some important things to know about {topic}: First, {topic} has many interesting aspects to explore. Second, understanding {topic} helps us in daily life. Third, scientists study {topic} to make new discoveries. Fourth, learning about {topic} can be fun and exciting. By the end of this lesson, you'll have a better understanding of {topic} and why it matters!"

        else:
            explanation_text = f"In this lesson, we will explore {topic} in depth. {topic} is a fascinating subject that has been studied extensively. Understanding {topic} requires knowledge of various concepts and principles. Key areas of study include: Fundamentals - the basic principles underlying {topic}; Applications - how {topic} is used in real-world scenarios; History - the development of our understanding of {topic}; Modern Research - current advances in the study of {topic}; Future Directions - where the field is heading. These concepts are fundamental in understanding {topic} and its applications in various fields."

        if feedback:
            explanation_text = f"[REFINED VERSION] {explanation_text}"

        return {
            "explanation": {
                "text": explanation_text,
                "grade": grade
            },
            "mcqs": [
                {
                    "question": f"What is {topic} primarily about?",
                    "options": [f"The study of {topic}", "Something unrelated", "A type of food", "A movie genre"],
                    "correct_index": 0
                },
                {
                    "question": f"Why is it important to learn about {topic}?",
                    "options": ["It's not important", "It helps us understand the world", "Only adults need to know", "It's just for fun"],
                    "correct_index": 1
                },
                {
                    "question": f"Who studies {topic}?",
                    "options": ["Only children", "Only teachers", "Scientists and researchers", "No one"],
                    "correct_index": 2
                },
                {
                    "question": f"Where can you learn more about {topic}?",
                    "options": ["At the grocery store", "In books and schools", "Only on TV", "Nowhere"],
                    "correct_index": 1
                },
                {
                    "question": f"What is a key benefit of understanding {topic}?",
                    "options": ["There are no benefits", "It helps in problem-solving", "It makes you tired", "It's only for tests"],
                    "correct_index": 1
                }
            ],
            "teacher_notes": {
                "learning_objective": f"By the end of this lesson, students will be able to explain the key concepts of {topic} and apply them to real-world examples.",
                "common_misconceptions": [
                    f"Students often confuse {topic} with related but different concepts",
                    f"Some students believe {topic} is only theoretical and has no practical applications"
                ]
            }
        }
