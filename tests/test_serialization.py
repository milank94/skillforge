"""
Tests for serialization utilities.

This module tests the serialization and deserialization functions
for all Pydantic models.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from skillforge.models import (
    AppConfig,
    Course,
    CourseProgress,
    Difficulty,
    Exercise,
    ExerciseProgress,
    LearningSession,
    Lesson,
    LessonProgress,
    LLMConfig,
    LLMProvider,
    ProgressStatus,
    SessionState,
)
from skillforge.utils.serialization import (
    from_dict,
    from_json,
    load_from_file,
    save_to_file,
    to_dict,
    to_json,
)


@pytest.fixture
def sample_exercise():
    """Create a sample Exercise for testing."""
    return Exercise(
        id="ex1",
        instruction="Print 'Hello, World!' using the print function",
        expected_output="Hello, World!",
        hints=["Use print()", "Don't forget the comma"],
    )


@pytest.fixture
def sample_lesson(sample_exercise):
    """Create a sample Lesson for testing."""
    return Lesson(
        id="lesson1",
        title="Introduction to Python",
        objectives=["Learn basics", "Write first program"],
        exercises=[sample_exercise],
    )


@pytest.fixture
def sample_course(sample_lesson):
    """Create a sample Course for testing."""
    return Course(
        id="course1",
        topic="Python Basics",
        description="Learn Python fundamentals",
        difficulty=Difficulty.BEGINNER,
        lessons=[sample_lesson],
    )


@pytest.fixture
def sample_exercise_progress():
    """Create a sample ExerciseProgress for testing."""
    return ExerciseProgress(
        exercise_id="ex1",
        status=ProgressStatus.IN_PROGRESS,
        attempts=2,
        user_solution="print('Hello, World!')",
    )


@pytest.fixture
def sample_lesson_progress(sample_exercise_progress):
    """Create a sample LessonProgress for testing."""
    return LessonProgress(
        lesson_id="lesson1",
        status=ProgressStatus.IN_PROGRESS,
        exercise_progress=[sample_exercise_progress],
    )


@pytest.fixture
def sample_course_progress(sample_lesson_progress):
    """Create a sample CourseProgress for testing."""
    return CourseProgress(
        course_id="course1",
        user_id="user123",
        current_lesson_index=0,
        lesson_progress=[sample_lesson_progress],
    )


@pytest.fixture
def sample_session(sample_course, sample_course_progress):
    """Create a sample LearningSession for testing."""
    return LearningSession(
        course=sample_course,
        progress=sample_course_progress,
        state=SessionState.ACTIVE,
        current_lesson_id="lesson1",
        current_exercise_id="ex1",
    )


@pytest.fixture
def sample_llm_config():
    """Create a sample LLMConfig for testing."""
    return LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-sonnet-4-5-20250929",
        api_key="sk-test-key",
        temperature=0.7,
        max_tokens=4096,
    )


@pytest.fixture
def sample_app_config(sample_llm_config):
    """Create a sample AppConfig for testing."""
    return AppConfig(
        data_dir="/tmp/skillforge",
        llm=sample_llm_config,
    )


@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file path."""
    return tmp_path / "test.json"


# Test to_dict function


def test_to_dict_exercise(sample_exercise):
    """Test converting Exercise to dict."""
    result = to_dict(sample_exercise)

    assert isinstance(result, dict)
    assert result["id"] == "ex1"
    assert result["instruction"] == "Print 'Hello, World!' using the print function"
    assert result["expected_output"] == "Hello, World!"
    assert result["hints"] == ["Use print()", "Don't forget the comma"]


def test_to_dict_course(sample_course):
    """Test converting Course to dict with nested objects."""
    result = to_dict(sample_course)

    assert isinstance(result, dict)
    assert result["id"] == "course1"
    assert result["topic"] == "Python Basics"
    assert result["difficulty"] == "beginner"
    assert len(result["lessons"]) == 1
    assert result["lessons"][0]["id"] == "lesson1"
    assert len(result["lessons"][0]["exercises"]) == 1


def test_to_dict_exclude_none(sample_exercise_progress):
    """Test to_dict with exclude_none option."""
    # completed_at is None initially
    result = to_dict(sample_exercise_progress, exclude_none=True)

    assert "exercise_id" in result
    assert "status" in result
    assert "completed_at" not in result  # Should be excluded


def test_to_dict_session_with_datetime(sample_session):
    """Test to_dict properly handles datetime fields."""
    result = to_dict(sample_session)

    assert isinstance(result, dict)
    assert "created_at" in result
    assert "last_activity_at" in result
    # Datetime objects should remain as datetime (not converted to string)
    assert isinstance(result["created_at"], datetime)
    assert isinstance(result["last_activity_at"], datetime)


# Test to_json function


def test_to_json_exercise(sample_exercise):
    """Test converting Exercise to JSON string."""
    result = to_json(sample_exercise)

    assert isinstance(result, str)
    # Should be valid JSON
    parsed = json.loads(result)
    assert parsed["id"] == "ex1"
    assert parsed["instruction"] == "Print 'Hello, World!' using the print function"


