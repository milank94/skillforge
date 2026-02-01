"""Tests for the exercise validator."""

from unittest.mock import Mock

import pytest

from skillforge.core.validator import (
    ExerciseValidator,
    ValidationResult,
    ValidationStatus,
)
from skillforge.models.lesson import Exercise

# --- Fixtures ---


@pytest.fixture
def simple_exercise() -> Exercise:
    """Exercise with an expected output."""
    return Exercise(
        id="ex-1",
        instruction="What command lists files in the current directory?",
        expected_output="ls",
        hints=["Think about a two-letter command", "It starts with 'l'"],
    )


@pytest.fixture
def no_output_exercise() -> Exercise:
    """Exercise without an expected output."""
    return Exercise(
        id="ex-2",
        instruction="Write a Python function that adds two numbers.",
        expected_output=None,
        hints=["Use the def keyword", "Remember to return the result"],
    )


@pytest.fixture
def no_hints_exercise() -> Exercise:
    """Exercise without hints."""
    return Exercise(
        id="ex-3",
        instruction="What is 2 + 2?",
        expected_output="4",
        hints=[],
    )


# --- ValidationResult Tests ---


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_correct_result(self):
        """Test correct validation result."""
        result = ValidationResult(
            status=ValidationStatus.CORRECT,
            score=1.0,
            feedback="Well done!",
        )
        assert result.is_correct is True
        assert result.is_partial is False
        assert result.score == 1.0

    def test_partial_result(self):
        """Test partial validation result."""
        result = ValidationResult(
            status=ValidationStatus.PARTIAL,
            score=0.5,
            feedback="Almost there.",
        )
        assert result.is_correct is False
        assert result.is_partial is True

    def test_incorrect_result(self):
        """Test incorrect validation result."""
        result = ValidationResult(
            status=ValidationStatus.INCORRECT,
            score=0.0,
            feedback="Try again.",
        )
        assert result.is_correct is False
        assert result.is_partial is False

    def test_result_with_hints(self):
        """Test result with hints."""
        result = ValidationResult(
            status=ValidationStatus.INCORRECT,
            score=0.0,
            feedback="Try again.",
            hints=["Hint 1", "Hint 2"],
        )
        assert len(result.hints) == 2

    def test_result_with_details(self):
        """Test result with details."""
        result = ValidationResult(
            status=ValidationStatus.CORRECT,
            score=1.0,
            feedback="Correct!",
            details={"match_type": "exact"},
        )
        assert result.details["match_type"] == "exact"


# --- ValidationStatus Tests ---


class TestValidationStatus:
    """Tests for ValidationStatus enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert ValidationStatus.CORRECT.value == "correct"
        assert ValidationStatus.INCORRECT.value == "incorrect"
        assert ValidationStatus.PARTIAL.value == "partial"


# --- Pattern Validation Tests ---


class TestPatternValidation:
    """Tests for pattern-based validation."""

    def test_exact_match(self, simple_exercise):
        """Test exact match validation."""
        validator = ExerciseValidator()
        result = validator.validate(simple_exercise, "ls")
        assert result.is_correct
        assert result.score == 1.0
        assert result.details["match_type"] == "exact"

    def test_case_insensitive_match(self, simple_exercise):
        """Test case-insensitive match."""
        validator = ExerciseValidator()
        result = validator.validate(simple_exercise, "LS")
        assert result.is_correct
        assert result.score == 1.0
        assert result.details["match_type"] == "case_insensitive"

    def test_whitespace_normalization(self):
        """Test whitespace normalization match."""
        exercise = Exercise(
            id="ex-ws",
            instruction="Write the command",
            expected_output="git status",
        )
        validator = ExerciseValidator()
        result = validator.validate(exercise, "git  status")
        assert result.is_correct
        assert result.details["match_type"] == "normalized_whitespace"

    def test_answer_contains_expected(self):
        """Test when answer contains the expected output."""
        exercise = Exercise(
            id="ex-contains",
            instruction="What command?",
            expected_output="ls",
            hints=["It's a short command"],
        )
        validator = ExerciseValidator()
        result = validator.validate(exercise, "ls -la")
        assert result.is_partial
        assert result.score == 0.7
        assert result.details["match_type"] == "contains"

    def test_answer_is_subset_of_expected(self):
        """Test when answer is a subset of the expected output."""
        exercise = Exercise(
            id="ex-subset",
            instruction="Type the full command",
            expected_output="docker run nginx",
            hints=["Include the image name"],
        )
        validator = ExerciseValidator()
        result = validator.validate(exercise, "docker")
        assert result.is_partial
        assert result.score == 0.5
        assert result.details["match_type"] == "subset"

    def test_no_match(self, simple_exercise):
        """Test when answer doesn't match at all."""
        validator = ExerciseValidator()
        result = validator.validate(simple_exercise, "pwd")
        assert result.status == ValidationStatus.INCORRECT
        assert result.score == 0.0

    def test_empty_answer(self, simple_exercise):
        """Test validation with empty answer."""
        validator = ExerciseValidator()
        result = validator.validate(simple_exercise, "")
        assert result.status == ValidationStatus.INCORRECT
        assert result.score == 0.0
        assert "No answer" in result.feedback

    def test_whitespace_only_answer(self, simple_exercise):
        """Test validation with whitespace-only answer."""
        validator = ExerciseValidator()
        result = validator.validate(simple_exercise, "   ")
        assert result.status == ValidationStatus.INCORRECT
        assert result.score == 0.0

    def test_answer_stripped(self):
        """Test that answer is stripped before validation."""
        exercise = Exercise(
            id="ex-strip",
            instruction="Command?",
            expected_output="ls",
        )
        validator = ExerciseValidator()
        result = validator.validate(exercise, "  ls  ")
        assert result.is_correct


