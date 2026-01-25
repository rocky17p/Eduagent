"""
Test suite for the AI Educational Content Generator Pipeline.

Tests:
1. Schema validation failure handling
2. Fail → refine → pass orchestration
3. Fail → refine → fail → reject orchestration
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import GeneratorOutput, ReviewerOutput, TaggerOutput
from agents.generator import GeneratorAgent
from agents.reviewer import ReviewerAgent
from agents.refiner import RefinerAgent
from agents.tagger import TaggerAgent
from orchestrator import Orchestrator


# ==================== Test 1: Schema Validation Failure Handling ====================

class TestSchemaValidation:
    """Test schema validation failure handling."""
    
    def test_generator_invalid_output_retries(self):
        """Test that Generator retries on schema validation failure."""
        agent = GeneratorAgent(api_key=None)  # Use mock
        
        # Mock generates content without teacher_notes first, then valid
        with patch.object(agent, '_generate_with_groq') as mock_generate:
            # First call returns invalid (no teacher_notes), second returns valid
            mock_generate.side_effect = [
                # Invalid output (missing teacher_notes)
                {
                    "explanation": {"text": "Test explanation " * 20, "grade": 5},
                    "mcqs": [
                        {"question": "Q1?", "options": ["A", "B", "C", "D"], "correct_index": 0},
                        {"question": "Q2?", "options": ["A", "B", "C", "D"], "correct_index": 1},
                        {"question": "Q3?", "options": ["A", "B", "C", "D"], "correct_index": 2}
                    ]
                    # Missing teacher_notes - should fail validation
                },
                # Valid output on retry
                {
                    "explanation": {"text": "Test explanation " * 20, "grade": 5},
                    "mcqs": [
                        {"question": "Q1?", "options": ["A", "B", "C", "D"], "correct_index": 0},
                        {"question": "Q2?", "options": ["A", "B", "C", "D"], "correct_index": 1},
                        {"question": "Q3?", "options": ["A", "B", "C", "D"], "correct_index": 2}
                    ],
                    "teacher_notes": {
                        "learning_objective": "Learn fractions",
                        "common_misconceptions": ["Fractions are hard"]
                    }
                }
            ]
            
            # Enable client to trigger API path
            agent.client = Mock()
            
            result = agent.generate(5, "Fractions")
            
            # Should have retried once
            assert mock_generate.call_count == 2
            assert "teacher_notes" in result
    
    def test_generator_output_schema_valid(self):
        """Test that valid output passes schema validation."""
        valid_output = {
            "explanation": {"text": "This is a test explanation about fractions. " * 10, "grade": 5},
            "mcqs": [
                {"question": "What is 1/2?", "options": ["Half", "Quarter", "Third", "Whole"], "correct_index": 0},
                {"question": "What is 1/4?", "options": ["Half", "Quarter", "Third", "Whole"], "correct_index": 1},
                {"question": "What is 1/3?", "options": ["Half", "Quarter", "Third", "Whole"], "correct_index": 2}
            ],
            "teacher_notes": {
                "learning_objective": "Students will understand fractions",
                "common_misconceptions": ["Fractions are just division"]
            }
        }
        
        # Should not raise
        validated = GeneratorOutput(**valid_output)
        assert validated.explanation.grade == 5
        assert len(validated.mcqs) == 3
    
    def test_reviewer_output_schema_valid(self):
        """Test that valid reviewer output passes schema validation."""
        valid_output = {
            "scores": {
                "age_appropriateness": 4,
                "correctness": 5,
                "clarity": 4,
                "coverage": 3
            },
            "passed": True,
            "feedback": [
                {"field": "explanation.text", "issue": "Minor improvement possible"}
            ]
        }
        
        validated = ReviewerOutput(**valid_output)
        assert validated.passed == True
        assert validated.scores.correctness == 5


# ==================== Test 2: Fail → Refine → Pass Orchestration ====================

class TestFailRefinePass:
    """Test the fail → refine → pass flow."""
    
    def test_orchestrator_refines_on_fail(self):
        """Test that orchestrator refines content when review fails, then passes."""
        
        with patch('orchestrator.GeneratorAgent') as MockGenerator, \
             patch('orchestrator.ReviewerAgent') as MockReviewer, \
             patch('orchestrator.RefinerAgent') as MockRefiner, \
             patch('orchestrator.TaggerAgent') as MockTagger, \
             patch('orchestrator.database') as MockDB:
            
            # Setup mock agents
            mock_generator = MockGenerator.return_value
            mock_reviewer = MockReviewer.return_value
            mock_refiner = MockRefiner.return_value
            mock_tagger = MockTagger.return_value
            
            # Initial generation
            mock_generator.generate.return_value = {
                "explanation": {"text": "Initial draft", "grade": 5},
                "mcqs": [],
                "teacher_notes": {"learning_objective": "Test", "common_misconceptions": []}
            }
            
            # First review: FAIL
            # Second review: PASS
            mock_reviewer.review.side_effect = [
                {
                    "scores": {"age_appropriateness": 2, "correctness": 4, "clarity": 3, "coverage": 3},
                    "passed": False,
                    "feedback": [{"field": "explanation.text", "issue": "Too complex"}]
                },
                {
                    "scores": {"age_appropriateness": 4, "correctness": 5, "clarity": 4, "coverage": 4},
                    "passed": True,
                    "feedback": []
                }
            ]
            
            # Refiner returns improved content
            mock_refiner.refine.return_value = {
                "explanation": {"text": "Refined and improved", "grade": 5},
                "mcqs": [],
                "teacher_notes": {"learning_objective": "Test", "common_misconceptions": []}
            }
            
            # Tagger returns tags
            mock_tagger.tag.return_value = {
                "subject": "Mathematics",
                "topic": "Fractions",
                "grade": 5,
                "difficulty": "Medium",
                "content_type": ["Explanation"],
                "blooms_level": "Understanding"
            }
            
            # Run orchestrator
            orch = Orchestrator(api_key="test")
            result = orch.run(5, "Fractions")
            
            # Assertions
            assert result["final"]["status"] == "approved"
            assert len(result["attempts"]) == 2  # Initial + 1 refinement
            assert mock_refiner.refine.called
            assert mock_tagger.tag.called


# ==================== Test 3: Fail → Refine → Fail → Reject ====================

class TestFailRefineFailReject:
    """Test the fail → refine → fail → reject flow."""
    
    def test_orchestrator_rejects_after_max_attempts(self):
        """Test that orchestrator rejects after max refinement attempts."""
        
        with patch('orchestrator.GeneratorAgent') as MockGenerator, \
             patch('orchestrator.ReviewerAgent') as MockReviewer, \
             patch('orchestrator.RefinerAgent') as MockRefiner, \
             patch('orchestrator.TaggerAgent') as MockTagger, \
             patch('orchestrator.database') as MockDB:
            
            # Setup mock agents
            mock_generator = MockGenerator.return_value
            mock_reviewer = MockReviewer.return_value
            mock_refiner = MockRefiner.return_value
            mock_tagger = MockTagger.return_value
            
            # Initial generation
            mock_generator.generate.return_value = {
                "explanation": {"text": "Bad content", "grade": 5},
                "mcqs": [],
                "teacher_notes": {"learning_objective": "Test", "common_misconceptions": []}
            }
            
            # All reviews: FAIL (always returns low scores)
            mock_reviewer.review.return_value = {
                "scores": {"age_appropriateness": 1, "correctness": 2, "clarity": 1, "coverage": 2},
                "passed": False,
                "feedback": [{"field": "explanation.text", "issue": "Completely inappropriate"}]
            }
            
            # Refiner tries but content still bad
            mock_refiner.refine.return_value = {
                "explanation": {"text": "Still bad content", "grade": 5},
                "mcqs": [],
                "teacher_notes": {"learning_objective": "Test", "common_misconceptions": []}
            }
            
            # Run orchestrator
            orch = Orchestrator(api_key="test")
            result = orch.run(5, "Fractions")
            
            # Assertions
            assert result["final"]["status"] == "rejected"
            assert len(result["attempts"]) == 3  # Initial + 2 refinements (max)
            assert "rejection_reason" in result["final"]
            assert not mock_tagger.tag.called  # Tagger should NOT be called for rejected content


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
