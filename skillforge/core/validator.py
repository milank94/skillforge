"""
Exercise validation engine for evaluating user responses.

This module provides LLM-powered evaluation of user answers to exercises,
with support for pattern-based validation and intelligent feedback generation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from skillforge.models.lesson import Exercise
from skillforge.utils.llm_client import BaseLLMClient


class ValidationStatus(Enum):
    """Status of a validation result."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"


@dataclass
class ValidationResult:
    """Result of validating a user's answer to an exercise.

    Attributes:
        status: Whether the answer is correct, incorrect, or partial
        score: Numerical score from 0.0 to 1.0
        feedback: Human-readable feedback message
        hints: Suggested hints if the answer is incorrect/partial
        details: Additional validation details
    """

    status: ValidationStatus
    score: float
    feedback: str
    hints: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_correct(self) -> bool:
        """Check if the answer is fully correct."""
        return self.status == ValidationStatus.CORRECT

    @property
    def is_partial(self) -> bool:
        """Check if the answer is partially correct."""
        return self.status == ValidationStatus.PARTIAL


class ExerciseValidator:
    """Validates user answers to exercises.

    Uses a combination of pattern matching for simple cases and
    LLM-powered evaluation for complex answers.
    """

    def __init__(self, llm_client: BaseLLMClient | None = None) -> None:
        """Initialize the exercise validator.

        Args:
            llm_client: LLM client for intelligent validation
        """
        self.llm_client = llm_client

    def validate(
        self,
        exercise: Exercise,
        user_answer: str,
        context: str | None = None,
    ) -> ValidationResult:
        """Validate a user's answer to an exercise.

        Args:
            exercise: The exercise being answered
            user_answer: The user's submitted answer
            context: Optional learning context for better evaluation

        Returns:
            ValidationResult with score, feedback, and hints
        """
        user_answer = user_answer.strip()

        if not user_answer:
            return ValidationResult(
                status=ValidationStatus.INCORRECT,
                score=0.0,
                feedback="No answer provided. Please try again.",
                hints=self._get_exercise_hints(exercise, hint_index=0),
            )

        # Try pattern-based validation first
        if exercise.expected_output:
            result = self._validate_with_pattern(exercise, user_answer)
            if result is not None:
                return result

        # Fall back to LLM-based validation
        if self.llm_client:
            return self._validate_with_llm(exercise, user_answer, context)

        # No LLM client and no exact match - do basic comparison
        return self._validate_basic(exercise, user_answer)

    def _validate_with_pattern(
        self, exercise: Exercise, user_answer: str
    ) -> ValidationResult | None:
        """Validate using pattern matching against expected output.

        Args:
            exercise: The exercise with expected output
            user_answer: The user's answer

        Returns:
            ValidationResult if pattern match is definitive, None otherwise
        """
        expected = exercise.expected_output
        if expected is None:
            return None

        expected_stripped = expected.strip()

        # Exact match
        if user_answer == expected_stripped:
            return ValidationResult(
                status=ValidationStatus.CORRECT,
                score=1.0,
                feedback="Correct! Well done.",
                details={"match_type": "exact"},
            )

        # Case-insensitive match
        if user_answer.lower() == expected_stripped.lower():
            return ValidationResult(
                status=ValidationStatus.CORRECT,
                score=1.0,
                feedback="Correct! Well done.",
                details={"match_type": "case_insensitive"},
            )

        # Normalized whitespace match
        normalized_answer = " ".join(user_answer.split())
        normalized_expected = " ".join(expected_stripped.split())
        if normalized_answer == normalized_expected:
            return ValidationResult(
                status=ValidationStatus.CORRECT,
                score=1.0,
                feedback="Correct! Well done.",
                details={"match_type": "normalized_whitespace"},
            )

        # Check if answer contains the expected output
        if expected_stripped.lower() in user_answer.lower():
            return ValidationResult(
                status=ValidationStatus.PARTIAL,
                score=0.7,
                feedback="Your answer contains the expected output, "
                "but includes extra content. Try to be more precise.",
                hints=self._get_exercise_hints(exercise, hint_index=0),
                details={"match_type": "contains"},
            )

        # If expected output is in the answer (reversed check)
        if user_answer.lower() in expected_stripped.lower():
            return ValidationResult(
                status=ValidationStatus.PARTIAL,
                score=0.5,
                feedback="You're on the right track, " "but your answer is incomplete.",
                hints=self._get_exercise_hints(exercise, hint_index=0),
                details={"match_type": "subset"},
            )

        # No definitive pattern match - return None to try LLM
        return None

    def _validate_basic(self, exercise: Exercise, user_answer: str) -> ValidationResult:
        """Basic validation without LLM (fallback).

        Args:
            exercise: The exercise being validated
            user_answer: The user's answer

        Returns:
            ValidationResult based on simple comparison
        """
        if exercise.expected_output is None:
            # No expected output defined - accept any non-empty answer
            return ValidationResult(
                status=ValidationStatus.PARTIAL,
                score=0.5,
                feedback="Answer received. Unable to fully validate "
                "without expected output defined.",
                details={"match_type": "no_expected_output"},
            )

        # No match at all
        return ValidationResult(
            status=ValidationStatus.INCORRECT,
            score=0.0,
            feedback="That's not quite right. Review the exercise "
            "instructions and try again.",
            hints=self._get_exercise_hints(exercise, hint_index=0),
            details={"match_type": "no_match"},
        )

    def _validate_with_llm(
        self,
        exercise: Exercise,
        user_answer: str,
        context: str | None = None,
    ) -> ValidationResult:
        """Validate using LLM for intelligent evaluation.

        Args:
            exercise: The exercise being validated
            user_answer: The user's answer
            context: Optional learning context

        Returns:
            ValidationResult from LLM evaluation
        """
        assert self.llm_client is not None

        prompt = f"""Evaluate the following user answer to a learning exercise.

Exercise Instruction: {exercise.instruction}
"""
        if exercise.expected_output:
            prompt += f"Expected Output: {exercise.expected_output}\n"

        prompt += f"""
User's Answer: {user_answer}
"""
        if context:
            prompt += f"Learning Context: {context}\n"

        prompt += """
Evaluate the answer and respond in this exact format:
Status: [correct/incorrect/partial]
Score: [0.0 to 1.0]
Feedback: [one sentence of constructive feedback]
Hint: [one helpful hint if not fully correct, or "none" if correct]
"""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system_prompt=(
                    "You are an expert programming tutor evaluating "
                    "student exercises. Be encouraging but accurate. "
                    "Give clear, specific feedback."
                ),
                temperature=0.3,
                max_tokens=256,
            )
            return self._parse_llm_response(response, exercise)
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.PARTIAL,
                score=0.5,
                feedback=f"Validation error: {e}. " "Your answer has been recorded.",
                details={"error": str(e)},
            )

    def _parse_llm_response(
        self, response: str, exercise: Exercise
    ) -> ValidationResult:
        """Parse LLM validation response into a ValidationResult.

        Args:
            response: Raw LLM response text
            exercise: The exercise being validated

        Returns:
            Parsed ValidationResult
        """
        status = ValidationStatus.PARTIAL
        score = 0.5
        feedback = "Answer evaluated."
        hints: list[str] = []

        for line in response.strip().split("\n"):
            line = line.strip()

            if line.lower().startswith("status:"):
                status_str = line.split(":", 1)[1].strip().lower()
                if status_str == "correct":
                    status = ValidationStatus.CORRECT
                elif status_str == "incorrect":
                    status = ValidationStatus.INCORRECT
                else:
                    status = ValidationStatus.PARTIAL

            elif line.lower().startswith("score:"):
                try:
                    score = float(line.split(":", 1)[1].strip())
                    score = max(0.0, min(1.0, score))
                except ValueError:
                    pass

            elif line.lower().startswith("feedback:"):
                feedback = line.split(":", 1)[1].strip()

            elif line.lower().startswith("hint:"):
                hint = line.split(":", 1)[1].strip()
                if hint.lower() != "none":
                    hints.append(hint)

        # Add exercise hints if answer is not correct
        if status != ValidationStatus.CORRECT:
            hints.extend(self._get_exercise_hints(exercise, hint_index=0))

        return ValidationResult(
            status=status,
            score=score,
            feedback=feedback,
            hints=hints,
            details={"source": "llm"},
        )

    def _get_exercise_hints(self, exercise: Exercise, hint_index: int = 0) -> list[str]:
        """Get hints from the exercise, starting at a given index.

        Args:
            exercise: The exercise to get hints from
            hint_index: Index of the first hint to return

        Returns:
            List of hint strings
        """
        if not exercise.hints:
            return []
        if hint_index >= len(exercise.hints):
            return []
        # Return one hint at a time
        return [exercise.hints[hint_index]]

    def generate_hint(
        self,
        exercise: Exercise,
        user_answer: str,
        attempt_number: int = 1,
    ) -> str:
        """Generate a contextual hint for the user.

        Args:
            exercise: The exercise the user is working on
            user_answer: The user's current answer
            attempt_number: Which attempt this is (for progressive hints)

        Returns:
            A helpful hint string
        """
        # First try exercise-defined hints
        if exercise.hints and attempt_number <= len(exercise.hints):
            return exercise.hints[attempt_number - 1]

        # Use LLM for dynamic hint generation
        if self.llm_client:
            return self._generate_llm_hint(exercise, user_answer, attempt_number)

        # Fallback hint
        return "Review the exercise instructions carefully and try again."

    def _generate_llm_hint(
        self,
        exercise: Exercise,
        user_answer: str,
        attempt_number: int,
    ) -> str:
        """Generate a hint using LLM.

        Args:
            exercise: The exercise
            user_answer: The user's current answer
            attempt_number: Which attempt this is

        Returns:
            A helpful hint string
        """
        assert self.llm_client is not None

        prompt = f"""A student is working on this exercise and needs a hint.

Exercise: {exercise.instruction}
"""
        if exercise.expected_output:
            prompt += f"Expected Answer: {exercise.expected_output}\n"

        prompt += f"""Student's Answer: {user_answer}
Attempt Number: {attempt_number}

Provide a single, concise hint that guides the student toward the correct answer
without giving it away. Make the hint progressively more specific for higher
attempt numbers.

Hint:"""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system_prompt=(
                    "You are a helpful programming tutor. Give concise, "
                    "encouraging hints without revealing the answer directly."
                ),
                temperature=0.5,
                max_tokens=128,
            )
            return response.strip()
        except Exception:
            return "Review the exercise instructions carefully and try again."
