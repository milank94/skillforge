"""
Progress tracking data models.

This module defines models for tracking user progress through courses,
lessons, and exercises.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .enums import ProgressStatus


class ExerciseProgress(BaseModel):
    """
    Tracks progress on a single exercise.

    Attributes:
        exercise_id: Reference to the exercise being tracked
        status: Current completion status
        attempts: Number of times the user attempted this exercise
        user_answer: The user's submitted answer (if any)
        completed_at: Timestamp when the exercise was completed
    """

    exercise_id: str = Field(..., description="Reference to the exercise")
    status: ProgressStatus = Field(
        default=ProgressStatus.NOT_STARTED, description="Current status"
    )
    attempts: int = Field(default=0, description="Number of attempts", ge=0)
    user_answer: Optional[str] = Field(None, description="User's submitted answer")
    completed_at: Optional[datetime] = Field(
        None, description="When the exercise was completed"
    )


class LessonProgress(BaseModel):
    """
    Tracks progress through a lesson.

    Attributes:
        lesson_id: Reference to the lesson being tracked
        status: Current completion status
        exercise_progress: Progress on individual exercises
        started_at: Timestamp when the lesson was started
        completed_at: Timestamp when the lesson was completed
    """

    lesson_id: str = Field(..., description="Reference to the lesson")
    status: ProgressStatus = Field(
        default=ProgressStatus.NOT_STARTED, description="Current status"
    )
    exercise_progress: list[ExerciseProgress] = Field(
        default_factory=list, description="Progress on exercises"
    )
    started_at: Optional[datetime] = Field(
        None, description="When the lesson was started"
    )
    completed_at: Optional[datetime] = Field(
        None, description="When the lesson was completed"
    )


class CourseProgress(BaseModel):
    """
    Tracks progress through an entire course.

    Attributes:
        course_id: Reference to the course being tracked
        user_id: Identifier for the user taking the course
        status: Current completion status
        lesson_progress: Progress on individual lessons
        current_lesson_index: Index of the lesson currently in progress
        started_at: Timestamp when the course was started
        completed_at: Timestamp when the course was completed
    """

    course_id: str = Field(..., description="Reference to the course")
    user_id: str = Field(..., description="User identifier")
    status: ProgressStatus = Field(
        default=ProgressStatus.NOT_STARTED, description="Current status"
    )
    lesson_progress: list[LessonProgress] = Field(
        default_factory=list, description="Progress on lessons"
    )
    current_lesson_index: int = Field(
        default=0, description="Current lesson index", ge=0
    )
    started_at: Optional[datetime] = Field(
        None, description="When the course was started"
    )
    completed_at: Optional[datetime] = Field(
        None, description="When the course was completed"
    )
