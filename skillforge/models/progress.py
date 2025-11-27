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

    def get_exercise_progress(self, exercise_id: str) -> Optional[ExerciseProgress]:
        """
        Get progress for a specific exercise.

        Args:
            exercise_id: The ID of the exercise

        Returns:
            The ExerciseProgress object if found, None otherwise
        """
        for progress in self.exercise_progress:
            if progress.exercise_id == exercise_id:
                return progress
        return None

    def calculate_completion_percentage(self) -> float:
        """
        Calculate the completion percentage for this lesson.

        Returns:
            Percentage of completed exercises (0.0 to 100.0)
        """
        if not self.exercise_progress:
            return 0.0
        completed = sum(
            1 for ex in self.exercise_progress if ex.status == ProgressStatus.COMPLETED
        )
        return (completed / len(self.exercise_progress)) * 100.0

    def is_completed(self) -> bool:
        """
        Check if all exercises in the lesson are completed.

        Returns:
            True if all exercises are completed, False otherwise
        """
        if not self.exercise_progress:
            return False
        return all(
            ex.status == ProgressStatus.COMPLETED for ex in self.exercise_progress
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

    def get_lesson_progress(self, lesson_id: str) -> Optional[LessonProgress]:
        """
        Get progress for a specific lesson.

        Args:
            lesson_id: The ID of the lesson

        Returns:
            The LessonProgress object if found, None otherwise
        """
        for progress in self.lesson_progress:
            if progress.lesson_id == lesson_id:
                return progress
        return None

    def get_current_lesson_progress(self) -> Optional[LessonProgress]:
        """
        Get the progress for the current lesson.

        Returns:
            The LessonProgress for the current lesson if valid index, None otherwise
        """
        if 0 <= self.current_lesson_index < len(self.lesson_progress):
            return self.lesson_progress[self.current_lesson_index]
        return None

    def calculate_completion_percentage(self) -> float:
        """
        Calculate the overall completion percentage for this course.

        Returns:
            Percentage of completed lessons (0.0 to 100.0)
        """
        if not self.lesson_progress:
            return 0.0
        completed = sum(
            1
            for lesson in self.lesson_progress
            if lesson.status == ProgressStatus.COMPLETED
        )
        return (completed / len(self.lesson_progress)) * 100.0

    def is_completed(self) -> bool:
        """
        Check if all lessons in the course are completed.

        Returns:
            True if all lessons are completed, False otherwise
        """
        if not self.lesson_progress:
            return False
        return all(
            lesson.status == ProgressStatus.COMPLETED for lesson in self.lesson_progress
        )

    def mark_lesson_complete(self, lesson_id: str) -> bool:
        """
        Mark a specific lesson as completed.

        Args:
            lesson_id: The ID of the lesson to mark complete

        Returns:
            True if lesson was found and marked, False otherwise
        """
        progress = self.get_lesson_progress(lesson_id)
        if progress:
            progress.status = ProgressStatus.COMPLETED
            progress.completed_at = datetime.now()
            return True
        return False
