"""
API mock response generator for testing criterion evaluation.

This module creates realistic mock API responses for:
- Perfect evaluation responses
- Partial credit responses  
- Zero score responses
- Error responses
- Edge cases and timeouts

All responses match the expected format from the DSPy evaluator.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import random


class APIResponseGenerator:
    """Generate mock API responses for testing."""
    
    def __init__(self, fixtures_dir: str = "tests/fixtures"):
        self.fixtures_dir = Path(fixtures_dir)
        self.api_mocks_dir = self.fixtures_dir / "api_mocks"
        self.api_mocks_dir.mkdir(parents=True, exist_ok=True)
    
    def create_perfect_responses(self) -> Dict[str, Any]:
        """Create perfect evaluation responses."""
        return {
            "task_2_responses": [
                {"score": 2, "confidence": 0.95, "reasoning": "Excellent data loading implementation"},
                {"score": 2, "confidence": 0.92, "reasoning": "Comprehensive data cleaning approach"},
                {"score": 2, "confidence": 0.88, "reasoning": "Correct statistical analysis methods"},
                {"score": 1, "confidence": 0.90, "reasoning": "Well-organized code structure"},
                {"score": 1, "confidence": 0.85, "reasoning": "Good documentation practices"}
            ],
            "task_3_responses": [
                {"score": 2, "confidence": 0.93, "reasoning": "Professional histogram with proper formatting"},
                {"score": 2, "confidence": 0.91, "reasoning": "Effective scatter plot implementation"},
                {"score": 2, "confidence": 0.89, "reasoning": "Excellent plot customization and labels"},
                {"score": 2, "confidence": 0.87, "reasoning": "Follows visualization best practices"},
                {"score": 1, "confidence": 0.88, "reasoning": "Clean and efficient code"},
                {"score": 1, "confidence": 0.82, "reasoning": "Good error handling for edge cases"}
            ],
            "task_4_responses": [
                {"score": 3, "confidence": 0.94, "reasoning": "Robust data preprocessing pipeline"},
                {"score": 2, "confidence": 0.90, "reasoning": "Correct feature scaling implementation"},
                {"score": 3, "confidence": 0.92, "reasoning": "Appropriate clustering algorithm choice"},
                {"score": 2, "confidence": 0.86, "reasoning": "Good parameter selection strategy"},
                {"score": 2, "confidence": 0.84, "reasoning": "Clear results interpretation"},
                {"score": 2, "confidence": 0.88, "reasoning": "Modular and reusable code design"},
                {"score": 1, "confidence": 0.83, "reasoning": "Adequate documentation"}
            ]
        }
    
    def create_partial_responses(self) -> Dict[str, Any]:
        """Create partial credit responses."""
        return {
            "task_2_responses": [
                {"score": 1, "confidence": 0.78, "reasoning": "Basic data loading, missing error handling"},
                {"score": 1, "confidence": 0.75, "reasoning": "Some data cleaning, could be more thorough"},
                {"score": 1, "confidence": 0.72, "reasoning": "Basic statistics but incomplete analysis"},
                {"score": 0, "confidence": 0.80, "reasoning": "Poor code organization"},
                {"score": 0, "confidence": 0.70, "reasoning": "Minimal documentation"}
            ],
            "task_3_responses": [
                {"score": 1, "confidence": 0.76, "reasoning": "Basic histogram but poor formatting"},
                {"score": 1, "confidence": 0.74, "reasoning": "Scatter plot created but lacks customization"},
                {"score": 0, "confidence": 0.82, "reasoning": "Missing proper labels and titles"},
                {"score": 1, "confidence": 0.68, "reasoning": "Some visualization practices followed"},
                {"score": 0, "confidence": 0.75, "reasoning": "Code works but inefficient"},
                {"score": 0, "confidence": 0.65, "reasoning": "No error handling implemented"}
            ]
        }
    
    def create_zero_responses(self) -> Dict[str, Any]:
        """Create zero score responses."""
        return {
            "missing_task_responses": [
                {"score": 0, "confidence": 0.95, "reasoning": "Task not implemented"},
                {"score": 0, "confidence": 0.93, "reasoning": "Code not found in notebook"},
                {"score": 0, "confidence": 0.90, "reasoning": "Only placeholder text present"}
            ],
            "syntax_error_responses": [
                {"score": 0, "confidence": 0.88, "reasoning": "Syntax errors prevent execution"},
                {"score": 0, "confidence": 0.85, "reasoning": "Missing parentheses and indentation errors"},
                {"score": 0, "confidence": 0.82, "reasoning": "Code cannot be parsed"}
            ],
            "incorrect_responses": [
                {"score": 0, "confidence": 0.80, "reasoning": "Incorrect algorithm implementation"},
                {"score": 0, "confidence": 0.78, "reasoning": "Wrong approach to problem"},
                {"score": 0, "confidence": 0.75, "reasoning": "Output does not match requirements"}
            ]
        }
    
    def create_error_responses(self) -> Dict[str, Any]:
        """Create error response scenarios."""
        return {
            "api_timeout_errors": [
                {"error": "TimeoutError", "message": "Request timed out after 30 seconds"},
                {"error": "ConnectionError", "message": "Failed to connect to API endpoint"},
                {"error": "RateLimitError", "message": "API rate limit exceeded"}
            ],
            "parsing_errors": [
                {"error": "ParseError", "message": "Could not parse AI response as integer"},
                {"error": "ValidationError", "message": "Response format does not match expected schema"},
                {"error": "ValueError", "message": "Score outside valid range 0-6"}
            ],
            "authentication_errors": [
                {"error": "AuthenticationError", "message": "Invalid API key"},
                {"error": "PermissionError", "message": "Insufficient permissions for model access"},
                {"error": "QuotaExceededError", "message": "Monthly usage quota exceeded"}
            ]
        }
    
    def create_edge_case_responses(self) -> Dict[str, Any]:
        """Create edge case response scenarios."""
        return {
            "ambiguous_responses": [
                {"raw_response": "The code is okay I guess", "parsed_score": None, "confidence": 0.30},
                {"raw_response": "Score: between 2 and 3", "parsed_score": None, "confidence": 0.25},
                {"raw_response": "Not sure, maybe 2.5?", "parsed_score": None, "confidence": 0.20}
            ],
            "inconsistent_responses": [
                {"score": 3, "confidence": 0.40, "reasoning": "Contradictory evaluation logic"},
                {"score": 1, "confidence": 0.35, "reasoning": "Uncertain assessment"},
                {"score": 2, "confidence": 0.30, "reasoning": "Mixed quality indicators"}
            ],
            "boundary_responses": [
                {"score": 0, "confidence": 0.99, "reasoning": "Clearly no implementation"},
                {"score": 6, "confidence": 0.98, "reasoning": "Perfect implementation exceeds requirements"},
                {"score": 3, "confidence": 0.50, "reasoning": "Exactly average performance"}
            ]
        }
    
    def create_realistic_response_sequences(self) -> Dict[str, Any]:
        """Create realistic sequences of responses for full assignments."""
        return {
            "perfect_student_sequence": {
                "total_score": 83,
                "total_possible": 83,
                "success_rate": 1.0,
                "average_confidence": 0.89,
                "responses_by_task": {
                    2: [2, 2, 2, 1, 1],  # Task 2: 8/8 points
                    3: [2, 2, 2, 2, 1, 1],  # Task 3: 10/10 points
                    4: [3, 2, 3, 2, 2, 2, 1],  # Task 4: 15/15 points
                    5: [3, 2, 3, 2, 2, 2, 1],  # Task 5: 15/15 points
                    6: [3, 3, 3, 3, 2, 1],  # Task 6: 15/15 points
                    7: [5, 4, 4, 4, 3]  # Task 7: 20/20 points
                }
            },
            "average_student_sequence": {
                "total_score": 58,
                "total_possible": 83,
                "success_rate": 0.70,
                "average_confidence": 0.74,
                "responses_by_task": {
                    2: [2, 1, 1, 1, 0],  # Task 2: 5/8 points
                    3: [1, 2, 1, 1, 1, 0],  # Task 3: 6/10 points
                    4: [2, 2, 2, 1, 2, 1, 1],  # Task 4: 11/15 points
                    5: [2, 1, 2, 2, 1, 1, 1],  # Task 5: 10/15 points
                    6: [2, 2, 2, 2, 1, 1],  # Task 6: 10/15 points
                    7: [3, 3, 3, 3, 2]  # Task 7: 14/20 points
                }
            },
            "struggling_student_sequence": {
                "total_score": 23,
                "total_possible": 83,
                "success_rate": 0.28,
                "average_confidence": 0.65,
                "responses_by_task": {
                    2: [1, 0, 1, 0, 0],  # Task 2: 2/8 points  
                    3: [0, 1, 0, 0, 0, 0],  # Task 3: 1/10 points
                    4: [1, 1, 0, 0, 1, 0, 0],  # Task 4: 3/15 points
                    5: [1, 0, 1, 1, 0, 0, 0],  # Task 5: 3/15 points
                    6: [0, 1, 0, 1, 0, 0],  # Task 6: 2/15 points
                    7: [2, 3, 2, 3, 2]  # Task 7: 12/20 points
                }
            }
        }
    
    def save_json_fixture(self, data: Dict[str, Any], filename: str):
        """Save mock responses to JSON file."""
        filepath = self.api_mocks_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def generate_all_responses(self):
        """Generate all API mock response fixtures."""
        # Perfect responses
        perfect_responses = self.create_perfect_responses()
        self.save_json_fixture(perfect_responses, "perfect_responses")
        
        # Partial responses
        partial_responses = self.create_partial_responses()
        self.save_json_fixture(partial_responses, "partial_responses")
        
        # Zero responses
        zero_responses = self.create_zero_responses()
        self.save_json_fixture(zero_responses, "zero_responses")
        
        # Error responses
        error_responses = self.create_error_responses()
        self.save_json_fixture(error_responses, "error_responses")
        
        # Edge cases
        edge_cases = self.create_edge_case_responses()
        self.save_json_fixture(edge_cases, "edge_case_responses")
        
        # Realistic sequences
        sequences = self.create_realistic_response_sequences()
        self.save_json_fixture(sequences, "response_sequences")
