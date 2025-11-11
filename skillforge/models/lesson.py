"""
Lesson and Exercise data models.

This module defines the structure for lessons and exercises in a course.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Exercise(BaseModel):
    """
    Represents a single exercise within a lesson.

    An exercise is a hands-on task that the user must complete to demonstrate
    understanding of a specific concept.

    Attributes:
        id: Unique identifier for the exercise
        instruction: The task description presented to the user
        expected_output: Optional expected result (for validation)
        hints: List of hints to help the user if they get stuck
    """

    id: str = Field(..., description="Unique identifier for the exercise")
    instruction: str = Field(..., description="The task description for the user")
    expected_output: Optional[str] = Field(
        None, description="Expected result for validation"
    )
    hints: List[str] = Field(default_factory=list, description="Hints to help the user")


class Lesson(BaseModel):
    """
    Represents a single lesson within a course.

    A lesson is a focused learning unit covering a specific topic or concept,
    containing multiple exercises for hands-on practice.

    Attributes:
        id: Unique identifier for the lesson
        title: The lesson title
        objectives: List of learning objectives for this lesson
        exercises: List of exercises in this lesson
    """

    id: str = Field(..., description="Unique identifier for the lesson")
    title: str = Field(..., description="The lesson title")
    objectives: List[str] = Field(
        ..., description="Learning objectives for this lesson"
    )
    exercises: List[Exercise] = Field(
        default_factory=list, description="Exercises in this lesson"
    )
