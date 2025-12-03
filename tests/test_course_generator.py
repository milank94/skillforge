"""Tests for course generator with caching."""

import os
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from skillforge.core.course_generator import CourseGenerator
from skillforge.models.config import LLMConfig
from skillforge.models.course import Course
from skillforge.models.enums import Difficulty, LLMProvider
from skillforge.utils.llm_client import LLMClientFactory

# Test fixtures


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    return client


@pytest.fixture
def sample_course_json():
    """Sample course JSON response from LLM."""
    return {
        "topic": "Python Basics",
        "description": "Learn fundamental Python programming concepts",
        "difficulty": "beginner",
        "lessons": [
            {
                "title": "Variables and Data Types",
                "objectives": [
                    "Understand basic data types",
                    "Learn variable assignment",
                ],
                "exercises": [
                    {
                        "instruction": "Create a variable named 'name' with your name",
                        "expected_output": None,
                        "hints": ["Use quotes for strings", "Use = for assignment"],
                    },
                    {
                        "instruction": "Print the variable",
                        "expected_output": "Your name",
                        "hints": ["Use print() function"],
                    },
                ],
            },
            {
                "title": "Control Flow",
                "objectives": ["Learn if statements", "Understand loops"],
                "exercises": [
                    {
                        "instruction": "Write an if statement",
                        "expected_output": None,
                        "hints": ["Use if keyword", "Don't forget the colon"],
                    }
                ],
            },
        ],
    }


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporary cache directory for testing."""
    return tmp_path / "cache"


# CourseGenerator initialization tests


def test_course_generator_initialization(mock_llm_client):
    """Test CourseGenerator initializes correctly."""
    generator = CourseGenerator(mock_llm_client)

    assert generator.llm_client == mock_llm_client
    assert generator.cache_ttl_days == 30
    assert generator.cache_dir == Path.home() / ".skillforge" / "cache" / "courses"


def test_course_generator_custom_cache_dir(mock_llm_client, temp_cache_dir):
    """Test CourseGenerator with custom cache directory."""
    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    assert generator.cache_dir == temp_cache_dir


def test_course_generator_custom_ttl(mock_llm_client):
    """Test CourseGenerator with custom cache TTL."""
    generator = CourseGenerator(mock_llm_client, cache_ttl_days=7)

    assert generator.cache_ttl_days == 7


# Course generation tests


def test_generate_course_success(mock_llm_client, sample_course_json, temp_cache_dir):
    """Test successful course generation."""
    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(
        mock_llm_client, cache_dir=temp_cache_dir, cache_ttl_days=30
    )
    course = generator.generate_course("Python Basics", use_cache=False)

    assert isinstance(course, Course)
    assert course.topic == "Python Basics"
    assert course.difficulty == Difficulty.BEGINNER
    assert len(course.lessons) == 2
    assert course.lessons[0].title == "Variables and Data Types"
    assert len(course.lessons[0].exercises) == 2


def test_generate_course_adds_uuids(
    mock_llm_client, sample_course_json, temp_cache_dir
):
    """Test that UUIDs are added to course, lessons, and exercises."""
    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)
    course = generator.generate_course("Python Basics", use_cache=False)

    # Check all IDs are present and are strings
    assert isinstance(course.id, str)
    assert len(course.id) > 0

    for lesson in course.lessons:
        assert isinstance(lesson.id, str)
        assert len(lesson.id) > 0

        for exercise in lesson.exercises:
            assert isinstance(exercise.id, str)
            assert len(exercise.id) > 0


def test_generate_course_with_difficulty(
    mock_llm_client, sample_course_json, temp_cache_dir
):
    """Test course generation with different difficulty levels."""
    sample_course_json["difficulty"] = "advanced"
    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)
    course = generator.generate_course(
        "Advanced Python", difficulty=Difficulty.ADVANCED, use_cache=False
    )

    assert course.difficulty == Difficulty.ADVANCED


def test_generate_course_with_custom_lesson_count(
    mock_llm_client, sample_course_json, temp_cache_dir
):
    """Test course generation with custom lesson count."""
    # Add more lessons to match num_lessons
    for i in range(3, 11):
        sample_course_json["lessons"].append(
            {
                "title": f"Lesson {i}",
                "objectives": ["Objective 1"],
                "exercises": [
                    {
                        "instruction": "Do something",
                        "expected_output": None,
                        "hints": ["Hint 1"],
                    }
                ],
            }
        )

    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)
    course = generator.generate_course("Python", num_lessons=10, use_cache=False)

    assert len(course.lessons) == 10


# Parameter validation tests


def test_generate_course_empty_topic(mock_llm_client, temp_cache_dir):
    """Test that empty topic raises ValueError."""
    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    with pytest.raises(ValueError, match="Topic cannot be empty"):
        generator.generate_course("", use_cache=False)


def test_generate_course_whitespace_topic(mock_llm_client, temp_cache_dir):
    """Test that whitespace-only topic raises ValueError."""
    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    with pytest.raises(ValueError, match="Topic cannot be empty"):
        generator.generate_course("   ", use_cache=False)


def test_generate_course_invalid_lesson_count_low(mock_llm_client, temp_cache_dir):
    """Test that lesson count < 1 raises ValueError."""
    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    with pytest.raises(ValueError, match="must be between 1 and 20"):
        generator.generate_course("Python", num_lessons=0, use_cache=False)


def test_generate_course_invalid_lesson_count_high(mock_llm_client, temp_cache_dir):
    """Test that lesson count > 20 raises ValueError."""
    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    with pytest.raises(ValueError, match="must be between 1 and 20"):
        generator.generate_course("Python", num_lessons=21, use_cache=False)


def test_generate_course_invalid_json(mock_llm_client, temp_cache_dir):
    """Test that invalid course data raises ValueError."""
    # Return invalid data (missing required fields)
    mock_llm_client.generate_json.return_value = {"invalid": "data"}

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    with pytest.raises(ValueError, match="Failed to validate course data"):
        generator.generate_course("Python", use_cache=False)


# Cache key generation tests


def test_cache_key_generation_consistent(mock_llm_client):
    """Test that cache key generation is consistent."""
    generator = CourseGenerator(mock_llm_client)

    key1 = generator._generate_cache_key("Python", Difficulty.BEGINNER, 5)
    key2 = generator._generate_cache_key("Python", Difficulty.BEGINNER, 5)

    assert key1 == key2
    assert len(key1) == 16  # 16 hex characters


def test_cache_key_generation_case_insensitive(mock_llm_client):
    """Test that cache key is case-insensitive for topic."""
    generator = CourseGenerator(mock_llm_client)

    key1 = generator._generate_cache_key("Python", Difficulty.BEGINNER, 5)
    key2 = generator._generate_cache_key("PYTHON", Difficulty.BEGINNER, 5)
    key3 = generator._generate_cache_key("python", Difficulty.BEGINNER, 5)

    assert key1 == key2 == key3


def test_cache_key_generation_different_params(mock_llm_client):
    """Test that different parameters generate different cache keys."""
    generator = CourseGenerator(mock_llm_client)

    key_topic = generator._generate_cache_key("Python", Difficulty.BEGINNER, 5)
    key_difficulty = generator._generate_cache_key("Python", Difficulty.ADVANCED, 5)
    key_lessons = generator._generate_cache_key("Python", Difficulty.BEGINNER, 10)

    assert key_topic != key_difficulty
    assert key_topic != key_lessons
    assert key_difficulty != key_lessons


# Caching tests


def test_generate_course_uses_cache(
    mock_llm_client, sample_course_json, temp_cache_dir
):
    """Test that course generation uses cache on second call."""
    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    # First call - should call LLM
    course1 = generator.generate_course("Python", use_cache=True)
    assert mock_llm_client.generate_json.call_count == 1

    # Second call - should use cache
    course2 = generator.generate_course("Python", use_cache=True)
    assert mock_llm_client.generate_json.call_count == 1  # No additional call

    # Courses should be equivalent
    assert course1.topic == course2.topic
    assert len(course1.lessons) == len(course2.lessons)


def test_generate_course_cache_miss(
    mock_llm_client, sample_course_json, temp_cache_dir
):
    """Test cache miss with different parameters."""
    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    # First call
    generator.generate_course("Python", difficulty=Difficulty.BEGINNER, use_cache=True)
    assert mock_llm_client.generate_json.call_count == 1

    # Second call with different difficulty - cache miss
    generator.generate_course("Python", difficulty=Difficulty.ADVANCED, use_cache=True)
    assert mock_llm_client.generate_json.call_count == 2


def test_generate_course_cache_disabled(
    mock_llm_client, sample_course_json, temp_cache_dir
):
    """Test that caching can be disabled."""
    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    # Both calls should hit LLM
    generator.generate_course("Python", use_cache=False)
    generator.generate_course("Python", use_cache=False)

    assert mock_llm_client.generate_json.call_count == 2


def test_cache_expiration(mock_llm_client, sample_course_json, temp_cache_dir):
    """Test that expired cache entries are not used."""
    mock_llm_client.generate_json.return_value = sample_course_json

    # Use very short TTL (convert to days: 0.1 seconds = 0.1/86400 days)
    generator = CourseGenerator(
        mock_llm_client, cache_dir=temp_cache_dir, cache_ttl_days=0.1 / 86400
    )

    # First call - creates cache
    generator.generate_course("Python", use_cache=True)
    assert mock_llm_client.generate_json.call_count == 1

    # Wait for cache to expire (0.15 seconds > 0.1 seconds)
    time.sleep(0.15)

    # Second call - cache expired, should call LLM again
    generator.generate_course("Python", use_cache=True)
    assert mock_llm_client.generate_json.call_count == 2


def test_corrupted_cache_handled(mock_llm_client, sample_course_json, temp_cache_dir):
    """Test that corrupted cache files are handled gracefully."""
    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    # Create corrupted cache file
    cache_key = generator._generate_cache_key("Python", Difficulty.BEGINNER, 5)
    temp_cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = temp_cache_dir / f"{cache_key}.json"
    cache_file.write_text("invalid json content")

    # Should handle corruption and regenerate
    course = generator.generate_course("Python", use_cache=True)

    assert isinstance(course, Course)
    assert mock_llm_client.generate_json.call_count == 1
    assert not cache_file.exists() or cache_file.read_text() != "invalid json content"


# Cache management tests


def test_clear_cache(mock_llm_client, sample_course_json, temp_cache_dir):
    """Test clearing cache."""
    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    # Generate some cached courses
    generator.generate_course("Python", use_cache=True)
    generator.generate_course("Docker", use_cache=True)

    # Verify cache files exist
    cache_files = list(temp_cache_dir.glob("*.json"))
    assert len(cache_files) == 2

    # Clear cache
    count = generator.clear_cache()

    assert count == 2
    assert len(list(temp_cache_dir.glob("*.json"))) == 0


def test_clear_cache_empty(mock_llm_client, temp_cache_dir):
    """Test clearing empty cache."""
    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    count = generator.clear_cache()

    assert count == 0


def test_get_cache_stats(mock_llm_client, sample_course_json, temp_cache_dir):
    """Test getting cache statistics."""
    mock_llm_client.generate_json.return_value = sample_course_json

    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    # Generate some cached courses
    generator.generate_course("Python", use_cache=True)
    generator.generate_course("Docker", use_cache=True)

    stats = generator.get_cache_stats()

    assert stats["cached_courses"] == 2
    assert stats["total_size_bytes"] > 0
    assert stats["cache_dir"] == str(temp_cache_dir)


def test_get_cache_stats_empty(mock_llm_client, temp_cache_dir):
    """Test cache statistics with empty cache."""
    generator = CourseGenerator(mock_llm_client, cache_dir=temp_cache_dir)

    stats = generator.get_cache_stats()

    assert stats["cached_courses"] == 0
    assert stats["total_size_bytes"] == 0
    assert stats["cache_dir"] == str(temp_cache_dir)


# Prompt generation tests


def test_system_prompt_generation(mock_llm_client):
    """Test system prompt contains key guidelines."""
    generator = CourseGenerator(mock_llm_client)

    prompt = generator._get_course_generation_system_prompt()

    assert "expert programming instructor" in prompt.lower()
    assert "interactive" in prompt.lower()
    assert "hands-on" in prompt.lower()
    assert "json" in prompt.lower()


def test_user_prompt_includes_requirements(mock_llm_client):
    """Test user prompt includes all requirements."""
    generator = CourseGenerator(mock_llm_client)

    prompt = generator._build_course_generation_prompt(
        "Python Basics", Difficulty.ADVANCED, 7
    )

    assert "Python Basics" in prompt
    assert "advanced" in prompt.lower()
    assert "7" in prompt


# Integration tests (marked, optional)


@pytest.mark.integration
def test_generate_course_with_real_anthropic_api():
    """Test course generation with real Anthropic API."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    config = LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-sonnet-4-5-20250929",
        temperature=0.7,
    )
    client = LLMClientFactory.create_client(config)
    generator = CourseGenerator(client)

    course = generator.generate_course(
        "Git Basics", difficulty=Difficulty.BEGINNER, num_lessons=3, use_cache=False
    )

    assert isinstance(course, Course)
    assert course.topic.lower() == "git basics"
    assert course.difficulty == Difficulty.BEGINNER
    assert len(course.lessons) == 3
    assert all(len(lesson.exercises) >= 2 for lesson in course.lessons)


