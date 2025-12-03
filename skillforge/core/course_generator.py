"""Course generator with LLM-powered curriculum creation and caching.

This module generates structured learning courses from topics using LLM APIs,
with hash-based caching to reduce API costs and improve performance.
"""

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from skillforge.models.course import Course
from skillforge.models.enums import Difficulty
from skillforge.utils.llm_client import BaseLLMClient
from skillforge.utils.serialization import load_from_file, save_to_file


class CourseGenerator:
    """Generates learning courses using LLM with caching support.

    Attributes:
        llm_client: LLM client for generating course content
        cache_dir: Directory for storing cached courses
        cache_ttl_days: Cache time-to-live in days (default: 30)
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        cache_dir: Optional[Path] = None,
        cache_ttl_days: int = 30,
    ):
        """Initialize the course generator.

        Args:
            llm_client: LLM client for generating content
            cache_dir: Optional cache directory (default: ~/.skillforge/cache/courses)
            cache_ttl_days: Cache TTL in days (default: 30)
        """
        self.llm_client = llm_client
        self.cache_ttl_days = cache_ttl_days

        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".skillforge" / "cache" / "courses"

    def generate_course(
        self,
        topic: str,
        difficulty: Difficulty = Difficulty.BEGINNER,
        num_lessons: int = 5,
        use_cache: bool = True,
    ) -> Course:
        """Generate a complete course for the given topic.

        Args:
            topic: The subject to create a course for (e.g., "pytorch basics")
            difficulty: Target difficulty level
            num_lessons: Number of lessons to generate
            use_cache: Whether to use caching (default: True)

        Returns:
            Complete Course object with lessons and exercises

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If course generation fails
        """
        # Validate parameters
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")

        if num_lessons < 1 or num_lessons > 20:
            raise ValueError("Number of lessons must be between 1 and 20")

        # Try cache first if enabled
        if use_cache:
            cache_key = self._generate_cache_key(topic, difficulty, num_lessons)
            cached_course = self._load_from_cache(cache_key)

            if cached_course:
                return cached_course

        # Generate new course
        course_data = self._generate_course_structure(topic, difficulty, num_lessons)

        # Parse into Course model
        course = self._parse_course_data(course_data)

        # Cache the result if enabled
        if use_cache:
            cache_key = self._generate_cache_key(topic, difficulty, num_lessons)
            self._save_to_cache(cache_key, course)

        return course

    def _generate_course_structure(
        self, topic: str, difficulty: Difficulty, num_lessons: int
    ) -> dict[str, Any]:
        """Generate course structure using LLM JSON mode.

        Args:
            topic: The topic for the course
            difficulty: Target difficulty level
            num_lessons: Number of lessons to generate

        Returns:
            Course data as dictionary

        Raises:
            RuntimeError: If LLM generation fails
        """
        system_prompt = self._get_course_generation_system_prompt()
        user_prompt = self._build_course_generation_prompt(
            topic, difficulty, num_lessons
        )

        # Request structured JSON response
        response = self.llm_client.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            schema=self._get_course_schema(),
        )

        return response

    def _parse_course_data(self, data: dict[str, Any]) -> Course:
        """Parse LLM JSON response into Course model.

        Args:
            data: Course data dictionary

        Returns:
            Validated Course object

        Raises:
            ValueError: If course data is invalid
        """
        # Add UUIDs if not present
        if "id" not in data:
            data["id"] = str(uuid.uuid4())

        for lesson in data.get("lessons", []):
            if "id" not in lesson:
                lesson["id"] = str(uuid.uuid4())
            for exercise in lesson.get("exercises", []):
                if "id" not in exercise:
                    exercise["id"] = str(uuid.uuid4())

        # Use Pydantic validation to create Course
        try:
            return Course.model_validate(data)
        except Exception as e:
            raise ValueError(f"Failed to validate course data: {e}") from e

    def _get_course_schema(self) -> dict[str, Any]:
        """Return JSON schema for course generation.

        Returns:
            JSON schema dictionary
        """
        return Course.model_json_schema()

    def _get_course_generation_system_prompt(self) -> str:
        """Get system prompt for course generation.

        Returns:
            System prompt string
        """
        return """You are an expert programming instructor creating interactive
learning courses.

Your task is to create structured, hands-on courses that teach technical
concepts through practical exercises.

Guidelines:
- Focus on interactive, command-line based learning
- Each lesson should build on previous lessons
- Exercises should be practical and testable
- Include clear learning objectives for each lesson
- Provide hints for learners who get stuck
- Keep exercises achievable but challenging
- Use realistic examples and scenarios

Output Format: Return a valid JSON object matching the provided schema."""

    def _build_course_generation_prompt(
        self, topic: str, difficulty: Difficulty, num_lessons: int
    ) -> str:
        """Build user prompt for course generation.

        Args:
            topic: The course topic
            difficulty: Target difficulty level
            num_lessons: Number of lessons to generate

        Returns:
            User prompt string
        """
        return f"""Create an interactive learning course on the topic: "{topic}"

Requirements:
- Difficulty level: {difficulty.value}
- Number of lessons: {num_lessons}
- Each lesson should have 2-4 exercises
- Each exercise should include:
  - Clear instruction
  - Expected output (if applicable)
  - 2-3 helpful hints

Focus on hands-on, command-line based learning where students can practice
actual commands and write real code.

Generate a complete course following the JSON schema provided."""

    def _generate_cache_key(
        self, topic: str, difficulty: Difficulty, num_lessons: int
    ) -> str:
        """Generate unique cache key for course parameters.

        Args:
            topic: The course topic
            difficulty: Target difficulty level
            num_lessons: Number of lessons

        Returns:
            16-character cache key (hex)
        """
        cache_input = {
            "topic": topic.lower().strip(),
            "difficulty": difficulty.value,
            "num_lessons": num_lessons,
        }
        cache_string = json.dumps(cache_input, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()[:16]

    def _load_from_cache(self, cache_key: str) -> Optional[Course]:
        """Load course from cache if exists and not expired.

        Args:
            cache_key: The cache key

        Returns:
            Course object if found and valid, None otherwise
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Check if expired
        mtime = cache_file.stat().st_mtime
        age_days = (time.time() - mtime) / 86400

        if age_days > self.cache_ttl_days:
            # Delete expired cache
            try:
                cache_file.unlink()
            except OSError:
                pass  # Ignore errors on deletion
            return None

        # Load and validate
        try:
            return load_from_file(Course, cache_file)  # type: ignore[return-value]
        except Exception:
            # Corrupted cache, delete and return None
            try:
                cache_file.unlink()
            except OSError:
                pass  # Ignore errors on deletion
            return None

    def _save_to_cache(self, cache_key: str, course: Course) -> None:
        """Save course to cache.

        Args:
            cache_key: The cache key
            course: Course object to cache
        """
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            save_to_file(course, cache_file)
        except Exception:
            # Ignore cache write errors
            pass

    def clear_cache(self) -> int:
        """Clear all cached courses.

        Returns:
            Number of cache files deleted
        """
        if not self.cache_dir.exists():
            return 0

        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass  # Ignore errors on deletion

        return count

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics:
                - cached_courses: Number of cached courses
                - total_size_bytes: Total cache size in bytes
                - cache_dir: Cache directory path
        """
        if not self.cache_dir.exists():
            return {
                "cached_courses": 0,
                "total_size_bytes": 0,
                "cache_dir": str(self.cache_dir),
            }

        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)

        return {
            "cached_courses": len(files),
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }
