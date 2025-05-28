"""
Criterion evaluator module for marking individual criteria using DSPy models.

This module provides the CriterionEvaluator class that takes student code,
task descriptions, and criteria to generate scores using pre-trained DSPy models.
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

import dspy

from .dspy_config import (
    create_dynamic_signature_class,
    create_dynamic_signature_instance,
    parse_integer_answer
)

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of a criterion evaluation."""
    score: int
    confidence: float
    raw_response: str
    error: Optional[str] = None
    retry_count: int = 0


class CriterionEvaluator:
    """
    Evaluates individual criteria using DSPy models with retry logic and error handling.
    
    This class uses dynamic prompting based on maximum points and implements
    exponential backoff for API retries.
    """
    
    def __init__(self, 
                 model_name: str = "gpt-4o-mini",
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 verbosity: int = 0):
        """
        Initialize the criterion evaluator.
        
        Args:
            model_name: Name of the model to use
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds for exponential backoff
            verbosity: Logging verbosity level (0=quiet, 1=normal, 2=verbose)
        """
        self.model_name = model_name
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.verbosity = verbosity
        
        # Cache for dynamic signature instances
        self._signature_cache: Dict[str, Any] = {}
        
        if verbosity >= 2:
            logger.setLevel(logging.DEBUG)
        elif verbosity >= 1:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)
    
    def _get_signature_instance(self, max_points: int) -> Any:
        """
        Get or create a dynamic signature instance for the given max_points.
        
        Args:
            max_points: Maximum points for this criterion
            
        Returns:
            DSPy signature instance
        """
        cache_key = f"criterion_marker_{max_points}"
        
        if cache_key not in self._signature_cache:
            logger.debug(f"Creating new signature instance for max_points={max_points}")
            
            # Create dynamic signature class
            signature_class = create_dynamic_signature_class(
                class_name=f"CriterionMarker{max_points}",
                doc_string=f"Grade a code snippet according to how well it meets a specific criterion on a scale of 0-{max_points}",
                input_fields={
                    "code": "Student code snippet to evaluate",
                    "task_description": "Description of the programming task",
                    "criterion": "Specific criterion to evaluate against"
                },
                output_fields={
                    "score": f"Numeric grade between 0-{max_points}",
                    "reasoning": "Brief explanation of the score"
                },
                max_points=max_points
            )
            
            # Create instance
            self._signature_cache[cache_key] = create_dynamic_signature_instance(
                class_name=f"CriterionMarker{max_points}",
                dynamic_signature_class=signature_class
            )
        
        return self._signature_cache[cache_key]
    
    def _exponential_backoff(self, attempt: int) -> float:
        """
        Calculate delay for exponential backoff.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    def _evaluate_with_retry(self, 
                           code: str,
                           task_description: str,
                           criterion: str,
                           max_points: int) -> EvaluationResult:
        """
        Evaluate criterion with retry logic and exponential backoff.
        
        Args:
            code: Student code to evaluate
            task_description: Description of the task
            criterion: Specific criterion to evaluate
            max_points: Maximum points for this criterion
            
        Returns:
            EvaluationResult with score and metadata
        """
        signature_instance = self._get_signature_instance(max_points)
        last_error = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                if attempt > 0:
                    delay = self._exponential_backoff(attempt - 1)
                    logger.info(f"Retrying evaluation (attempt {attempt + 1}/{self.max_retries + 1}) after {delay:.1f}s delay")
                    time.sleep(delay)
                
                # Log API interaction if verbose
                if self.verbosity >= 2:
                    logger.debug(f"Evaluating criterion: {criterion[:50]}..." if len(criterion) > 50 else criterion)
                    logger.debug(f"Code length: {len(code)} characters")
                
                # Make API call
                start_time = time.time()
                response = signature_instance(
                    code=code,
                    task_description=task_description,
                    criterion=criterion
                )
                api_time = time.time() - start_time
                
                if self.verbosity >= 2:
                    logger.debug(f"API call completed in {api_time:.2f}s")
                
                # Parse the response
                raw_score = getattr(response, 'score', '')
                raw_reasoning = getattr(response, 'reasoning', '')
                
                # Parse numeric score
                parsed_score = parse_integer_answer(str(raw_score), max_points=max_points)
                
                # Calculate confidence based on response quality
                confidence = self._calculate_confidence(raw_score, raw_reasoning, parsed_score, max_points)
                
                if self.verbosity >= 1:
                    logger.info(f"Criterion evaluated: score={parsed_score}/{max_points}, confidence={confidence:.2f}")
                
                return EvaluationResult(
                    score=parsed_score,
                    confidence=confidence,
                    raw_response=f"Score: {raw_score} | Reasoning: {raw_reasoning}",
                    retry_count=attempt
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Evaluation attempt {attempt + 1} failed: {e}")
                
                # If this is the last attempt, break
                if attempt == self.max_retries:
                    break
        
        # All retries failed
        logger.error(f"All evaluation attempts failed. Last error: {last_error}")
        return EvaluationResult(
            score=0,
            confidence=0.0,
            raw_response="",
            error=last_error,
            retry_count=self.max_retries
        )
    
    def _calculate_confidence(self, 
                            raw_score: str,
                            raw_reasoning: str,
                            parsed_score: int,
                            max_points: int) -> float:
        """
        Calculate confidence level based on response quality.
        
        Args:
            raw_score: Raw score response from model
            raw_reasoning: Raw reasoning response from model
            parsed_score: Parsed numeric score
            max_points: Maximum possible points
            
        Returns:
            Confidence level between 0.0 and 1.0
        """
        confidence = 1.0
        
        # Convert to string if not already (handle None and Mock objects)
        try:
            raw_score_str = str(raw_score) if raw_score is not None else ""
            raw_reasoning_str = str(raw_reasoning) if raw_reasoning is not None else ""
        except Exception:
            raw_score_str = ""
            raw_reasoning_str = ""
        
        # Check if raw response seems completely malformed first
        if not raw_score_str and not raw_reasoning_str:
            confidence -= 0.7  # Major penalty for completely empty response
        else:
            # Apply individual penalties for partially problematic responses
            
            # Check if raw score is numeric
            is_numeric = False
            try:
                if raw_score_str.strip():
                    float(raw_score_str.strip())
                    is_numeric = True
            except (ValueError, AttributeError):
                pass
            
            if not is_numeric:
                confidence -= 0.3
            
            # Check if reasoning is provided and substantial
            if not raw_reasoning_str or len(raw_reasoning_str.strip()) < 10:
                confidence -= 0.2
        
        # Check if parsed score is in valid range (always apply this)
        if parsed_score < 0 or parsed_score > max_points:
            confidence -= 0.3
        
        # Ensure confidence is in valid range
        return max(0.0, min(1.0, confidence))
    
    def evaluate_criterion(self,
                          code: str,
                          task_description: str,
                          criterion: str,
                          max_points: int) -> EvaluationResult:
        """
        Evaluate a single criterion for student code.
        
        Args:
            code: Student code to evaluate
            task_description: Description of the programming task
            criterion: Specific criterion to evaluate against
            max_points: Maximum points for this criterion
            
        Returns:
            EvaluationResult with score, confidence, and metadata
        """
        # Validate inputs
        if not code or not code.strip():
            logger.warning("Empty code provided for evaluation")
            return EvaluationResult(
                score=0,
                confidence=1.0,
                raw_response="Empty code",
                error="EMPTY_CODE"
            )
        
        if not criterion or not criterion.strip():
            logger.error("Empty criterion provided for evaluation")
            return EvaluationResult(
                score=0,
                confidence=0.0,
                raw_response="",
                error="EMPTY_CRITERION"
            )
        
        if max_points <= 0:
            logger.error(f"Invalid max_points: {max_points}")
            return EvaluationResult(
                score=0,
                confidence=0.0,
                raw_response="",
                error="INVALID_MAX_POINTS"
            )
        
        # Check for basic syntax errors first (before placeholder check)
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            logger.info(f"Syntax error detected: {e}")
            return EvaluationResult(
                score=0,
                confidence=1.0,
                raw_response=f"Syntax error: {e}",
                error="SYNTAX_ERROR"
            )
        
        # Check for placeholder code patterns (after syntax check)
        placeholder_patterns = [
            "# your code here",
            "# your solution here",
            "# todo",
            "# implement this",
            "raise notimplementederror"
        ]
        
        code_lower = code.lower().strip()
        # Special case: lone 'pass' statement is considered placeholder
        if code_lower == "pass" or any(pattern in code_lower for pattern in placeholder_patterns) and len(code_lower) < 50:
            logger.info("Detected placeholder code")
            return EvaluationResult(
                score=0,
                confidence=1.0,
                raw_response="Placeholder code detected",
                error="PLACEHOLDER_CODE"
            )
        
        # Perform evaluation with retry logic
        return self._evaluate_with_retry(code, task_description, criterion, max_points)
    
    def evaluate_multiple_criteria(self,
                                 code: str,
                                 task_description: str,
                                 criteria: Dict[str, int]) -> Dict[str, EvaluationResult]:
        """
        Evaluate multiple criteria for the same code.
        
        Args:
            code: Student code to evaluate
            task_description: Description of the programming task
            criteria: Dictionary mapping criterion descriptions to max_points
            
        Returns:
            Dictionary mapping criterion descriptions to EvaluationResults
        """
        results = {}
        total_criteria = len(criteria)
        
        for i, (criterion, max_points) in enumerate(criteria.items(), 1):
            if self.verbosity >= 1:
                logger.info(f"Evaluating criterion {i}/{total_criteria}: {criterion[:50]}..." if len(criterion) > 50 else criterion)
            
            result = self.evaluate_criterion(code, task_description, criterion, max_points)
            results[criterion] = result
            
            # Add small delay between evaluations to avoid rate limiting
            if i < total_criteria:
                time.sleep(0.1)
        
        return results