@pytest.mark.integration
def test_generate_course_with_real_openai_api():
    """Test course generation with real OpenAI API."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4", temperature=0.7)
    client = LLMClientFactory.create_client(config)
    generator = CourseGenerator(client)

    course = generator.generate_course(
        "Docker Basics", difficulty=Difficulty.BEGINNER, num_lessons=3, use_cache=False
    )

    assert isinstance(course, Course)
    assert "docker" in course.topic.lower()
    assert course.difficulty == Difficulty.BEGINNER
    assert len(course.lessons) == 3


@pytest.mark.integration
def test_cache_functionality_end_to_end():
    """Test complete cache workflow with real API."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    config = LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-sonnet-4-5-20250929",
        temperature=0.7,
    )
    client = LLMClientFactory.create_client(config)

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cache"
        generator = CourseGenerator(client, cache_dir=cache_dir)

        # First generation - should call API
        course1 = generator.generate_course(
            "Kubernetes Basics", num_lessons=2, use_cache=True
        )

        # Check cache was created
        stats1 = generator.get_cache_stats()
        assert stats1["cached_courses"] == 1

        # Second generation - should use cache (much faster)
        start_time = time.time()
        course2 = generator.generate_course(
            "Kubernetes Basics", num_lessons=2, use_cache=True
        )
        cache_time = time.time() - start_time

        assert cache_time < 0.5  # Should be nearly instant from cache
        assert course1.topic == course2.topic

        # Clear cache
        count = generator.clear_cache()
        assert count == 1

        stats2 = generator.get_cache_stats()
        assert stats2["cached_courses"] == 0
