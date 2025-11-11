"""
Tests for Pydantic data models.

Tests the Course, Lesson, Exercise, and Config models to ensure proper
validation, nested relationships, and default values.
"""

import pytest
from pydantic import ValidationError

from skillforge.models import (
    AppConfig,
    Course,
    Difficulty,
    Exercise,
    Lesson,
    LLMConfig,
    LLMProvider,
)


class TestExercise:
    """Test the Exercise model."""

    def test_exercise_creation(self) -> None:
        """Test creating a basic exercise."""
        exercise = Exercise(
            id="ex1", instruction="Print hello world", expected_output="hello world"
        )
        assert exercise.id == "ex1"
        assert exercise.instruction == "Print hello world"
        assert exercise.expected_output == "hello world"
        assert exercise.hints == []

    def test_exercise_with_hints(self) -> None:
        """Test creating an exercise with hints."""
        exercise = Exercise(
            id="ex2",
            instruction="Write a function",
            hints=["Start with def", "Use return statement"],
        )
        assert len(exercise.hints) == 2
        assert exercise.hints[0] == "Start with def"

    def test_exercise_optional_expected_output(self) -> None:
        """Test that expected_output is optional."""
        exercise = Exercise(id="ex3", instruction="Explore the docs")
        assert exercise.expected_output is None

    def test_exercise_missing_required_fields(self) -> None:
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            Exercise()  # type: ignore

    def test_exercise_defaults(self) -> None:
        """Test that default values are applied correctly."""
        exercise = Exercise(id="ex4", instruction="Test defaults")
        assert exercise.hints == []
        assert exercise.expected_output is None


class TestLesson:
    """Test the Lesson model."""

    def test_lesson_creation(self) -> None:
        """Test creating a basic lesson."""
        lesson = Lesson(
            id="lesson1",
            title="Introduction to Python",
            objectives=["Understand variables", "Use print function"],
        )
        assert lesson.id == "lesson1"
        assert lesson.title == "Introduction to Python"
        assert len(lesson.objectives) == 2
        assert lesson.exercises == []

    def test_lesson_with_exercises(self) -> None:
        """Test creating a lesson with exercises."""
        exercise1 = Exercise(id="ex1", instruction="Print your name")
        exercise2 = Exercise(id="ex2", instruction="Create a variable")

        lesson = Lesson(
            id="lesson2",
            title="Python Basics",
            objectives=["Learn printing"],
            exercises=[exercise1, exercise2],
        )
        assert len(lesson.exercises) == 2
        assert lesson.exercises[0].id == "ex1"
        assert lesson.exercises[1].id == "ex2"

    def test_lesson_missing_required_fields(self) -> None:
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            Lesson(id="lesson3", title="Incomplete")  # type: ignore

    def test_lesson_nested_exercise_validation(self) -> None:
        """Test that nested Exercise objects are validated."""
        with pytest.raises(ValidationError):
            Lesson(
                id="lesson4",
                title="Bad Lesson",
                objectives=["Test"],
                exercises=[{"id": "ex1"}],  # type: ignore  # Missing instruction
            )


class TestCourse:
    """Test the Course model."""

    def test_course_creation(self) -> None:
        """Test creating a basic course."""
        course = Course(
            id="course1",
            topic="Python Programming",
            description="Learn Python from scratch",
            difficulty=Difficulty.BEGINNER,
        )
        assert course.id == "course1"
        assert course.topic == "Python Programming"
        assert course.difficulty == Difficulty.BEGINNER
        assert course.lessons == []

    def test_course_with_lessons(self) -> None:
        """Test creating a course with nested lessons and exercises."""
        exercise = Exercise(id="ex1", instruction="Print hello")
        lesson = Lesson(
            id="lesson1",
            title="Basics",
            objectives=["Learn printing"],
            exercises=[exercise],
        )
        course = Course(
            id="course2",
            topic="Python",
            description="Intro course",
            difficulty=Difficulty.BEGINNER,
            lessons=[lesson],
        )
        assert len(course.lessons) == 1
        assert course.lessons[0].id == "lesson1"
        assert len(course.lessons[0].exercises) == 1
        assert course.lessons[0].exercises[0].id == "ex1"

    def test_course_missing_required_fields(self) -> None:
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            Course(id="course3", topic="Incomplete")  # type: ignore

    def test_course_nested_validation(self) -> None:
        """Test that nested Lesson objects are validated."""
        with pytest.raises(ValidationError):
            Course(
                id="course4",
                topic="Bad Course",
                description="Test",
                difficulty=Difficulty.BEGINNER,
                lessons=[{"id": "lesson1"}],  # type: ignore  # Missing title and objectives
            )

    def test_course_invalid_difficulty(self) -> None:
        """Test that invalid difficulty values are rejected."""
        with pytest.raises(ValidationError):
            Course(
                id="course5",
                topic="Test Course",
                description="Test",
                difficulty="expert",  # type: ignore  # Invalid difficulty
            )

    def test_course_difficulty_enum_values(self) -> None:
        """Test all valid difficulty enum values."""
        for difficulty in Difficulty:
            course = Course(
                id=f"course_{difficulty.value}",
                topic="Test",
                description="Test",
                difficulty=difficulty,
            )
            assert course.difficulty == difficulty


