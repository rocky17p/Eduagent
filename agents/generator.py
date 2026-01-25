"""
Generator Agent - Generates educational content for a given grade and topic.

Responsibility:
- Generate draft educational content tailored to the specified grade level
- Produce structured output with explanation and MCQs
- Incorporate feedback for refinement when provided
"""

import json
import os
from groq import Groq


class GeneratorAgent:
    """
    Agent responsible for generating educational content.
    
    Input:
        {
            "grade": 4,
            "topic": "Types of angles"
        }
    
    Output:
        {
            "explanation": "...",
            "mcqs": [
                {
                    "question": "...",
                    "options": ["A", "B", "C", "D"],
                    "answer": "B"
                }
            ]
        }
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the Generator Agent with Groq API key."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
    
    def generate(self, grade: int, topic: str, feedback: list = None) -> dict:
        """
        Generate educational content for the given grade and topic.
        
        Args:
            grade: The grade level (1-12)
            topic: The educational topic to cover
            feedback: Optional list of feedback from reviewer for refinement
            
        Returns:
            Dictionary with 'explanation' and 'mcqs' keys
        """
        if not self.client:
            # Return mock response if no API key
            return self._generate_mock_response(grade, topic, feedback)
        
        return self._generate_with_groq(grade, topic, feedback)
    
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

IMPORTANT: The MCQs MUST be based on specific facts and concepts mentioned in your explanation. Each question should test understanding of something you taught in the explanation.

You MUST respond with ONLY valid JSON in this exact format (no markdown, no code blocks, just raw JSON):
{{
    "explanation": "A detailed, age-appropriate explanation of the topic with examples and key facts (4-6 paragraphs)",
    "mcqs": [
        {{
            "question": "Question testing a concept from the explanation?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "A"
        }},
        {{
            "question": "Second question based on explanation?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "B"
        }},
        {{
            "question": "Third question based on explanation?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "C"
        }},
        {{
            "question": "Fourth question based on explanation?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "D"
        }},
        {{
            "question": "Fifth question based on explanation?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "A"
        }}
    ]
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
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            print(f"✅ Groq API responded successfully")
            
            # Try to parse JSON from the response
            # Handle cases where response might have markdown code blocks
            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
            
            # Clean up control characters that break JSON parsing
            import re
            # Replace control characters inside strings with spaces
            content = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)
            # Fix common JSON issues
            content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            # Remove multiple spaces
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
            explanation = f"""Let's learn about {topic}! 

{topic} is something really interesting to learn about. It's fun to explore and discover new things!

When we learn about {topic}, we can understand our world better. Scientists and teachers have studied {topic} for a long time.

There are many cool facts about {topic}. Let's learn some of them together!"""

        elif grade <= 6:
            explanation = f"""Welcome to our lesson on {topic}!

{topic} is an important subject that helps us understand the world around us. In this lesson, we'll explore the key concepts and ideas.

Here are some important things to know about {topic}:
1. **Key Concept 1**: {topic} has many interesting aspects to explore
2. **Key Concept 2**: Understanding {topic} helps us in daily life
3. **Key Concept 3**: Scientists study {topic} to make new discoveries
4. **Key Concept 4**: Learning about {topic} can be fun and exciting

By the end of this lesson, you'll have a better understanding of {topic} and why it matters!"""

        else:
            explanation = f"""In this lesson, we will explore {topic} in depth.

{topic} is a fascinating subject that has been studied extensively. Understanding {topic} requires knowledge of various concepts and principles.

Key Areas of Study:
1. **Fundamentals**: The basic principles underlying {topic}
2. **Applications**: How {topic} is used in real-world scenarios
3. **History**: The development of our understanding of {topic}
4. **Modern Research**: Current advances in the study of {topic}
5. **Future Directions**: Where the field is heading

These concepts are fundamental in understanding {topic} and its applications in various fields."""

        # Add refinement note if feedback was provided
        if feedback:
            explanation = f"[REFINED VERSION - Addressed feedback]\n\n{explanation}"

        return {
            "explanation": explanation,
            "mcqs": [
                {
                    "question": f"What is {topic} primarily about?",
                    "options": [
                        f"The study of {topic}",
                        "Something unrelated",
                        "A type of food",
                        "A movie genre"
                    ],
                    "answer": "A"
                },
                {
                    "question": f"Why is it important to learn about {topic}?",
                    "options": [
                        "It's not important",
                        "It helps us understand the world",
                        "Only adults need to know",
                        "It's just for fun"
                    ],
                    "answer": "B"
                },
                {
                    "question": f"Who studies {topic}?",
                    "options": [
                        "Only children",
                        "Only teachers",
                        "Scientists and researchers",
                        "No one"
                    ],
                    "answer": "C"
                },
                {
                    "question": f"Where can you learn more about {topic}?",
                    "options": [
                        "At the grocery store",
                        "In books and schools",
                        "Only on TV",
                        "Nowhere"
                    ],
                    "answer": "B"
                },
                {
                    "question": f"What is a key benefit of understanding {topic}?",
                    "options": [
                        "There are no benefits",
                        "It helps in problem-solving",
                        "It makes you tired",
                        "It's only for tests"
                    ],
                    "answer": "B"
                }
            ]
        }
