"""
Course data model.

This module defines the structure for a complete learning course.
"""

from pydantic import BaseModel, Field

from .enums import Difficulty
from .lesson import Lesson


class Course(BaseModel):
    """
    Represents a complete learning course.

    A course is a structured curriculum on a specific topic, containing
    multiple lessons that guide the user through progressive learning.

    Attributes:
        id: Unique identifier for the course
        topic: The main topic or subject of the course
        description: Detailed description of what the course covers
        difficulty: Difficulty level (Difficulty enum)
        lessons: List of lessons in this course
    """

    id: str = Field(..., description="Unique identifier for the course")
    topic: str = Field(..., description="The main topic of the course")
    description: str = Field(..., description="What the course covers")
    difficulty: Difficulty = Field(..., description="Difficulty level")
    lessons: list[Lesson] = Field(
        default_factory=list, description="Lessons in this course"
    )

    def get_lesson_by_id(self, lesson_id: str) -> Lesson | None:
        """
        Get a lesson by its ID.

        Args:
            lesson_id: The ID of the lesson to find

        Returns:
            The Lesson object if found, None otherwise
        """
        for lesson in self.lessons:
            if lesson.id == lesson_id:
                return lesson
        return None

    def get_lesson_by_index(self, index: int) -> Lesson | None:
        """
        Get a lesson by its index in the course.

        Args:
            index: The zero-based index of the lesson

        Returns:
            The Lesson object if index is valid, None otherwise
        """
        if 0 <= index < len(self.lessons):
            return self.lessons[index]
        return None

    def total_lessons(self) -> int:
        """
        Get the total number of lessons in the course.

        Returns:
            The number of lessons
        """
        return len(self.lessons)

    def total_exercises(self) -> int:
        """
        Get the total number of exercises across all lessons.

        Returns:
            The total count of exercises
        """
        return sum(len(lesson.exercises) for lesson in self.lessons)