# --- Basic Validation Tests (no LLM) ---


class TestBasicValidation:
    """Tests for basic validation without LLM."""

    def test_no_expected_output_accepts_answer(self, no_output_exercise):
        """Test that exercises without expected output accept any answer."""
        validator = ExerciseValidator()
        result = validator.validate(no_output_exercise, "def add(a, b): return a + b")
        assert result.is_partial
        assert result.score == 0.5
        assert result.details["match_type"] == "no_expected_output"

    def test_incorrect_with_no_llm(self, simple_exercise):
        """Test incorrect answer without LLM falls back to basic."""
        validator = ExerciseValidator()
        result = validator.validate(simple_exercise, "completely wrong")
        assert result.status == ValidationStatus.INCORRECT
        assert result.score == 0.0
        assert result.details["match_type"] == "no_match"


# --- LLM Validation Tests ---


class TestLLMValidation:
    """Tests for LLM-powered validation."""

    def test_llm_validation_correct(self, no_output_exercise):
        """Test LLM validation returns correct result."""
        mock_client = Mock()
        mock_client.generate.return_value = (
            "Status: correct\n"
            "Score: 1.0\n"
            "Feedback: Perfect implementation!\n"
            "Hint: none"
        )

        validator = ExerciseValidator(llm_client=mock_client)
        result = validator.validate(no_output_exercise, "def add(a, b): return a + b")

        assert result.is_correct
        assert result.score == 1.0
        assert result.feedback == "Perfect implementation!"
        assert result.details["source"] == "llm"

    def test_llm_validation_incorrect(self, no_output_exercise):
        """Test LLM validation returns incorrect result."""
        mock_client = Mock()
        mock_client.generate.return_value = (
            "Status: incorrect\n"
            "Score: 0.2\n"
            "Feedback: Your function doesn't return a value.\n"
            "Hint: Make sure to use the return keyword."
        )

        validator = ExerciseValidator(llm_client=mock_client)
        result = validator.validate(no_output_exercise, "def add(a, b): pass")

        assert result.status == ValidationStatus.INCORRECT
        assert result.score == 0.2
        assert "return" in result.feedback.lower()
        assert len(result.hints) > 0

    def test_llm_validation_partial(self, no_output_exercise):
        """Test LLM validation returns partial result."""
        mock_client = Mock()
        mock_client.generate.return_value = (
            "Status: partial\n"
            "Score: 0.6\n"
            "Feedback: Good start, but missing type hints.\n"
            "Hint: Consider adding type annotations."
        )

        validator = ExerciseValidator(llm_client=mock_client)
        result = validator.validate(no_output_exercise, "def add(a, b): return a + b")

        assert result.is_partial
        assert result.score == 0.6

    def test_llm_validation_with_context(self, no_output_exercise):
        """Test that context is passed to LLM."""
        mock_client = Mock()
        mock_client.generate.return_value = (
            "Status: correct\nScore: 1.0\n" "Feedback: Correct!\nHint: none"
        )

        validator = ExerciseValidator(llm_client=mock_client)
        context = "Student is learning Python basics"
        validator.validate(no_output_exercise, "def add(a, b): return a + b", context)

        call_args = mock_client.generate.call_args
        assert context in call_args[1]["prompt"]

    def test_llm_validation_error_handling(self, no_output_exercise):
        """Test LLM validation handles errors gracefully."""
        mock_client = Mock()
        mock_client.generate.side_effect = Exception("API Error")

        validator = ExerciseValidator(llm_client=mock_client)
        result = validator.validate(no_output_exercise, "def add(a, b): return a + b")

        assert result.is_partial
        assert result.score == 0.5
        assert "error" in result.details

    def test_llm_fallback_for_no_pattern_match(self, simple_exercise):
        """Test LLM is used when pattern matching fails."""
        mock_client = Mock()
        mock_client.generate.return_value = (
            "Status: correct\nScore: 0.9\n" "Feedback: Good alternative!\nHint: none"
        )

        validator = ExerciseValidator(llm_client=mock_client)
        result = validator.validate(simple_exercise, "dir")

        assert mock_client.generate.called
        assert result.score == 0.9

    def test_llm_score_clamped(self, no_output_exercise):
        """Test that LLM scores are clamped to [0.0, 1.0]."""
        mock_client = Mock()
        mock_client.generate.return_value = (
            "Status: correct\nScore: 1.5\n" "Feedback: Correct!\nHint: none"
        )

        validator = ExerciseValidator(llm_client=mock_client)
        result = validator.validate(no_output_exercise, "answer")

        assert result.score == 1.0

    def test_llm_negative_score_clamped(self, no_output_exercise):
        """Test that negative LLM scores are clamped to 0.0."""
        mock_client = Mock()
        mock_client.generate.return_value = (
            "Status: incorrect\nScore: -0.5\n" "Feedback: Wrong.\nHint: Try again."
        )

        validator = ExerciseValidator(llm_client=mock_client)
        result = validator.validate(no_output_exercise, "answer")

        assert result.score == 0.0

    def test_llm_malformed_response(self, no_output_exercise):
        """Test handling of malformed LLM response."""
        mock_client = Mock()
        mock_client.generate.return_value = "Some random text without format"

        validator = ExerciseValidator(llm_client=mock_client)
        result = validator.validate(no_output_exercise, "answer")

        # Should use defaults
        assert result.status == ValidationStatus.PARTIAL
        assert result.score == 0.5