class TestLLMConfig:
    """Test the LLMConfig model."""

    def test_llm_config_creation(self) -> None:
        """Test creating LLM configuration."""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4-5-20250929",
            temperature=0.7,
        )
        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model == "claude-sonnet-4-5-20250929"
        assert config.temperature == 0.7

    def test_llm_config_default_temperature(self) -> None:
        """Test that temperature has a default value."""
        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4")
        assert config.temperature == 0.7

    def test_llm_config_temperature_validation(self) -> None:
        """Test that temperature is validated (0.0-1.0)."""
        with pytest.raises(ValidationError):
            LLMConfig(provider=LLMProvider.ANTHROPIC, model="test", temperature=1.5)

        with pytest.raises(ValidationError):
            LLMConfig(provider=LLMProvider.ANTHROPIC, model="test", temperature=-0.1)

    def test_llm_config_missing_required_fields(self) -> None:
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            LLMConfig(provider=LLMProvider.ANTHROPIC)  # type: ignore

    def test_llm_config_invalid_provider(self) -> None:
        """Test that invalid provider values are rejected."""
        with pytest.raises(ValidationError):
            LLMConfig(
                provider="google",  # type: ignore  # Invalid provider
                model="gemini-pro",
            )

    def test_llm_config_provider_enum_values(self) -> None:
        """Test all valid provider enum values."""
        for provider in LLMProvider:
            config = LLMConfig(provider=provider, model="test-model")
            assert config.provider == provider


class TestAppConfig:
    """Test the AppConfig model."""

    def test_app_config_creation(self) -> None:
        """Test creating app configuration."""
        llm_config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-3")
        app_config = AppConfig(llm=llm_config, data_dir="/custom/path")
        assert app_config.llm.provider == LLMProvider.ANTHROPIC
        assert app_config.data_dir == "/custom/path"

    def test_app_config_default_data_dir(self) -> None:
        """Test that data_dir has a default value."""
        llm_config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4")
        app_config = AppConfig(llm=llm_config)
        assert app_config.data_dir == "~/.skillforge"

    def test_app_config_nested_llm_validation(self) -> None:
        """Test that nested LLMConfig is validated."""
        with pytest.raises(ValidationError):
            AppConfig(llm={"provider": "anthropic"})  # type: ignore  # Missing model


class TestEnums:
    """Test enum definitions and behavior."""

    def test_difficulty_enum_values(self) -> None:
        """Test that Difficulty enum has expected values."""
        assert Difficulty.BEGINNER.value == "beginner"
        assert Difficulty.INTERMEDIATE.value == "intermediate"
        assert Difficulty.ADVANCED.value == "advanced"
        assert len(Difficulty) == 3

    def test_difficulty_enum_string_comparison(self) -> None:
        """Test that Difficulty enum values can be compared to strings."""
        assert Difficulty.BEGINNER == "beginner"
        assert Difficulty.INTERMEDIATE == "intermediate"
        assert Difficulty.ADVANCED == "advanced"

    def test_llm_provider_enum_values(self) -> None:
        """Test that LLMProvider enum has expected values."""
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.OPENAI.value == "openai"
        assert len(LLMProvider) == 2

    def test_llm_provider_enum_string_comparison(self) -> None:
        """Test that LLMProvider enum values can be compared to strings."""
        assert LLMProvider.ANTHROPIC == "anthropic"
        assert LLMProvider.OPENAI == "openai"