def test_to_json_with_indent(sample_lesson):
    """Test to_json with pretty-printing."""
    result = to_json(sample_lesson, indent=2)

    assert isinstance(result, str)
    # Should contain newlines for pretty-printing
    assert "\n" in result
    # Should be valid JSON
    parsed = json.loads(result)
    assert parsed["id"] == "lesson1"


def test_to_json_exclude_none(sample_exercise_progress):
    """Test to_json with exclude_none option."""
    result = to_json(sample_exercise_progress, exclude_none=True)

    parsed = json.loads(result)
    assert "exercise_id" in parsed
    assert "completed_at" not in parsed


# Test from_dict function


def test_from_dict_exercise():
    """Test creating Exercise from dict."""
    data = {
        "id": "ex2",
        "instruction": "Create a variable named x and set it to 5",
        "expected_output": "x = 5",
        "hints": ["Use ="],
    }

    exercise = from_dict(Exercise, data)

    assert exercise.id == "ex2"
    assert exercise.instruction == "Create a variable named x and set it to 5"
    assert exercise.expected_output == "x = 5"
    assert exercise.hints == ["Use ="]


def test_from_dict_course():
    """Test creating Course from dict with nested objects."""
    data = {
        "id": "course2",
        "topic": "Docker",
        "description": "Learn Docker containers",
        "difficulty": "intermediate",
        "lessons": [
            {
                "id": "lesson1",
                "title": "Introduction to Containers",
                "objectives": ["Understand containers", "Run first container"],
                "exercises": [],
            }
        ],
    }

    course = from_dict(Course, data)

    assert course.id == "course2"
    assert course.topic == "Docker"
    assert course.difficulty == Difficulty.INTERMEDIATE
    assert len(course.lessons) == 1
    assert course.lessons[0].id == "lesson1"


def test_from_dict_validation_error():
    """Test from_dict raises ValidationError for invalid data."""
    data = {
        "id": "ex3",
        # Missing required fields
    }

    with pytest.raises(ValidationError):
        from_dict(Exercise, data)


def test_from_dict_session_with_datetime():
    """Test from_dict properly deserializes datetime fields."""
    now = datetime.now()
    data = {
        "session_id": "sess1",
        "course": {
            "id": "c1",
            "topic": "Test",
            "description": "Test course",
            "difficulty": "beginner",
            "lessons": [],
        },
        "progress": {
            "course_id": "c1",
            "user_id": "user1",
            "current_lesson_index": 0,
            "lesson_progress": [],
        },
        "state": "active",
        "created_at": now.isoformat(),
        "last_activity_at": now.isoformat(),
    }

    session = from_dict(LearningSession, data)

    assert session.session_id == "sess1"
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.last_activity_at, datetime)


# Test from_json function


def test_from_json_exercise():
    """Test creating Exercise from JSON string."""
    json_str = """
    {
        "id": "ex3",
        "instruction": "Define a function named hello that does nothing",
        "expected_output": "def hello(): pass",
        "hints": ["Use def", "Use pass for empty function"]
    }
    """

    exercise = from_json(Exercise, json_str)

    assert exercise.id == "ex3"
    assert exercise.instruction == "Define a function named hello that does nothing"
    assert exercise.hints == ["Use def", "Use pass for empty function"]


def test_from_json_course():
    """Test creating Course from JSON string with nested objects."""
    json_str = """
    {
        "id": "course3",
        "topic": "Kubernetes",
        "description": "Learn K8s",
        "difficulty": "advanced",
        "lessons": []
    }
    """

    course = from_json(Course, json_str)

    assert course.id == "course3"
    assert course.difficulty == Difficulty.ADVANCED


def test_from_json_invalid_json():
    """Test from_json raises error for invalid JSON."""
    json_str = "{ invalid json"

    with pytest.raises(ValidationError):
        from_json(Exercise, json_str)


def test_from_json_validation_error():
    """Test from_json raises ValidationError for invalid data."""
    json_str = '{"id": "ex4"}'  # Missing required fields

    with pytest.raises(ValidationError):
        from_json(Exercise, json_str)


# Test save_to_file function


def test_save_to_file_exercise(sample_exercise, temp_json_file):
    """Test saving Exercise to file."""
    save_to_file(sample_exercise, temp_json_file)

    assert temp_json_file.exists()

    # Verify file contents
    content = temp_json_file.read_text()
    parsed = json.loads(content)
    assert parsed["id"] == "ex1"
    assert parsed["instruction"] == "Print 'Hello, World!' using the print function"


def test_save_to_file_course(sample_course, temp_json_file):
    """Test saving Course with nested objects to file."""
    save_to_file(sample_course, temp_json_file)

    assert temp_json_file.exists()

    content = temp_json_file.read_text()
    parsed = json.loads(content)
    assert parsed["id"] == "course1"
    assert len(parsed["lessons"]) == 1