# --- Hint Generation Tests ---


class TestHintGeneration:
    """Tests for hint generation."""

    def test_get_first_hint(self, simple_exercise):
        """Test getting the first hint from exercise."""
        validator = ExerciseValidator()
        hint = validator.generate_hint(simple_exercise, "wrong", attempt_number=1)
        assert hint == "Think about a two-letter command"

    def test_get_second_hint(self, simple_exercise):
        """Test getting the second hint from exercise."""
        validator = ExerciseValidator()
        hint = validator.generate_hint(simple_exercise, "wrong", attempt_number=2)
        assert hint == "It starts with 'l'"

    def test_hint_beyond_available(self, simple_exercise):
        """Test hint request beyond available hints uses fallback."""
        validator = ExerciseValidator()
        hint = validator.generate_hint(simple_exercise, "wrong", attempt_number=3)
        assert "Review the exercise" in hint

    def test_hint_no_hints_defined(self, no_hints_exercise):
        """Test hint when no hints are defined."""
        validator = ExerciseValidator()
        hint = validator.generate_hint(no_hints_exercise, "wrong", attempt_number=1)
        assert "Review the exercise" in hint

    def test_llm_hint_generation(self, simple_exercise):
        """Test LLM-based hint generation."""
        mock_client = Mock()
        mock_client.generate.return_value = "Try using a shorter command."

        validator = ExerciseValidator(llm_client=mock_client)
        hint = validator.generate_hint(
            simple_exercise, "wrong answer", attempt_number=3
        )

        assert mock_client.generate.called
        assert hint == "Try using a shorter command."

    def test_llm_hint_error_fallback(self, simple_exercise):
        """Test LLM hint generation falls back on error."""
        mock_client = Mock()
        mock_client.generate.side_effect = Exception("API Error")

        validator = ExerciseValidator(llm_client=mock_client)
        hint = validator.generate_hint(simple_exercise, "wrong", attempt_number=3)

        assert "Review the exercise" in hint

    def test_hints_returned_in_validation(self, simple_exercise):
        """Test that hints are included in validation results."""
        validator = ExerciseValidator()
        result = validator.validate(simple_exercise, "")
        assert len(result.hints) > 0
        assert result.hints[0] == "Think about a two-letter command"


# --- Integration-style Tests ---


class TestValidationWorkflow:
    """Tests for validation workflows."""

    def test_progressive_validation(self, simple_exercise):
        """Test that validation works across multiple attempts."""
        validator = ExerciseValidator()

        # First attempt - wrong
        result1 = validator.validate(simple_exercise, "pwd")
        assert result1.status == ValidationStatus.INCORRECT

        # Second attempt - partial
        result2 = validator.validate(simple_exercise, "ls -la")
        assert result2.is_partial

        # Third attempt - correct
        result3 = validator.validate(simple_exercise, "ls")
        assert result3.is_correct

    def test_pattern_takes_precedence_over_llm(self, simple_exercise):
        """Test that pattern matching is preferred over LLM."""
        mock_client = Mock()
        validator = ExerciseValidator(llm_client=mock_client)

        # Exact match should not call LLM
        result = validator.validate(simple_exercise, "ls")
        assert result.is_correct
        assert not mock_client.generate.called

    @pytest.mark.integration
    def test_real_llm_validation(self):
        """Integration test with real LLM (requires API key)."""
        pytest.skip("Integration test - requires API key")
