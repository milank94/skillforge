"""
Course data model.

This module defines the structure for a complete learning course.
"""

from typing import List

from pydantic import BaseModel, Field

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
        difficulty: Difficulty level (e.g., "beginner", "intermediate", "advanced")
        lessons: List of lessons in this course
    """

    id: str = Field(..., description="Unique identifier for the course")
    topic: str = Field(..., description="The main topic of the course")
    description: str = Field(..., description="What the course covers")
    difficulty: str = Field(
        ..., description="Difficulty level (beginner/intermediate/advanced)"
    )
    lessons: List[Lesson] = Field(
        default_factory=list, description="Lessons in this course"
    )