def test_save_to_file_creates_parent_dirs(sample_lesson, tmp_path):
    """Test save_to_file creates parent directories."""
    nested_path = tmp_path / "nested" / "dir" / "lesson.json"

    save_to_file(sample_lesson, nested_path)

    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_save_to_file_with_indent(sample_exercise, temp_json_file):
    """Test save_to_file respects indent parameter."""
    save_to_file(sample_exercise, temp_json_file, indent=4)

    content = temp_json_file.read_text()
    # 4-space indent should create more whitespace
    assert "    " in content


def test_save_to_file_session_with_datetime(sample_session, temp_json_file):
    """Test saving session with datetime fields."""
    save_to_file(sample_session, temp_json_file)

    assert temp_json_file.exists()

    content = temp_json_file.read_text()
    parsed = json.loads(content)
    # Datetime should be serialized
    assert "created_at" in parsed
    assert isinstance(parsed["created_at"], str)


# Test load_from_file function


def test_load_from_file_exercise(sample_exercise, temp_json_file):
    """Test loading Exercise from file."""
    # First save
    save_to_file(sample_exercise, temp_json_file)

    # Then load
    loaded = load_from_file(Exercise, temp_json_file)

    assert loaded.id == sample_exercise.id
    assert loaded.instruction == sample_exercise.instruction
    assert loaded.hints == sample_exercise.hints


def test_load_from_file_course(sample_course, temp_json_file):
    """Test loading Course with nested objects from file."""
    save_to_file(sample_course, temp_json_file)

    loaded = load_from_file(Course, temp_json_file)

    assert loaded.id == sample_course.id
    assert loaded.topic == sample_course.topic
    assert loaded.difficulty == sample_course.difficulty
    assert len(loaded.lessons) == len(sample_course.lessons)
    assert loaded.lessons[0].id == sample_course.lessons[0].id


def test_load_from_file_not_found(tmp_path):
    """Test load_from_file raises FileNotFoundError for missing file."""
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_from_file(Exercise, missing_file)


def test_load_from_file_invalid_json(temp_json_file):
    """Test load_from_file raises error for invalid JSON."""
    temp_json_file.write_text("{ invalid json")

    with pytest.raises(ValidationError):
        load_from_file(Exercise, temp_json_file)


def test_load_from_file_validation_error(temp_json_file):
    """Test load_from_file raises ValidationError for invalid data."""
    temp_json_file.write_text('{"id": "ex5"}')  # Missing required fields

    with pytest.raises(ValidationError):
        load_from_file(Exercise, temp_json_file)


def test_load_from_file_session_with_datetime(sample_session, temp_json_file):
    """Test loading session properly deserializes datetime fields."""
    save_to_file(sample_session, temp_json_file)

    loaded = load_from_file(LearningSession, temp_json_file)

    assert isinstance(loaded.created_at, datetime)
    assert isinstance(loaded.last_activity_at, datetime)
    assert loaded.session_id == sample_session.session_id


# Test round-trip serialization


def test_roundtrip_exercise(sample_exercise, temp_json_file):
    """Test save and load round-trip for Exercise."""
    save_to_file(sample_exercise, temp_json_file)
    loaded = load_from_file(Exercise, temp_json_file)

    assert loaded == sample_exercise


def test_roundtrip_lesson(sample_lesson, temp_json_file):
    """Test save and load round-trip for Lesson."""
    save_to_file(sample_lesson, temp_json_file)
    loaded = load_from_file(Lesson, temp_json_file)

    assert loaded == sample_lesson


def test_roundtrip_course(sample_course, temp_json_file):
    """Test save and load round-trip for Course."""
    save_to_file(sample_course, temp_json_file)
    loaded = load_from_file(Course, temp_json_file)

    assert loaded == sample_course


def test_roundtrip_progress(sample_course_progress, temp_json_file):
    """Test save and load round-trip for CourseProgress."""
    save_to_file(sample_course_progress, temp_json_file)
    loaded = load_from_file(CourseProgress, temp_json_file)

    assert loaded.course_id == sample_course_progress.course_id
    assert loaded.current_lesson_index == sample_course_progress.current_lesson_index


def test_roundtrip_session(sample_session, temp_json_file):
    """Test save and load round-trip for LearningSession."""
    save_to_file(sample_session, temp_json_file)
    loaded = load_from_file(LearningSession, temp_json_file)

    assert loaded.session_id == sample_session.session_id
    assert loaded.state == sample_session.state
    # Datetime comparison with small tolerance
    assert abs((loaded.created_at - sample_session.created_at).total_seconds()) < 1


def test_roundtrip_config(sample_app_config, temp_json_file):
    """Test save and load round-trip for AppConfig."""
    save_to_file(sample_app_config, temp_json_file)
    loaded = load_from_file(AppConfig, temp_json_file)

    assert loaded.data_dir == sample_app_config.data_dir
    assert loaded.llm.provider == sample_app_config.llm.provider
    assert loaded.llm.model == sample_app_config.llm.model
